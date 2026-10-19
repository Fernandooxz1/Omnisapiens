"""Las sesiones en vivo: estado, entrega, reloj y vencimientos.

Hay dos formas en el mismo store:

- **Solo** (`SessionStore`): una conexión, el `SoloEngine`, un `outbox` y una
  tarea que vence la ronda servida. No hay lobby, gracia ni lock por silla.
- **Versus** (`VersusSessionStore`): una sala con dos sillas, el `VersusEngine`,
  un `outbox` por jugador, lock por código de sala, ventana de gracia de 20 s y
  pausa/reanudación del reloj cuando alguien se cae.

`SessionStore` y `VersusSessionStore` son los contratos, no las implementaciones.
Los handlers dependerán de las interfaces y este archivo podrá mudarse a Redis el
día que haya más de un proceso. En solo, si el socket se cae, `close` la saca de
memoria y la fila queda `playing` para que el barrendero la invalide. En versus
la silla sobrevive a la desconexión durante la gracia; vencida, la partida
termina en abandono (o `void` si no queda nadie).

El reloj y el `sleep` se inyectan para que una sesión entera, con vencimientos,
corra en microsegundos en los tests. El contenido no vive acá: el borde inyecta
un `ItemSource` que decide y carga el ítem siguiente; el store solo lo sirve.
"""

import asyncio
import logging
import time
import uuid
from collections.abc import Awaitable, Callable, Coroutine, Mapping
from dataclasses import dataclass, field
from random import Random
from typing import Protocol

from app.config import settings
from app.game import protocols, versus_engine
from app.game.answers import Answer, ServedQuestion
from app.game.constants import CHOICES
from app.game.errors import InvalidTransition
from app.game.solo_engine import RoundRecord, SoloEngine, SoloRules, SoloRun
from app.game.versus_engine import VersusConfig, VersusState
from app.services.question_bank import LoadedQuestion, shuffle_options

logger = logging.getLogger(__name__)


class Outbox(Protocol):
    """La cola de salida de una sesión. El store solo escribe.

    El borde puede envolverla para adjuntar el `id` de correlación de un `pong`
    o de un `error`; por eso el contrato es lo mínimo que hace `_push`, no una
    `asyncio.Queue` concreta.
    """

    def put_nowait(self, message: protocols.Message) -> None: ...

    def get_nowait(self) -> object: ...


Clock = Callable[[], int]
Sleeper = Callable[[float], Coroutine[object, object, None]]
Effects = tuple[protocols.Message, ...]

# Tope por conexión: un cliente que deja de leer no puede hacer crecer la cola
# sin fin (H-13). Si se llena se descarta lo más viejo; la conexión la corta el
# timeout de inactividad. Es el mismo criterio que `room_manager.OUTBOX_MAX`.
OUTBOX_MAX = 64

# El reloj de una sesión versus no puede morir con el primer error transitorio
# del borde (elegir la pregunta es I/O): reintenta con backoff. Si el borde está
# caído de verdad, se rinde y avisa: una partida sin reloj tiene que cortar, no
# quedarse muda.
MAX_VERSUS_EXPIRY_FAILURES = 5
VERSUS_EXPIRY_BACKOFF_S = 1.0


@dataclass(frozen=True)
class NextQuestion:
    """Lo que el borde ya eligió y cargó, listo para servir.

    `repeated` es la excepción de §9.4: el pool se quedó sin ítems nuevos y se
    repite uno para no cortar la sesión. Sin ese permiso explícito, repetir es un
    error de programación y el motor lo rechaza.
    """

    question: LoadedQuestion
    repeated: bool = False


# El borde aporta la pregunta ya elegida: candidatas, dificultad, Redis y carga
# son I/O. El store solo aplica las reglas y entrega.
ItemSource = Callable[[SoloRun, frozenset[str]], Awaitable[NextQuestion | None]]

# En versus el pool depende de la partida (tramo de dificultad y preguntas ya
# vistas), así que el borde recibe el estado completo y devuelve la pregunta.
VersusItemSource = Callable[[VersusState], Awaitable[LoadedQuestion | None]]


@dataclass(frozen=True)
class RoundInFlight:
    """La ronda servida y aún sin resolver."""

    served: ServedQuestion
    question: LoadedQuestion


