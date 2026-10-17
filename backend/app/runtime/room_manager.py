"""Las salas en vivo: lock, entrega, vencimientos y las dos escrituras de la partida.

`room.py` decide *qué* pasa; acá se le pone lo que le falta para funcionar con
gente conectada: el lock por sala, el reloj, la entrega a cada jugador, la tarea
que dispara los vencimientos y las dos escrituras de la partida en Postgres
(§5.4: la fila de `matches` al arrancar, el `UPDATE` y sus rondas al terminar).

`RoomStore` es el contrato (A3.6), no la implementación: el handler del WebSocket
va a depender de la interfaz, así el día que haya más de una instancia del backend
se escribe otra implementación y el handler no se toca.

Tres cosas que sorprenden a primera vista:

- La sesión de base se abre y se commitea acá adentro: el manager no corre dentro
  de un pedido HTTP, así que no hereda el commit de `get_session` (mismo criterio
  que la CLI: el borde del pedido es el borde de la transacción, pero acá no hay
  pedido).
- El reloj y el `sleep` se inyectan: los tests corren una partida entera por
  vencimientos sin esperar los 20 s reales de cada ronda.
- Se guarda el `outbox` (una cola) de cada jugador y no un callback: el
  vencimiento tiene que poder entregar sin que haya nadie esperando del otro lado.
"""

import asyncio
import logging
import time
import uuid
from collections.abc import Callable, Coroutine
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from random import Random
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import session_factory
from app.game import protocols
from app.game.constants import CATEGORIES
from app.game.match_engine import (
    MatchConfig,
    MatchStatus,
    Player,
    RoundRecord,
    difficulty_range,
)
from app.models import Match, MatchRound
from app.runtime import room
from app.runtime.room import Effects, RoomState, Transition
from app.services.question_bank import LoadedQuestion, candidates, load
from app.services.questions import select

logger = logging.getLogger(__name__)

Outbox = asyncio.Queue[protocols.Message]
Clock = Callable[[], int]
Sleeper = Callable[[float], Coroutine[object, object, None]]
# Acepta tanto un `async_sessionmaker` como un envoltorio que comparta una sesión
# ya abierta (es lo que hacen los tests para no salirse de su transacción).
SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]


class RoomStore(Protocol):
    """Lo que el WebSocket de una sala necesita del estado vivo (A3.6).

    Todos los métodos entregan los mensajes en los `outbox` de la sala: no
    devuelven nada, porque el receptor no es quien llama.
    """

    async def open(
        self, *, code: str, room_id: str, config: MatchConfig, host_id: str
    ) -> None:
        """Da de alta la sala viva. Idempotente: reconectar no la reinicia."""
        ...

    async def join(self, *, code: str, user_id: str, nick: str, outbox: Outbox) -> None:
        """Sienta a un jugador (o lo reconecta) y le manda el estado."""
        ...

    async def sync(self, *, code: str, user_id: str) -> None:
        """Reenvía el estado completo al que manda `hello`."""
        ...

    async def start(self, *, code: str, user_id: str) -> None:
        """El host arranca la partida: fila de `matches` y primera ronda."""
        ...

    async def answer(
        self, *, code: str, user_id: str, round_index: int, choice: int
    ) -> None: ...

    async def disconnect(self, *, code: str, user_id: str) -> None: ...

    async def rematch(self, *, code: str, user_id: str) -> None: ...

    def player_count(self, code: str) -> int:
        """Cuántos jugadores hay conectados: la presencia que le falta a la vista previa."""
        ...

    def seated(self, *, code: str, user_id: str) -> bool:
        """Si ese usuario tiene silla.

        Lo consulta el handler después de `join`: un tercero ya recibió su
        `ROOM_FULL` en el `outbox` y hay que cortarle la conexión.
        """
        ...

    async def close(self) -> None:
        """Corta las tareas de vencimiento (shutdown del proceso)."""
        ...


@dataclass
class _Room:
    """La sala viva: su estado puro más lo que el estado puro no puede tener."""

    room_id: str
    state: RoomState
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    outboxes: dict[str, Outbox] = field(default_factory=dict)
    # Despierta a la tarea de vencimientos cuando cambió el estado: así no hay
    # polling y el plazo se recalcula con la sala ya quieta.
    wakeup: asyncio.Event = field(default_factory=asyncio.Event)
    task: asyncio.Task[None] | None = None


