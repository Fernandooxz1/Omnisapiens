"""El WebSocket de una sala: el borde del versus sobre el store de sesiones.

Es el controlador del canal en vivo. La sala la decide `runtime/session_store`
(sillas, gracia, pausa, vencimientos y entrega); acá viven el socket, la elección
y carga de la pregunta, y la escritura de la sesión genérica de `game_sessions`
con su historial. `rooms` sigue siendo el lobby y el borde mantiene su estado.

Tres cosas que sorprenden a primera vista:

- El token llega por `?token=`: el navegador no deja mandar headers en
  `new WebSocket`, así que el `Authorization` de HTTP no sirve acá.
- El socket lo escribe una sola corrutina en régimen: la que drena el `outbox`.
  El lector, cuando responde por su cuenta (`pong`, un error), pasa por el mismo
  lock: dos `send` en paralelo sobre el mismo socket no son seguros.
- El store avisa cuándo empieza y termina una partida, pero no toca la base: el
  borde abre una sesión propia para persistir, porque el vencimiento puede
  cerrar la partida después de que el handler ya se fue.
"""

import asyncio
import contextlib
import json
import logging
import time
import uuid
from collections.abc import Callable, Iterable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from random import Random
from typing import Annotated, Any, TypeGuard

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketDisconnected

from app.api.deps import SessionDep, authenticate
from app.api.errors import ApiError
from app.api.rate_limit import room_limit
from app.config import settings
from app.db import session_factory
from app.game import protocols, versus_engine
from app.game.constants import CATEGORIES, DIFFICULTY_MIN
from app.game.versus_engine import MatchStatus, VersusConfig, VersusState
from app.models import GameSession, Room, User
from app.runtime.session_store import (
    OUTBOX_MAX,
    VersusSessionStore,
    session_store,
)
from app.services import sessions
from app.services.question_bank import LoadedQuestion, candidates, load
from app.services.questions import select
from app.services.rooms import get_by_code, room_is_available

logger = logging.getLogger(__name__)

router = APIRouter()

# Rechazo de entrada (token, sala, sala llena): el cliente no debe reintentar igual.
_CLOSE_POLICY = 1008

# La sesión genérica de la sala: el formato versus fija su configuración con
# `ruleset_version` y su solución con `solution_version`.
VERSUS_MODE = "trivia_versus"
CONTENT_KIND = "quiz"
PLAY_FORMAT = "versus"
RULESET_VERSION = 1
SOLUTION_VERSION = 1

Clock = Callable[[], int]
# El borde abre su propia sesión de base: el vencimiento puede correr cuando el
# handler (y su `SessionDep`) ya no existen.
SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]


@dataclass(frozen=True)
class RoomRuntime:
    """Lo que el handler no puede inventar: el reloj y el azar."""

    now_ms: Clock
    rng: Random


def get_room_store() -> VersusSessionStore:
    """El store del proceso, inyectado.

    Los tests ponen uno con reloj falso y su propia sesión; en producción es el
    global del proceso, el mismo que apaga el lifespan.
    """
    return session_store


def get_room_runtime() -> RoomRuntime:
    return RoomRuntime(now_ms=_system_now_ms, rng=Random())


def get_room_session_factory() -> SessionFactory:
    """La fábrica del borde; los tests la apuntan a su sesión compartida."""
    return session_factory


StoreDep = Annotated[VersusSessionStore, Depends(get_room_store)]
RuntimeDep = Annotated[RoomRuntime, Depends(get_room_runtime)]
FactoryDep = Annotated[SessionFactory, Depends(get_room_session_factory)]