@dataclass(frozen=True)
class SoloState:
    """El estado puro de una sesión solo, sin lock ni tarea.

    `seen` es del borde y no del motor: el motor no guarda historial. Vive acá
    para que el store pueda pasárselo al `ItemSource` y no servir dos veces el
    mismo ítem en una sesión larga.
    """

    session_id: str
    run: SoloRun
    round: RoundInFlight | None = None
    seen: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("session_id vacío")
        if self.run.finished and self.round is not None:
            raise ValueError("una sesión terminada no tiene ronda en vuelo")
        if self.round is not None:
            if self.round.served.round_index != self.run.round_index:
                raise ValueError("la ronda en vuelo no es la del motor")
            if self.round.served.question_id not in self.seen:
                raise ValueError("la ronda en vuelo no está en las vistas")

    @property
    def finished(self) -> bool:
        return self.run.finished

    @property
    def needs_next_question(self) -> bool:
        """El caller tiene que elegir y cargar el próximo ítem."""
        return not self.finished and self.round is None


# El cierre es I/O y lo hace el borde: persiste, calcula el ranking y devuelve
# el `arcade_end` ya completo. El store espera a que termine antes de entregarlo,
# para que el cliente nunca vea posiciones nulas si la base contestó.
FinishHandler = Callable[
    [SoloState, tuple[RoundRecord, ...], protocols.ArcadeEnd],
    Awaitable[protocols.ArcadeEnd],
]


@dataclass(frozen=True)
class Transition:
    state: SoloState
    effects: Effects = ()
    record: RoundRecord | None = None


@dataclass(frozen=True)
class SoloSessionView:
    """Una foto de la sesión viva para tests y diagnóstico.

    No expone el `outbox` ni la tarea: quien consulta no puede escribirle a una
    conexión que no es suya.
    """

    session_id: str
    owner_id: uuid.UUID
    state: SoloState
    records: tuple[RoundRecord, ...] = ()


@dataclass(frozen=True)
class VersusSessionView:
    """Una foto de una sala versus viva para tests y diagnóstico."""

    code: str
    room_id: str
    state: VersusState


class SessionStore(Protocol):
    """Lo que el borde necesita de una sesión solo (fase 4.1).

    El handler del WebSocket depende de la interfaz, no de la clase. El versus
    tiene su propio contrato (`VersusSessionStore`) sobre la misma implementación.
    """

    async def open(
        self,
        *,
        session_id: str,
        owner_id: uuid.UUID,
        outbox: Outbox,
        rules: SoloRules,
        next_item: ItemSource,
        on_finish: FinishHandler | None = None,
    ) -> bool:
        """Registra la sesión, manda el arranque y sirve el primer ítem.

        Devuelve `False` si esa sesión ya estaba abierta. Así el borde distingue
        un `start` repetido sin inventar un estado nuevo.

        `on_finish` es el cierre del borde (persistir y rankear); si no llega,
        el `arcade_end` sale con las posiciones nulas.
        """
        ...

    async def submit(self, *, session_id: str, round_index: int, choice: int) -> None:
        """Resuelve la ronda servida y, si sigue, sirve la siguiente."""
        ...

    async def close(self, *, session_id: str | None = None) -> None:
        """Suelta una sesión (o todas, sin id) y corta su tarea de vencimiento.

        Idempotente. La fila no se toca: el barrendero la invalida si quedó
        `playing`.
        """
        ...

    def live(self) -> frozenset[uuid.UUID]:
        """Las sesiones con socket abierto, para que el barrido no las invalide."""
        ...

    def sessions(self) -> Mapping[str, SoloSessionView]:
        """Las sesiones que este proceso tiene en memoria, en una foto."""
        ...


class VersusSessionStore(Protocol):
    """Lo que el borde necesita de una sala versus (fase 5.1)."""

    async def open_versus(
        self,
        *,
        code: str,
        room_id: str,
        config: VersusConfig,
        host_id: str,
        next_item: VersusItemSource,
    ) -> None:
        """Da de alta la sala viva. Idempotente: reconectar no la reinicia."""
        ...

    async def join(self, *, code: str, user_id: str, nick: str, outbox: Outbox) -> None:
        """Sienta a un jugador (o lo reconecta) y le manda el estado."""
        ...

    async def reconnect(
        self, *, code: str, user_id: str, nick: str, outbox: Outbox
    ) -> None:
        """Vuelve a enganchar una silla existente a una conexión nueva."""
        ...

    async def sync(self, *, code: str, user_id: str) -> None:
        """Reenvía el estado completo al que manda `hello`."""
        ...

    async def start(
        self, *, code: str, user_id: str, match_id: str | None = None
    ) -> str | None:
        """El host arranca la partida y sirve la primera ronda."""
        ...

    async def answer(
        self, *, code: str, user_id: str, round_index: int, choice: int
    ) -> None: ...

    async def disconnect(self, *, code: str, user_id: str, outbox: Outbox) -> None:
        """Suelta la silla si la conexión que se va sigue siendo la vigente."""
        ...

    async def rematch(
        self, *, code: str, user_id: str, match_id: str | None = None
    ) -> str | None: ...

    async def close(
        self, *, session_id: str | None = None, code: str | None = None
    ) -> None:
        """Suelta una sesión solo, una sala versus o todo, y corta sus tareas."""
        ...

    def player_count(self, code: str) -> int:
        """Cuántos jugadores conectados hay en la sala."""
        ...

    def seated(self, *, code: str, user_id: str) -> bool:
        """Si ese usuario tiene silla."""
        ...

    def room_count(self) -> int:
        """Salas versus vivas en memoria."""
        ...

    def live(self) -> frozenset[uuid.UUID]:
        """Las partidas versus en curso, para que el barrido no las invalide."""
        ...

    def versus_sessions(self) -> Mapping[str, VersusSessionView]:
        """Las salas versus que este proceso tiene en memoria, en una foto."""
        ...