class InMemoryRoomStore:
    """La implementación de un solo proceso: todo el estado en memoria.

    Alcance: una instancia del backend. Con dos instancias, dos salas con el mismo
    código vivirían en procesos distintos; ese día entra otra implementación de
    `RoomStore` (con Pub/Sub), no un parche acá.
    """

    def __init__(
        self,
        *,
        session_factory: SessionFactory,
        grace_seconds: int,
        now_ms: Clock | None = None,
        sleep: Sleeper | None = None,
        rng: Random | None = None,
    ) -> None:
        self._sessions = session_factory
        self._grace_seconds = grace_seconds
        self._now_ms = now_ms or _system_now_ms
        self._sleep = sleep or asyncio.sleep
        self._rng = rng or Random()
        self._rooms: dict[str, _Room] = {}

    async def open(
        self, *, code: str, room_id: str, config: MatchConfig, host_id: str
    ) -> None:
        if code in self._rooms:
            return
        entry = _Room(
            room_id=room_id,
            state=RoomState(code=code, config=config, host_id=host_id),
        )
        self._rooms[code] = entry
        entry.task = asyncio.create_task(self._expiry_loop(entry))

    async def join(self, *, code: str, user_id: str, nick: str, outbox: Outbox) -> None:
        entry = self._entry(code)
        if entry is None:
            return
        async with entry.lock:
            entry.outboxes[user_id] = outbox
            await self._step(
                entry,
                lambda state: room.join(
                    state, user_id=user_id, nick=nick, now_ms=self._now_ms()
                ),
            )
            if entry.state.player_of(user_id) is None:
                # Un tercero: ya recibió su error y no queda colgado en la sala.
                entry.outboxes.pop(user_id, None)

    async def sync(self, *, code: str, user_id: str) -> None:
        await self._act(
            code,
            lambda state: room.sync(state, user_id=user_id, now_ms=self._now_ms()),
        )

    async def start(self, *, code: str, user_id: str) -> None:
        # El id se acuña acá y viaja al mensaje: la fila de `matches` se escribe
        # cuando la transición confirma que la partida arrancó de verdad.
        match_id = str(uuid.uuid4())
        await self._act(
            code, lambda state: room.start(state, user_id=user_id, match_id=match_id)
        )

    async def answer(
        self, *, code: str, user_id: str, round_index: int, choice: int
    ) -> None:
        await self._act(
            code,
            lambda state: room.answer(
                state,
                user_id=user_id,
                round_index=round_index,
                choice=choice,
                now_ms=self._now_ms(),
            ),
        )

    async def disconnect(self, *, code: str, user_id: str) -> None:
        entry = self._entry(code)
        if entry is None:
            return
        async with entry.lock:
            # Se suelta el `outbox` antes de la transición: mensajes para un
            # socket que ya se fue no le sirven a nadie y se acumularían.
            entry.outboxes.pop(user_id, None)
            await self._step(
                entry,
                lambda state: room.disconnect(
                    state,
                    user_id=user_id,
                    now_ms=self._now_ms(),
                    grace_seconds=self._grace_seconds,
                ),
            )

    async def rematch(self, *, code: str, user_id: str) -> None:
        # Igual que `start`: el id viaja aunque el pedido sea el primero de los
        # dos y la partida nueva todavía no arranque.
        match_id = str(uuid.uuid4())
        await self._act(
            code, lambda state: room.rematch(state, user_id=user_id, match_id=match_id)
        )

    def player_count(self, code: str) -> int:
        entry = self._rooms.get(code)
        if entry is None:
            return 0
        return sum(
            1 for seat in entry.state.seats if seat is not None and seat.connected
        )

    def seated(self, *, code: str, user_id: str) -> bool:
        entry = self._rooms.get(code)
        return entry is not None and entry.state.player_of(user_id) is not None

    async def close(self) -> None:
        tasks = [entry.task for entry in self._rooms.values() if entry.task]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._rooms.clear()

    def _entry(self, code: str) -> _Room | None:
        return self._rooms.get(code)

    async def _act(
        self, code: str, transition: Callable[[RoomState], Transition]
    ) -> None:
        entry = self._entry(code)
        if entry is None:
            return
        async with entry.lock:
            await self._step(entry, transition)

    async def _step(
        self, entry: _Room, transition: Callable[[RoomState], Transition]
    ) -> None:
        """Aplica una transición con el lock tomado y hace sonar todo lo que cuelga.

        El orden importa: primero la base, después la entrega, y por último la
        ronda siguiente. Si la base falla, el estado en memoria vuelve atrás,
        porque nadie vio todavía nada.
        """
        before = entry.state
        after, effects = transition(before)
        entry.state = after
        try:
            await self._persist(entry, before, after)
        except Exception:
            entry.state = before
            raise
        try:
            await _deliver(entry, effects)
            await self._serve_next(entry)
        finally:
            # Cambió el estado (o falló a mitad): el reloj tiene que recalcular.
            entry.wakeup.set()

    async def _serve_next(self, entry: _Room) -> None:
        """Sirve la ronda siguiente si el motor ya la pidió.

        Es lo que cierra el ciclo: contestar la última respuesta y vencer el
        reloj desembocan los dos acá.
        """
        if not entry.state.needs_next_round:
            return
        question = await self._pick(entry.state)
        if question is None:
            # Sin banco no hay partida que seguir. La sala queda como está y la
            # fila de `matches` en `playing` la barre el barrendero.
            await _deliver(
                entry,
                _error_to_seats(
                    entry.state, "NO_QUESTIONS", "No hay preguntas para servir."
                ),
            )
            return
        after, effects = room.serve(
            entry.state, question=question, now_ms=self._now_ms()
        )
        entry.state = after
        await _deliver(entry, effects)

    async def _pick(self, state: RoomState) -> LoadedQuestion | None:
        """Elige y carga la pregunta de la ronda.

        El pool se recorta al tramo de dificultad de la ronda: `next_round` exige
        que la dificultad de la pregunta entre en el tramo, y una pregunta en
        rango cercano la rompería. Antes queda descartado lo ya visto en la partida.
        """
        match = state.match
        if match is None:
            return None
        low, high = difficulty_range(match)
        used = {record.question_id for record in match.rounds}
        async with self._sessions() as session:
            pool = [
                candidate
                for candidate in await candidates(session)
                if low <= candidate.difficulty <= high
            ]
            if not pool:
                logger.warning(
                    "la sala %s no tiene preguntas en el tramo %s-%s",
                    state.code,
                    low,
                    high,
                )
                return None
            selection = select(
                pool,
                category=self._rng.choice(CATEGORIES),
                difficulty=self._rng.randint(low, high),
                rng=self._rng,
                excluded=used,
            )
            return await load(session, selection.question_id)

    async def _persist(self, entry: _Room, before: RoomState, after: RoomState) -> None:
        """Las dos escrituras de §5.4, más la revancha, que abre una partida nueva."""
        if after.match is None:
            return
        playing = after.match.status is MatchStatus.PLAYING
        if playing and (
            before.match is None or before.match.status is not MatchStatus.PLAYING
        ):
            await self._write_match(entry, after)
        elif (
            before.match is not None
            and before.match.status is MatchStatus.PLAYING
            and not playing
        ):
            await self._close_match(after)

    async def _write_match(self, entry: _Room, state: RoomState) -> None:
        assert state.match_id is not None
        match = Match(
            id=uuid.UUID(state.match_id),
            room_id=uuid.UUID(entry.room_id),
            player_a_id=uuid.UUID(_player_id(state, Player.A)),
            player_b_id=uuid.UUID(_player_id(state, Player.B)),
            config={
                "rounds": state.config.rounds,
                "seconds": state.config.seconds,
            },
            status=MatchStatus.PLAYING.value,
        )
        async with self._sessions() as session:
            session.add(match)
            await session.commit()

    async def _close_match(self, state: RoomState) -> None:
        assert state.match is not None and state.match_id is not None
        match_id = uuid.UUID(state.match_id)
        async with self._sessions() as session:
            match = await session.get(Match, match_id)
            if match is None:
                logger.warning("la partida %s no estaba en la base", match_id)
                return
            match.status = state.match.status.value
            match.score_a = state.match.score_a
            match.score_b = state.match.score_b
            match.winner_id = (
                None
                if state.match.winner is None
                else uuid.UUID(_player_id(state, state.match.winner))
            )
            match.ended_at = datetime.now(UTC)
            session.add_all(_round_rows(match_id, state.match.rounds))
            await session.commit()

    async def _expiry_loop(self, entry: _Room) -> None:
        """Vence lo que el reloj tenga que vencer, sin polling.

        Duerme hasta el próximo plazo y se despierta antes si la sala cambió. El
        `clear` va antes de leer el estado: un cambio que llegue después deja el
        evento puesto y la espera vuelve enseguida.

        Un error acá no se reintenta: la sala se quedaría girando en vacío contra
        la base. Se corta la tarea, el rastro queda en el log y la fila abierta la
        cierra el barrendero.
        """
        try:
            while True:
                entry.wakeup.clear()
                deadline = _next_deadline(entry.state)
                if deadline is None:
                    await entry.wakeup.wait()
                    continue
                if not await self._wait(entry, (deadline - self._now_ms()) / 1000):
                    continue
                async with entry.lock:
                    # Bajo el lock el estado puede haberse movido: otra acción pudo
                    # resolver la ronda, o recién servirse una nueva.
                    if _next_deadline(entry.state) != deadline:
                        continue
                    if self._now_ms() < deadline:
                        continue
                    await self._step(
                        entry, lambda state: room.expire(state, now_ms=self._now_ms())
                    )
        except Exception:
            logger.exception("la sala %s quedó sin vencimientos", entry.state.code)

    async def _wait(self, entry: _Room, timeout_s: float) -> bool:
        """`True` si venció el plazo; `False` si la sala se despertó antes."""
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