@router.websocket("/ws/room/{code}")
async def room_socket(
    websocket: WebSocket,
    code: str,
    session: SessionDep,
    store: StoreDep,
    runtime: RuntimeDep,
    db_factory: FactoryDep,
) -> None:
    # Se acepta antes de autenticar: si no, un token malo no tiene por dónde
    # recibir el `error` con el que el cliente vuelve al inicio (§12).
    await websocket.accept()
    try:
        await room_limit(websocket.client.host if websocket.client else None)
        usuario = await _identify(websocket, session)
        sala = await _load_room(session, code)
    except ApiError as exc:
        await _send(websocket, protocols.Error(code=exc.code, message=exc.message))
        await websocket.close(code=_CLOSE_POLICY)
        return

    codigo = sala.code
    user_id = str(usuario.id)
    border = _Border(db=db_factory, runtime=runtime, room_id=str(sala.id))
    await store.open_versus(
        code=codigo,
        room_id=str(sala.id),
        config=VersusConfig(**sala.config),
        host_id=str(sala.host_user_id),
        next_item=border.next_item,
        on_match_start=border.match_started,
        on_match_end=border.match_finished,
        on_room_reopened=border.room_reopened,
    )

    outbox: asyncio.Queue[protocols.Message] = asyncio.Queue(maxsize=OUTBOX_MAX)
    await store.join(code=codigo, user_id=user_id, nick=usuario.nick, outbox=outbox)
    send_lock = asyncio.Lock()
    if not store.seated(code=codigo, user_id=user_id):
        # El store ya dejó su `ROOM_FULL` en la cola: se manda y se corta, porque
        # una conexión sin silla no tiene a quién entregarle nada.
        await _flush(websocket, outbox)
        await websocket.close(code=_CLOSE_POLICY)
        return

    reader = asyncio.create_task(
        _reader(
            websocket,
            send_lock,
            store,
            code=codigo,
            user_id=user_id,
            idle_s=settings.ws_idle_timeout_seconds,
        )
    )
    writer = asyncio.create_task(_writer(websocket, send_lock, outbox))
    try:
        done, _ = await asyncio.wait(
            {reader, writer}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in done:
            error = task.exception()
            if error is not None and not _is_gone(error):
                # El canal se rompió: la conexión se cierra igual y el que quedó
                # adentro entra en la ventana de gracia. El rastro queda en el log.
                logger.error("el canal de la sala %s se cortó", codigo, exc_info=error)
    finally:
        for task in (reader, writer):
            task.cancel()
        await asyncio.gather(reader, writer, return_exceptions=True)
        await _close(websocket)
        await store.disconnect(code=codigo, user_id=user_id, outbox=outbox)


class _Border:
    """La parte del borde que el store llama: ítems y persistencia."""

    def __init__(
        self, *, db: SessionFactory, runtime: RoomRuntime, room_id: str
    ) -> None:
        self._db = db
        self._runtime = runtime
        self._room_id = room_id

    async def next_item(self, state: VersusState) -> LoadedQuestion | None:
        """Elige y carga la pregunta. La base es de afuera del store."""
        match = state.match
        if match is None:
            return None
        low, high = versus_engine.difficulty_range(match)
        used = {record.question_id for record in match.rounds}
        async with self._db() as session:
            pool = await candidates(session, low=low, high=high)
            if not pool:
                # Sin banco no hay partida que seguir: el store avisa y espera.
                logger.warning(
                    "la sala %s no tiene preguntas en el tramo %s-%s",
                    state.code,
                    low,
                    high,
                )
                return None
            selection = select(
                pool,
                category=self._runtime.rng.choice(CATEGORIES),
                difficulty=self._runtime.rng.randint(low, high),
                rng=self._runtime.rng,
                excluded=used,
            )
            return await load(session, selection.question_id)

    async def match_started(self, state: VersusState, now_ms: int) -> None:
        """La fila `playing` de la sesión genérica; la sala pasa a `playing`."""
        match = state.match
        if match is None or state.match_id is None:
            return
        participants = [
            sessions.Participant(seat=seat, user_id=uuid.UUID(player.user_id))
            for seat, player in enumerate(state.seats)
            if player is not None
        ]
        try:
            async with self._db() as session:
                await _mark_room_playing(session, self._room_id, state.config, now_ms)
                await sessions.start_session(
                    session,
                    session_id=uuid.UUID(state.match_id),
                    mode=VERSUS_MODE,
                    content_kind=CONTENT_KIND,
                    play_format=PLAY_FORMAT,
                    ruleset_version=RULESET_VERSION,
                    config={
                        "rounds": state.config.rounds,
                        "seconds": state.config.seconds,
                    },
                    started_at=_datetime(now_ms),
                    room_id=uuid.UUID(self._room_id),
                    participants=participants,
                )
        except Exception:
            # Sin fila no se juega: el store revierte el arranque y el cliente
            # puede reintentarlo en otra conexión.
            logger.exception("la partida %s no se pudo registrar", state.match_id)
            raise

    async def match_finished(self, state: VersusState, now_ms: int) -> None:
        """Cierra la sesión genérica y guarda el historial de las dos sillas.

        Es best-effort: si la base falla, el jugador ya vio su final y la fila
        queda `playing` para que el barrendero la invalide.
        """
        match = state.match
        if match is None or state.match_id is None:
            return
        match_id = uuid.UUID(state.match_id)
        try:
            async with self._db() as session:
                row = await session.get(GameSession, match_id)
                if row is None:
                    logger.error("la partida %s no estaba en la base", match_id)
                    return
                if row.status != "playing":
                    return
                await _mark_room_finished(session, self._room_id)
                items, attempts = _history(match, row.started_at)
                await sessions.finish_session(
                    session,
                    session_id=match_id,
                    state=_summary(match, now_ms),
                    items=items,
                    attempts=attempts,
                    participants=_participants(match, state.seats),
                )
        except Exception:
            logger.exception("la partida %s no se pudo cerrar", match_id)

    async def room_reopened(self, state: VersusState, now_ms: int) -> None:
        """Una sala terminada vuelve al lobby: la fila tiene que decir lo mismo."""
        try:
            async with self._db() as session:
                sala = await session.get(Room, uuid.UUID(self._room_id))
                if sala is None:
                    return
                sala.status = versus_engine.VersusStatus.WAITING.value
                sala.expires_at = _datetime(now_ms) + timedelta(
                    seconds=settings.room_idle_timeout_seconds
                )
                await session.commit()
        except Exception:
            logger.exception("la sala %s no se pudo reabrir", self._room_id)


async def _identify(websocket: WebSocket, session: AsyncSession) -> User:
    token = websocket.query_params.get("token")
    if not token:
        raise ApiError(401, "AUTH_REQUIRED", "Se necesita un token válido.")
    return await authenticate(session, token)


async def _load_room(session: AsyncSession, code: str) -> Room:
    sala = await get_by_code(session, code)
    if sala is None or not room_is_available(sala):
        raise ApiError(404, "ROOM_NOT_FOUND", "No hay una sala con ese código.")
    return sala


async def _reader(
    websocket: WebSocket,
    lock: asyncio.Lock,
    store: VersusSessionStore,
    *,
    code: str,
    user_id: str,
    idle_s: float,
) -> None:
    """Lee el socket y traduce. Vuelve cuando el cliente se va o se queda mudo."""
    while True:
        try:
            raw = await asyncio.wait_for(websocket.receive_text(), idle_s)
        except WebSocketDisconnect:
            return
        except TimeoutError:
            logger.info("la sala %s cortó a %s por inactividad", code, user_id)
            return

        pedido = _parse(raw)
        if pedido is None:
            await _send(
                websocket,
                protocols.Error(
                    code="BAD_MESSAGE", message="El mensaje no tiene la forma esperada."
                ),
                lock=lock,
            )
            continue
        tipo, datos, correlacion = pedido
        await _dispatch(
            websocket,
            lock,
            store,
            code=code,
            user_id=user_id,
            tipo=tipo,
            datos=datos,
            correlacion=correlacion,
        )


async def _dispatch(
    websocket: WebSocket,
    lock: asyncio.Lock,
    store: VersusSessionStore,
    *,
    code: str,
    user_id: str,
    tipo: str,
    datos: dict[str, Any],
    correlacion: str | None,
) -> None:
    if tipo == "ping":
        await _send(websocket, protocols.Pong(), lock=lock, correlacion=correlacion)
    elif tipo == "hello":
        # Al conectar ya se hizo `join`; esto repinta el estado completo y, de
        # paso, la ronda en curso con su `ends_at` original (§10.3).
        await store.sync(code=code, user_id=user_id)
    elif tipo == "start":
        await store.start(code=code, user_id=user_id)
    elif tipo == "answer":
        respuesta = _answer(datos)
        if respuesta is None:
            await _send(
                websocket,
                protocols.Error(code="BAD_MESSAGE", message="Respuesta mal formada."),
                lock=lock,
                correlacion=correlacion,
            )
            return
        ronda, eleccion = respuesta
        await store.answer(
            code=code, user_id=user_id, round_index=ronda, choice=eleccion
        )
    elif tipo == "rematch":
        await store.rematch(code=code, user_id=user_id)
    else:
        await _send(
            websocket,
            protocols.Error(
                code="UNKNOWN_MESSAGE", message=f"Tipo de mensaje desconocido: {tipo}"
            ),
            lock=lock,
            correlacion=correlacion,
        )


async def _writer(
    websocket: WebSocket,
    lock: asyncio.Lock,
    outbox: asyncio.Queue[protocols.Message],
) -> None:
    """Lo que el store entrega, al socket. En régimen, el único que escribe."""
    while True:
        await _send(websocket, await outbox.get(), lock=lock)


def _parse(raw: str) -> tuple[str, dict[str, Any], str | None] | None:
    try:
        sobre = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(sobre, dict):
        return None
    tipo = sobre.get("t")
    datos = sobre.get("d", {})
    correlacion = sobre.get("id")
    if not isinstance(tipo, str) or not isinstance(datos, dict):
        return None
    if correlacion is not None and not isinstance(correlacion, str):
        return None
    return tipo, datos, correlacion


def _answer(datos: dict[str, Any]) -> tuple[int, int] | None:
    """`(ronda, opción)` si los dos son enteros. `bool` es `int`: se descarta."""
    ronda = datos.get("round")
    eleccion = datos.get("choice")
    if not _is_int(ronda) or not _is_int(eleccion):
        return None
    return ronda, eleccion


def _is_int(valor: object) -> TypeGuard[int]:
    return isinstance(valor, int) and not isinstance(valor, bool)


async def _send(
    websocket: WebSocket,
    message: protocols.Message,
    *,
    lock: asyncio.Lock | None = None,
    correlacion: str | None = None,
) -> None:
    if lock is None:
        # Camino de entrada: todavía no hay `outbox` ni escritor con quien competir.
        await websocket.send_json(protocols.encode(message, id=correlacion))
        return
    async with lock:
        await websocket.send_json(protocols.encode(message, id=correlacion))


async def _flush(
    websocket: WebSocket, outbox: asyncio.Queue[protocols.Message]
) -> None:
    while not outbox.empty():
        await _send(websocket, outbox.get_nowait())


def _is_gone(error: BaseException) -> bool:
    """Un corte esperado: el cliente se fue, no un error del handler."""
    return isinstance(error, (WebSocketDisconnect, WebSocketDisconnected))


async def _close(websocket: WebSocket) -> None:
    """Cierra el socket si sigue abierto; si el cliente se fue, no hay más que hacer."""
    with contextlib.suppress(WebSocketDisconnect, WebSocketDisconnected):
        await websocket.close()


def _datetime(ms: int) -> datetime:
    """El instante del servidor, en UTC. La base guarda `timestamptz`."""
    return datetime.fromtimestamp(ms / 1000, tz=UTC)


async def _mark_room_playing(
    session: AsyncSession, room_id: str, config: VersusConfig, now_ms: int
) -> None:
    """La sala deja de ser `waiting` y su vencimiento pasa a ser el techo de la partida.

    Si el barrendero mirara solo `expires_at`, una partida viva con la fecha vieja
    sería una víctima (H-04).
    """
    sala = await session.get(Room, uuid.UUID(room_id))
    if sala is None:
        return
    sala.status = versus_engine.VersusStatus.PLAYING.value
    sala.expires_at = _datetime(now_ms) + timedelta(
        seconds=_match_ceiling_seconds(config)
    )


async def _mark_room_finished(session: AsyncSession, room_id: str) -> None:
    """La sala pasa a `finished` al cerrar la sesión genérica."""
    sala = await session.get(Room, uuid.UUID(room_id))
    if sala is not None:
        sala.status = versus_engine.VersusStatus.FINISHED.value


def _match_ceiling_seconds(config: VersusConfig) -> int:
    """Techo de una partida: cada ronda con su ventana y una gracia por ronda."""
    return config.rounds * (config.seconds + settings.reconnect_grace_seconds) + 60


def _summary(match: versus_engine.MatchState, now_ms: int) -> sessions.SessionState:
    """El resumen de la sesión, con el mismo criterio que el backfill."""
    return sessions.SessionState(
        ended_at=_datetime(now_ms),
        status=_session_status(match.status),
        score=max(match.score_a, match.score_b),
        correct_count=sum(
            1
            for record in match.rounds
            for correct in (record.a_correct, record.b_correct)
            if correct
        ),
        longest_streak=max(
            _longest_streak(record.a_correct for record in match.rounds),
            _longest_streak(record.b_correct for record in match.rounds),
        ),
        max_difficulty=max(
            (record.difficulty for record in match.rounds), default=DIFFICULTY_MIN
        ),
    )


def _session_status(status: MatchStatus) -> str:
    return {
        MatchStatus.FINISHED: "finished",
        MatchStatus.ABANDONED: "abandoned",
        MatchStatus.VOID: "void",
    }[status]


def _participants(
    match: versus_engine.MatchState, seats: tuple[versus_engine.Seat | None, ...]
) -> list[sessions.ParticipantResult]:
    """El resultado de cada silla, con el mismo criterio que el backfill."""
    outcomes = _outcomes(match)
    results: list[sessions.ParticipantResult] = []
    for seat, player in enumerate(seats):
        if player is None:
            continue
        results.append(
            sessions.ParticipantResult(
                seat=seat,
                score=match.score_a if seat == 0 else match.score_b,
                outcome=outcomes[seat],
            )
        )
    return results


def _outcomes(match: versus_engine.MatchState) -> tuple[str, str]:
    if match.status is MatchStatus.FINISHED:
        if match.winner is None:
            return "draw", "draw"
        if match.winner is versus_engine.Player.A:
            return "win", "lose"
        return "lose", "win"
    if match.status is MatchStatus.ABANDONED:
        return "abandoned", "abandoned"
    return "void", "void"


def _longest_streak(flags: Iterable[bool]) -> int:
    best = current = 0
    for correct in flags:
        current = current + 1 if correct else 0
        best = max(best, current)
    return best


def _history(
    match: versus_engine.MatchState, started_at: datetime
) -> tuple[list[sessions.ItemRecord], list[sessions.AttemptRecord]]:
    """Reconstruye ítems e intentos contiguos desde el arranque, como el backfill.

    Las tablas viejas no guardan el instante de cada ronda; el camino en vivo
    tampoco lo necesita para auditar: lo que importa es la secuencia, los
    puntajes y los milisegundos de cada respuesta.
    """
    items: list[sessions.ItemRecord] = []
    attempts: list[sessions.AttemptRecord] = []
    cursor = started_at
    window_ms = 0

    for record in match.rounds:
        served_at = cursor
        window_ms = record.seconds * 1000
        a_elapsed = record.a_ms if record.a_ms is not None else window_ms
        b_elapsed = record.b_ms if record.b_ms is not None else window_ms
        closed_at = served_at + _delta_ms(max(a_elapsed, b_elapsed))
        items.append(
            sessions.ItemRecord(
                item_key=str(record.round_index),
                position=record.round_index,
                content_id=uuid.UUID(record.question_id),
                difficulty=record.difficulty,
                seconds=record.seconds,
                served_at=served_at,
                deadline_at=served_at + _delta_ms(window_ms),
                closed_at=closed_at,
                solution={
                    "v": SOLUTION_VERSION,
                    "correct_index": record.correct_index,
                },
            )
        )
        attempts.append(
            _attempt(
                item_key=str(record.round_index),
                seat=0,
                served_at=served_at,
                choice=record.a_choice,
                elapsed_ms=a_elapsed,
                correct=record.a_correct,
                points=record.a_points,
                rejected=record.a_rejected.value if record.a_rejected else None,
            )
        )
        attempts.append(
            _attempt(
                item_key=str(record.round_index),
                seat=1,
                served_at=served_at,
                choice=record.b_choice,
                elapsed_ms=b_elapsed,
                correct=record.b_correct,
                points=record.b_points,
                rejected=record.b_rejected.value if record.b_rejected else None,
            )
        )
        cursor = closed_at

    return items, attempts


def _attempt(
    *,
    item_key: str,
    seat: int,
    served_at: datetime,
    choice: int | None,
    elapsed_ms: int,
    correct: bool,
    points: int,
    rejected: str | None,
) -> sessions.AttemptRecord:
    return sessions.AttemptRecord(
        item_key=item_key,
        attempt_seq=0,
        seat=seat,
        submitted_at=served_at + _delta_ms(elapsed_ms),
        submission={} if choice is None else {"type": "choice", "index": choice},
        correct=correct,
        elapsed_ms=elapsed_ms,
        points=points,
        rejected=rejected,
    )


def _delta_ms(ms: int) -> timedelta:
    return timedelta(milliseconds=ms)


def _system_now_ms() -> int:
    return int(time.time() * 1000)