@dataclass
class _Session:
    """La sesión viva: el estado puro más lo que el estado puro no puede tener."""

    session_id: str
    owner_id: uuid.UUID
    session_uuid: uuid.UUID
    next_item: ItemSource
    state: SoloState
    outbox: Outbox
    on_finish: FinishHandler | None = None
    # El motor no guarda historial: se acumula acá hasta que el borde persista.
    records: list[RoundRecord] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    # Despierta al reloj cuando cambió la ronda: contestar o servir la siguiente
    # evita el polling y hace que el plazo se recalcule con el estado quieto.
    wakeup: asyncio.Event = field(default_factory=asyncio.Event)
    task: asyncio.Task[None] | None = None


@dataclass
class _Versus:
    """La sala versus viva: el estado puro más la entrega y el reloj."""

    code: str
    room_id: str
    state: VersusState
    next_item: VersusItemSource
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    outboxes: dict[str, Outbox] = field(default_factory=dict)
    # Despierta a la tarea de vencimientos cuando cambió el estado: así no hay
    # polling y el plazo se recalcula con la sala ya quieta.
    wakeup: asyncio.Event = field(default_factory=asyncio.Event)
    # La sala quedó debiendo la ronda siguiente (su consulta falló): el reloj la
    # reintenta. No se usa `needs_next_round` a secas porque el caso `NO_QUESTIONS`
    # también lo deja en `True` y ahí hay que esperar, no girar en vacío.
    retry_serve: bool = False
    # Última vez que pasó algo (alta, join, transición). El alta de una sala nueva
    # usa este dato para desalojar las que murieron sin que nadie las cierre (H-03).
    last_activity_ms: int = 0
    task: asyncio.Task[None] | None = None


