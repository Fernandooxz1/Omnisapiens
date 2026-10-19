"""Las sesiones en vivo de un solo jugador: estado, entrega, reloj y vencimientos.

`room_manager.py` resuelve lo mismo para una sala con sillas. Acá hay una sola
conexión, así que sobran el lobby, la gracia y el lock por silla: queda el estado
del motor, el `outbox` de esa conexión y una tarea que vence la ronda servida.

`SessionStore` es el contrato, no la implementación. El handler dependerá de la
interfaz y este archivo podrá mudarse a Redis el día que haya más de un proceso.
La sesión es de una conexión: si el socket se cae, `close` la saca de memoria y
la fila queda `playing` para que el barrendero la invalide. Media sesión no
compite en el ranking.

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
from app.game import protocols
from app.game.answers import Answer, ServedQuestion
from app.game.constants import CHOICES
from app.game.errors import InvalidTransition
from app.game.solo_engine import RoundRecord, SoloEngine, SoloRules, SoloRun
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


class SessionStore(Protocol):
    """Lo que el borde necesita de una sesión solo (fase 4.1).

    Fase 5 extiende la implementación con sillas para el versus; el handler del
    WebSocket sigue dependiendo de la interfaz, no de la clase.
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


class InMemorySessionStore:
    """La implementación de un solo proceso: todas las sesiones en memoria."""

    def __init__(
        self,
        *,
        reveal_seconds: float | None = None,
        now_ms: Clock | None = None,
        sleep: Sleeper | None = None,
        rng: Random | None = None,
    ) -> None:
        # `None` lee `settings.reveal_seconds` al dormir: el test puede bajarla o
        # subirla después de construir el store, igual que el handler viejo.
        self._reveal_seconds = reveal_seconds
        self._now_ms = now_ms or _system_now_ms
        self._sleep = sleep or asyncio.sleep
        self._rng = rng or Random()
        self._sessions: dict[str, _Session] = {}

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

    async def close(self, *, session_id: str | None = None) -> None:
        if session_id is None:
            entries = list(self._sessions.values())
            self._sessions.clear()
        else:
            entry = self._sessions.pop(session_id, None)
            entries = [entry] if entry is not None else []

        tasks = [entry.task for entry in entries if entry.task is not None]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    def live(self) -> frozenset[uuid.UUID]:
        return frozenset(
            entry.session_uuid
            for entry in self._sessions.values()
            if not entry.state.finished
        )

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

    async def _wait(self, entry: _Session, timeout_s: float) -> bool:
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