async def _deliver(entry: _Room, effects: Effects) -> None:
    for user_id, messages in effects.items():
        outbox = entry.outboxes.get(user_id)
        if outbox is None:
            continue
        for message in messages:
            await outbox.put(message)


def _error_to_seats(state: RoomState, code: str, message: str) -> Effects:
    error = protocols.Error(code=code, message=message)
    return {seat.user_id: (error,) for seat in state.seats if seat is not None}


def _next_deadline(state: RoomState) -> int | None:
    """El próximo instante que el reloj tiene que atender, si hay alguno.

    Mientras hay gracia, el plazo que manda es el de la gracia: la ronda está
    pausada, así que su `ends_at` no corre.
    """
    if state.grace_deadline_ms is not None:
        return state.grace_deadline_ms
    if state.round is not None and state.round.paused_since_ms is None:
        return state.round.served.ends_at_ms
    return None


def _player_id(state: RoomState, player: Player) -> str:
    seat = state.seats[0 if player is Player.A else 1]
    assert seat is not None
    return seat.user_id


def _round_rows(
    match_id: uuid.UUID, rounds: tuple[RoundRecord, ...]
) -> list[MatchRound]:
    return [
        MatchRound(
            id=uuid.uuid4(),
            match_id=match_id,
            round_index=record.round_index,
            question_id=uuid.UUID(record.question_id),
            difficulty=record.difficulty,
            seconds=record.seconds,
            correct_index=record.correct_index,
            a_choice=record.a_choice,
            b_choice=record.b_choice,
            a_ms=record.a_ms,
            b_ms=record.b_ms,
            a_correct=record.a_correct,
            b_correct=record.b_correct,
            a_points=record.a_points,
            b_points=record.b_points,
            a_rejected=record.a_rejected.value if record.a_rejected else None,
            b_rejected=record.b_rejected.value if record.b_rejected else None,
        )
        for record in rounds
    ]


def _system_now_ms() -> int:
    return int(time.time() * 1000)


# El estado vivo del proceso, compartido por el handler del WebSocket y por la
# vista previa de `/rooms/{code}`: mismo criterio que `engine` y `redis_client`,
# un objeto por proceso y no uno por pedido.
room_store = InMemoryRoomStore(
    session_factory=session_factory,
    grace_seconds=settings.reconnect_grace_seconds,
)