class InMemorySessionStore:
    """La implementación de un solo proceso: todas las sesiones en memoria."""

    def __init__(
        self,
        *,
        reveal_seconds: float | None = None,
        grace_seconds: int = settings.reconnect_grace_seconds,
        now_ms: Clock | None = None,
        sleep: Sleeper | None = None,
        rng: Random | None = None,
        max_failures: int = MAX_VERSUS_EXPIRY_FAILURES,
        backoff_s: float = VERSUS_EXPIRY_BACKOFF_S,
        idle_timeout_seconds: int = settings.room_idle_timeout_seconds,
        shuffle_served_options: bool = True,
    ) -> None:
        # `None` lee `settings.reveal_seconds` al dormir: el test puede bajarla o
        # subirla después de construir el store, igual que el handler viejo.
        self._reveal_seconds = reveal_seconds
        self._grace_seconds = grace_seconds
        self._now_ms = now_ms or _system_now_ms
        self._sleep = sleep or asyncio.sleep
        self._rng = rng or Random()
        self._max_failures = max_failures
        self._backoff_s = backoff_s
        self._idle_timeout_ms = idle_timeout_seconds * 1000
        self._shuffle = shuffle_served_options
        self._sessions: dict[str, _Session] = {}
        self._versus: dict[str, _Versus] = {}

    @property
    def _reveal(self) -> float:
        if self._reveal_seconds is None:
            return settings.reveal_seconds
        return self._reveal_seconds

    async def open(
        self,
        *,
        session_id: str,
        owner_id: uuid.UUID,
        outbox: Outbox,
        rules: SoloRules,
        next_item: ItemSource,
        on_finish: FinishHandler | None = None,
    ) -> bool:
        if session_id in self._sessions:
            return False

        session_uuid = uuid.UUID(session_id)
        transition = _start(session_id, rules)
        entry = _Session(
            session_id=session_id,
            owner_id=owner_id,
            session_uuid=session_uuid,
            next_item=next_item,
            state=transition.state,
            outbox=outbox,
            on_finish=on_finish,
        )
        # Se registra antes de entregar: si el primer ítem tarda, el barrido ya
        # sabe que la sesión está viva.
        self._sessions[session_id] = entry
        self._deliver(entry, transition.effects)
        try:
            await self._serve_next(entry)
            entry.task = asyncio.create_task(self._expiry_loop(entry))
        except Exception:
            # Sin primer ítem no hay sesión que relojear: se saca para no dejar
            # una entrada muda en `live.sessions`.
            self._sessions.pop(session_id, None)
            raise
        return True

    async def submit(self, *, session_id: str, round_index: int, choice: int) -> None:
        entry = self._sessions.get(session_id)
        if entry is None:
            return
        async with entry.lock:
            # El `close` pudo sacarla mientras se esperaba el lock.
            if self._sessions.get(session_id) is not entry:
                return
            if entry.state.finished:
                self._error(entry, "NOT_PLAYING", "No hay una ronda para contestar")
                return
            transition = _answer(
                entry.state,
                round_index=round_index,
                choice=choice,
                now_ms=self._now_ms(),
            )
            await self._apply(entry, transition)
            await self._advance(entry, transition)
            entry.wakeup.set()

    async def close(
        self, *, session_id: str | None = None, code: str | None = None
    ) -> None:
        """Suelta una sesión solo, una sala versus o todo; corta sus tareas."""
        solo: list[_Session] = []
        versus: list[_Versus] = []
        if session_id is not None:
            entry = self._sessions.pop(session_id, None)
            if entry is not None:
                solo.append(entry)
        elif code is not None:
            room = self._versus.pop(code, None)
            if room is not None:
                versus.append(room)
        else:
            solo = list(self._sessions.values())
            versus = list(self._versus.values())
            self._sessions.clear()
            self._versus.clear()

        tasks = [entry.task for entry in solo if entry.task is not None]
        tasks.extend(room.task for room in versus if room.task is not None)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    def live(self) -> frozenset[uuid.UUID]:
        sessions = {
            entry.session_uuid
            for entry in self._sessions.values()
            if not entry.state.finished
        }
        # Una partida versus vive en `game_sessions` con el id del match desde la
        # fase 5.2; mientras se juega, el barrido no puede invalidarla.
        matches = {
            uuid.UUID(room.state.match_id)
            for room in self._versus.values()
            if room.state.match_id is not None
            and room.state.match is not None
            and room.state.match.status is versus_engine.MatchStatus.PLAYING
        }
        return frozenset(sessions | matches)

    def sessions(self) -> Mapping[str, SoloSessionView]:
        return {
            session_id: SoloSessionView(
                session_id=entry.session_id,
                owner_id=entry.owner_id,
                state=entry.state,
                records=tuple(entry.records),
            )
            for session_id, entry in self._sessions.items()
        }

    async def open_versus(
        self,
        *,
        code: str,
        room_id: str,
        config: VersusConfig,
        host_id: str,
        next_item: VersusItemSource,
    ) -> None:
        """Da de alta la sala viva. Idempotente: reconectar no la reinicia."""
        actual = self._versus.get(code)
        if actual is not None and not self._versus_evictable(actual):
            # El handler nuevo puede traer otro `ItemSource` (otra sesión de
            # base): la sala sigue, pero la próxima pregunta la carga este.
            actual.next_item = next_item
            return
        if actual is not None:
            self._versus.pop(code, None)
            _cancel(actual)
        self._evict_versus_dead()
        entry = _Versus(
            code=code,
            room_id=room_id,
            state=VersusState(code=code, config=config, host_id=host_id),
            next_item=next_item,
            last_activity_ms=self._now_ms(),
        )
        self._versus[code] = entry
        entry.task = asyncio.create_task(self._versus_expiry_loop(entry))

    async def join(self, *, code: str, user_id: str, nick: str, outbox: Outbox) -> None:
        entry = self._versus.get(code)
        if entry is None:
            return
        async with entry.lock:
            await self._versus_join(entry, user_id=user_id, nick=nick, outbox=outbox)

    async def reconnect(
        self, *, code: str, user_id: str, nick: str, outbox: Outbox
    ) -> None:
        entry = self._versus.get(code)
        if entry is None:
            _push(
                outbox,
                protocols.Error(code="NOT_IN_ROOM", message="No estás en esta sala"),
            )
            return
        async with entry.lock:
            if entry.state.player_of(user_id) is None:
                # Una conexión nueva no puede inventar una silla: sin asiento no
                # hay ronda que repintar ni reloj que reanudar.
                _push(
                    outbox,
                    protocols.Error(
                        code="NOT_IN_ROOM", message="No estás en esta sala"
                    ),
                )
                return
            await self._versus_join(entry, user_id=user_id, nick=nick, outbox=outbox)

    async def sync(self, *, code: str, user_id: str) -> None:
        await self._versus_act(
            code,
            lambda state: versus_engine.sync(
                state, user_id=user_id, now_ms=self._now_ms()
            ),
        )

    async def start(
        self, *, code: str, user_id: str, match_id: str | None = None
    ) -> str | None:
        entry = self._versus.get(code)
        if entry is None:
            return None
        # El id se acuña acá y viaja al mensaje: quien persiste la sesión lo usa.
        nuevo = match_id or str(uuid.uuid4())
        async with entry.lock:
            anterior = entry.state.match_id
            await self._versus_step(
                entry,
                lambda state: versus_engine.start(
                    state, user_id=user_id, match_id=nuevo
                ),
            )
            return nuevo if entry.state.match_id not in (None, anterior) else None

    async def answer(
        self, *, code: str, user_id: str, round_index: int, choice: int
    ) -> None:
        await self._versus_act(
            code,
            lambda state: versus_engine.answer(
                state,
                user_id=user_id,
                round_index=round_index,
                choice=choice,
                now_ms=self._now_ms(),
            ),
        )

    async def disconnect(self, *, code: str, user_id: str, outbox: Outbox) -> None:
        entry = self._versus.get(code)
        if entry is None:
            return
        async with entry.lock:
            # Si otra conexión más nueva ya se sentó, este cierre es de un socket
            # viejo: la silla no es suya y no puede desmontarla.
            if entry.outboxes.get(user_id) is not outbox:
                return
            # Se suelta el `outbox` antes de la transición: mensajes para un
            # socket que ya se fue no le sirven a nadie y se acumularían.
            entry.outboxes.pop(user_id, None)
            await self._versus_step(
                entry,
                lambda state: versus_engine.disconnect(
                    state,
                    user_id=user_id,
                    now_ms=self._now_ms(),
                    grace_seconds=self._grace_seconds,
                ),
            )

    async def rematch(
        self, *, code: str, user_id: str, match_id: str | None = None
    ) -> str | None:
        entry = self._versus.get(code)
        if entry is None:
            return None
        nuevo = match_id or str(uuid.uuid4())
        async with entry.lock:
            anterior = entry.state.match_id
            await self._versus_step(
                entry,
                lambda state: versus_engine.rematch(
                    state, user_id=user_id, match_id=nuevo
                ),
            )
            return nuevo if entry.state.match_id not in (None, anterior) else None

    def player_count(self, code: str) -> int:
        entry = self._versus.get(code)
        if entry is None:
            return 0
        return sum(
            1 for seat in entry.state.seats if seat is not None and seat.connected
        )

    def seated(self, *, code: str, user_id: str) -> bool:
        entry = self._versus.get(code)
        return entry is not None and entry.state.player_of(user_id) is not None

    def room_count(self) -> int:
        """Salas versus vivas en memoria: la métrica que vigila el desalojo."""
        return len(self._versus)

    def versus_sessions(self) -> Mapping[str, VersusSessionView]:
        return {
            code: VersusSessionView(
                code=entry.code, room_id=entry.room_id, state=entry.state
            )
            for code, entry in self._versus.items()
        }

    async def _versus_join(
        self, entry: _Versus, *, user_id: str, nick: str, outbox: Outbox
    ) -> None:
        entry.outboxes[user_id] = outbox
        await self._versus_step(
            entry,
            lambda state: versus_engine.join(
                state, user_id=user_id, nick=nick, now_ms=self._now_ms()
            ),
        )
        if entry.state.player_of(user_id) is None:
            # Un tercero: ya recibió su error y no queda colgado en la sala.
            entry.outboxes.pop(user_id, None)

    async def _versus_act(
        self,
        code: str,
        transition: Callable[[VersusState], versus_engine.Transition],
    ) -> None:
        entry = self._versus.get(code)
        if entry is None:
            return
        async with entry.lock:
            await self._versus_step(entry, transition)

    async def _versus_step(
        self,
        entry: _Versus,
        transition: Callable[[VersusState], versus_engine.Transition],
    ) -> None:
        """Aplica una transición con el lock tomado y hace sonar lo que cuelga."""
        before = entry.state
        entry.last_activity_ms = self._now_ms()
        after, effects = transition(before)
        entry.state = after
        await self._deliver_versus(entry, effects)
        try:
            # La revelación se ve antes de que corra el reloj de la próxima ronda:
            # el `ends_at` se calcula después de la pausa, no antes. Al terminar la
            # partida (`needs_next_round` falso) no hay pausa extra.
            if (
                before.round is not None
                and after.round is None
                and after.needs_next_round
            ):
                await self._sleep(self._reveal)
            await self._serve_versus_next(entry)
            entry.retry_serve = False
        except Exception:
            # Si quedó debiendo la ronda siguiente, el reloj la reintenta: el estado
            # ya es consistente (la ronda anterior está resuelta y entregada).
            entry.retry_serve = after.needs_next_round
            raise
        finally:
            # Cambió el estado (o falló a mitad): el reloj tiene que recalcular.
            entry.wakeup.set()

    async def _serve_versus_next(self, entry: _Versus) -> None:
        """Sirve la ronda siguiente si el motor ya la pidió."""
        if not entry.state.needs_next_round:
            return
        question = await entry.next_item(entry.state)
        if question is None:
            # Sin banco no hay partida que seguir. La sala queda como está y la
            # sesión `playing` la invalida el barrendero.
            await self._deliver_versus(
                entry,
                _versus_error_to_seats(
                    entry.state, "NO_QUESTIONS", "No hay preguntas para servir."
                ),
            )
            return
        if self._shuffle:
            question = shuffle_options(question, self._rng)
        after, effects = versus_engine.serve(
            entry.state, question=question, now_ms=self._now_ms()
        )
        entry.state = after
        await self._deliver_versus(entry, effects)

    async def _versus_expiry_loop(self, entry: _Versus) -> None:
        """Vence lo que el reloj tenga que vencer, sin polling."""
        fallos = 0
        while True:
            try:
                await self._versus_tick(entry)
            except asyncio.CancelledError:
                raise
            except Exception:
                fallos += 1
                logger.exception(
                    "la sala %s falló al vencer (intento %d)",
                    entry.state.code,
                    fallos,
                )
                if fallos >= self._max_failures:
                    await self._versus_surrender(entry)
                    return
                await self._sleep(self._backoff_s)
            else:
                fallos = 0

    async def _versus_tick(self, entry: _Versus) -> None:
        entry.wakeup.clear()
        if entry.retry_serve:
            # Una transición anterior quedó debiendo la ronda siguiente: se
            # reintenta el servir antes de volver a esperar.
            async with entry.lock:
                if self._versus.get(entry.code) is not entry:
                    return
                await self._serve_versus_next(entry)
                entry.retry_serve = False
            return
        deadline = _versus_deadline(entry.state)
        if deadline is None:
            await entry.wakeup.wait()
            return
        if not await self._wait(entry, (deadline - self._now_ms()) / 1000):
            return
        async with entry.lock:
            # Bajo el lock el estado puede haberse movido: otra acción pudo
            # resolver la ronda, reconectar o servirse una nueva.
            if self._versus.get(entry.code) is not entry:
                return
            if _versus_deadline(entry.state) != deadline:
                return
            if self._now_ms() < deadline:
                return
            await self._versus_step(
                entry,
                lambda state: versus_engine.expire(state, now_ms=self._now_ms()),
            )

    async def _versus_surrender(self, entry: _Versus) -> None:
        """La sala perdió el reloj: se avisa a los sentados antes de rendirse."""
        async with entry.lock:
            await self._deliver_versus(
                entry,
                _versus_error_to_seats(
                    entry.state,
                    "ROOM_CLOCK_DOWN",
                    "La sala perdió el reloj. Se corta la partida.",
                ),
            )

    async def _deliver_versus(
        self, entry: _Versus, effects: versus_engine.Effects
    ) -> None:
        for user_id, messages in effects.items():
            outbox = entry.outboxes.get(user_id)
            if outbox is None:
                continue
            for message in messages:
                _push(outbox, message)

    def _evict_versus_dead(self) -> None:
        """Saca del mapa las salas que ya no pueden revivir (H-03)."""
        for code, entry in list(self._versus.items()):
            if self._versus_evictable(entry):
                self._versus.pop(code, None)
                _cancel(entry)

    def _versus_evictable(self, entry: _Versus) -> bool:
        return (
            not entry.outboxes
            and entry.state.status is not versus_engine.VersusStatus.PLAYING
            and self._now_ms() - entry.last_activity_ms >= self._idle_timeout_ms
        )

    async def _apply(self, entry: _Session, transition: Transition) -> None:
        entry.state = transition.state
        if transition.record is not None:
            entry.records.append(transition.record)
        effects = transition.effects
        if entry.state.finished:
            effects = await self._finish(entry, effects)
        self._deliver(entry, effects)

    async def _finish(self, entry: _Session, effects: Effects) -> Effects:
        """Deja que el borde cierre la fila antes de entregar el `arcade_end`."""
        hook = entry.on_finish
        if hook is None:
            return effects
        for message in effects:
            if isinstance(message, protocols.ArcadeEnd):
                end = await hook(entry.state, tuple(entry.records), message)
                return tuple(
                    end if isinstance(item, protocols.ArcadeEnd) else item
                    for item in effects
                )
        return effects

    async def _advance(self, entry: _Session, transition: Transition) -> None:
        """Deja ver el resultado y recién después sirve el próximo ítem.

        El `ends_at` de la siguiente ronda se calcula al servir, o sea después de
        la pausa. El final de la sesión no lleva pausa extra.
        """
        if transition.record is not None and entry.state.needs_next_question:
            await self._sleep(self._reveal)
        if entry.state.needs_next_question:
            await self._serve_next(entry)

    async def _serve_next(self, entry: _Session) -> None:
        if not entry.state.needs_next_question:
            return
        item = await entry.next_item(entry.state.run, entry.state.seen)
        if item is None:
            # Sin banco no hay sesión que seguir: se avisa y se espera. La fila
            # `playing` la invalida el barrendero.
            self._error(entry, "NO_QUESTIONS", "No hay preguntas para servir.")
            return
        transition = _serve(
            entry.state,
            question=item.question,
            now_ms=self._now_ms(),
            rng=self._rng,
            allow_repeat=item.repeated,
        )
        await self._apply(entry, transition)

    async def _expiry_loop(self, entry: _Session) -> None:
        while True:
            # La sesión pudo terminar entre dos vueltas (o antes de que esta
            # tarea arrancara): sin ronda no hay plazo que esperar.
            if entry.state.finished:
                return
            try:
                await self._tick(entry)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("la sesión %s falló al vencer", entry.session_id)
                return

    async def _tick(self, entry: _Session) -> None:
        entry.wakeup.clear()
        if entry.state.finished:
            return
        deadline = _deadline(entry.state)
        if deadline is None:
            await entry.wakeup.wait()
            return
        if not await self._wait(entry, (deadline - self._now_ms()) / 1000):
            return
        async with entry.lock:
            if self._sessions.get(entry.session_id) is not entry:
                return
            # Bajo el lock el estado pudo moverse: otra acción pudo resolver la
            # ronda o servirse una nueva.
            if entry.state.finished or entry.state.round is None:
                return
            if entry.state.round.served.ends_at_ms != deadline:
                return
            if self._now_ms() < deadline:
                return
            transition = _expire(entry.state, now_ms=self._now_ms())
            await self._apply(entry, transition)
            await self._advance(entry, transition)
            entry.wakeup.set()

    async def _wait(self, entry: _Session | _Versus, timeout_s: float) -> bool:
        """`True` si venció el plazo; `False` si la sesión se despertó antes."""
        if timeout_s <= 0:
            return True
        reloj = asyncio.create_task(self._sleep(timeout_s))
        despertar = asyncio.create_task(entry.wakeup.wait())
        try:
            hechos, _ = await asyncio.wait(
                {reloj, despertar}, return_when=asyncio.FIRST_COMPLETED
            )
        finally:
            reloj.cancel()
            despertar.cancel()
            await asyncio.gather(reloj, despertar, return_exceptions=True)
        return reloj in hechos and despertar not in hechos

    def _deliver(self, entry: _Session, effects: Effects) -> None:
        for message in effects:
            _push(entry.outbox, message)

    def _error(self, entry: _Session, code: str, message: str) -> None:
        _push(
            entry.outbox,
            protocols.Error(code=code, message=message),
        )


def _start(session_id: str, rules: SoloRules) -> Transition:
    """Crea la corrida en memoria. La fila `playing` la escribe el borde."""
    engine = SoloEngine(rules)
    state = SoloState(session_id=session_id, run=engine.start())
    return Transition(
        state,
        (
            protocols.ArcadeStart(
                run_id=session_id,
                lives=state.run.lives,
                seconds=rules.seconds_for(0),
            ),
        ),
    )


def _serve(
    state: SoloState,
    *,
    question: LoadedQuestion,
    now_ms: int,
    rng: Random,
    allow_repeat: bool = False,
) -> Transition:
    """Sirve el próximo ítem. El caller ya lo eligió y cargó (eso es I/O)."""
    if state.finished:
        raise InvalidTransition("la sesión terminó: no hay ítem siguiente")
    if state.round is not None:
        raise InvalidTransition("ya hay una ronda en curso")
    if question.question.id in state.seen and not allow_repeat:
        raise InvalidTransition("el ítem ya salió en esta sesión")

    # Se baraja acá, en el último paso puro antes de servir: si dependiera del
    # llamador, olvidarlo le devolvería al cliente la respuesta en la posición
    # original (H-25).
    shuffled = shuffle_options(question, rng)
    served = SoloEngine(state.run.rules).next_question(
        state.run, question_id=shuffled.question.id, now_ms=now_ms
    )
    session = SoloState(
        session_id=state.session_id,
        run=state.run,
        round=RoundInFlight(served=served, question=shuffled),
        seen=state.seen | {shuffled.question.id},
    )
    return Transition(session, (_question_message(session, served, shuffled),))


def _answer(
    state: SoloState, *, round_index: int, choice: int, now_ms: int
) -> Transition:
    round_ = state.round
    if round_ is None or state.finished:
        return _error_transition(
            state, "NOT_PLAYING", "No hay una ronda para contestar"
        )
    if round_index != round_.served.round_index:
        return _error_transition(state, "ROUND_MISMATCH", "Esa ronda ya pasó")
    if choice not in CHOICES:
        return _error_transition(state, "BAD_CHOICE", "Opción fuera de rango")

    submission = Answer(round_index=round_index, choice=choice, answered_at_ms=now_ms)
    return _resolve(state, round_, submission)


def _expire(state: SoloState, *, now_ms: int) -> Transition:
    """La ventana se agotó: la ronda se resuelve como no contestada."""
    round_ = state.round
    if round_ is None or now_ms < round_.served.ends_at_ms:
        return Transition(state)
    return _resolve(state, round_, None)


def _resolve(
    state: SoloState, round_: RoundInFlight, answer: Answer | None
) -> Transition:
    resolved = SoloEngine(state.run.rules).resolve(
        state.run,
        round_.served,
        correct_index=round_.question.correct_index,
        answer=answer,
    )
    session = SoloState(
        session_id=state.session_id,
        run=resolved.run,
        round=None,
        seen=state.seen,
    )
    effects: list[protocols.Message] = [
        _result_message(resolved.run, resolved.record, round_.question)
    ]
    if resolved.run.finished:
        effects.append(_end_message(session))
    return Transition(session, tuple(effects), resolved.record)


def _question_message(
    state: SoloState, served: ServedQuestion, question: LoadedQuestion
) -> protocols.ArcadeQuestion:
    return protocols.ArcadeQuestion(
        round=served.round_index,
        prompt=question.question.prompt,
        options=list(question.question.options),
        category=question.question.category,
        difficulty=served.difficulty,
        seconds=served.seconds,
        ends_at=served.ends_at_ms,
        score=state.run.score,
        lives=state.run.lives,
        streak=state.run.streak,
        correct_count=state.run.correct_count,
    )


def _result_message(
    run: SoloRun, record: RoundRecord, question: LoadedQuestion
) -> protocols.ArcadeResult:
    return protocols.ArcadeResult(
        round=record.round_index,
        correct_index=record.correct_index,
        explanation=question.question.explanation,
        you=protocols.RoundChoice(
            choice=record.choice,
            ms=record.elapsed_ms,
            points=record.points,
            correct=record.correct,
        ),
        score=run.score,
        lives=run.lives,
        streak=run.streak,
        correct_count=run.correct_count,
    )


def _end_message(state: SoloState) -> protocols.ArcadeEnd:
    # El ranking es I/O: el estado puro deja las posiciones nulas y el borde las
    # completa después de cerrar la fila.
    return protocols.ArcadeEnd(
        run_id=state.session_id,
        score=state.run.score,
        correct_count=state.run.correct_count,
        max_difficulty=state.run.max_difficulty,
        longest_streak=state.run.longest_streak,
        rank_global=None,
        rank_weekly=None,
        personal_best=None,
        is_new_best=False,
    )


def _error_transition(state: SoloState, code: str, message: str) -> Transition:
    return Transition(state, (protocols.Error(code=code, message=message),))


def _deadline(state: SoloState) -> int | None:
    if state.round is None:
        return None
    return state.round.served.ends_at_ms


def _versus_deadline(state: VersusState) -> int | None:
    """El próximo instante que el reloj tiene que atender, si hay alguno.

    Mientras hay gracia, el plazo que manda es el de la gracia: la ronda está
    pausada, así que su `ends_at` no corre.
    """
    if state.grace_deadline_ms is not None:
        return state.grace_deadline_ms
    if state.round is not None and state.round.paused_since_ms is None:
        return state.round.served.ends_at_ms
    return None


def _versus_error_to_seats(
    state: VersusState, code: str, message: str
) -> versus_engine.Effects:
    error = protocols.Error(code=code, message=message)
    return {seat.user_id: (error,) for seat in state.seats if seat is not None}


def _cancel(entry: _Versus) -> None:
    if entry.task is not None:
        entry.task.cancel()


def _push(outbox: Outbox, message: protocols.Message) -> None:
    try:
        outbox.put_nowait(message)
    except asyncio.QueueFull:
        # El cliente dejó de leer (TCP sin drenar): se descarta lo más viejo y
        # queda lo más nuevo. La conexión la corta el timeout de inactividad.
        outbox.get_nowait()
        outbox.put_nowait(message)
        logger.warning("el outbox de una sesión se llenó: se descartó un mensaje")


def _system_now_ms() -> int:
    return int(time.time() * 1000)


# El estado vivo del proceso, compartido por el handler del WebSocket y por el
# barrido periódico: un objeto por proceso, no uno por pedido.
session_store = InMemorySessionStore()
