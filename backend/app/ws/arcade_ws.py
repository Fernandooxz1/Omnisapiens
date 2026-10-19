"""El WebSocket del arcade: el borde de una sesión solo.

Es el controlador del canal en vivo. La partida la decide `runtime/session_store`
(estado, reloj, vencimientos y entrega); acá viven el socket, la elección de la
pregunta, la persistencia y el ranking. El motor de reglas es el mismo que usa
cualquier sesión solo (`game/solo_engine.py`).

Tres cosas que sorprenden a primera vista:

- El token llega por `?token=`: el navegador no deja mandar headers en
  `new WebSocket`, así que el `Authorization` de HTTP no sirve acá.
- El socket lo escribe **una sola corrutina** en régimen: la que drena el
  `outbox`. Hasta el `pong` y los errores pasan por la cola, con su `id` de
  correlación; el lector nunca toca el socket y no hace falta lock de escritura.
- La sesión es de una conexión, no de una sala. Si el socket se cae, el store la
  suelta y la fila queda `playing` para que el barrendero la invalide: media
  corrida no compite en el ranking.
"""

import asyncio
import contextlib
import json
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from random import Random
from typing import Annotated, Any, TypeGuard

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketDisconnected

from app.api.deps import SessionDep, authenticate
from app.api.errors import ApiError
from app.api.rate_limit import arcade_limit
from app.config import settings
from app.game import protocols
from app.game.constants import CATEGORIES, DIFFICULTY_MAX, DIFFICULTY_MIN
from app.game.modes.arcade import ARCADE_RULES
from app.game.solo_engine import RoundRecord, SoloRun
from app.models import User
from app.redis import redis_client
from app.runtime.session_store import (
    OUTBOX_MAX,
    NextQuestion,
    SessionStore,
    SoloState,
    session_store,
)
from app.services import leaderboard, sessions
from app.services.question_bank import (
    candidates,
    load,
    remember_seen,
    seen_ids,
)
from app.services.questions import SelectionStrategy, select

logger = logging.getLogger(__name__)

router = APIRouter()

# Rechazo de entrada (token, rate limit): el cliente no debe reintentar igual.
_CLOSE_POLICY = 1008

# La sesión genérica del arcade: el formato fija sus reglas con `ruleset_version`.
ARCADE_MODE = "trivia_arcade"
CONTENT_KIND = "quiz"
PLAY_FORMAT = "arcade"
RULESET_VERSION = 1
SOLUTION_VERSION = 1

Clock = Callable[[], int]
# El `id` viaja con el mensaje: el escritor es el único que toca el socket y el
# `pong` tiene que poder correlacionar sin un lock de escritura.
Envelope = tuple[protocols.Message, str | None]


@dataclass(frozen=True)
class ArcadeRuntime:
    """Lo que el handler no puede inventar: el reloj y el azar."""

    now_ms: Clock
    rng: Random


def get_arcade_runtime() -> ArcadeRuntime:
    return ArcadeRuntime(now_ms=_system_now_ms, rng=Random())


def get_arcade_redis() -> Redis:
    return redis_client


def get_session_store() -> SessionStore:
    """El estado vivo del proceso; el test lo reemplaza por uno con reloj falso."""
    return session_store


RuntimeDep = Annotated[ArcadeRuntime, Depends(get_arcade_runtime)]
RedisDep = Annotated[Redis, Depends(get_arcade_redis)]
StoreDep = Annotated[SessionStore, Depends(get_session_store)]


class _Outbox:
    """La única cola de la conexión.

    El store escribe mensajes sueltos; el lector adjunta el `id` de correlación
    del `pong` y de los errores. El escritor es el único que toca el socket.
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Envelope] = asyncio.Queue(maxsize=OUTBOX_MAX)

    def put_nowait(self, message: protocols.Message) -> None:
        self.push(message)

    def push(self, message: protocols.Message, correlation: str | None = None) -> None:
        try:
            self._queue.put_nowait((message, correlation))
        except asyncio.QueueFull:
            # El cliente dejó de leer (TCP sin drenar). Se descarta el mensaje
            # más viejo y queda el más nuevo; la conexión la corta el timeout
            # de inactividad.
            self._queue.get_nowait()
            self._queue.put_nowait((message, correlation))
            logger.warning("el outbox del arcade se llenó: se descartó un mensaje")

    def get_nowait(self) -> Envelope:
        return self._queue.get_nowait()

    async def get(self) -> Envelope:
        return await self._queue.get()


@router.websocket("/ws/arcade")
async def arcade_socket(
    websocket: WebSocket,
    session: SessionDep,
    runtime: RuntimeDep,
    redis: RedisDep,
    store: StoreDep,
) -> None:
    # Se acepta antes de autenticar: si no, un token malo no tiene por dónde
    # recibir el `error` con el que el cliente vuelve al inicio (§12).
    await websocket.accept()
    try:
        await arcade_limit(websocket.client.host if websocket.client else None)
        usuario = await _identify(websocket, session)
    except ApiError as exc:
        await websocket.send_json(
            protocols.encode(protocols.Error(code=exc.code, message=exc.message))
        )
        await websocket.close(code=_CLOSE_POLICY)
        return

    outbox = _Outbox()
    connection = _Connection(
        db=session,
        redis=redis,
        runtime=runtime,
        store=store,
        user_id=usuario.id,
        outbox=outbox,
    )
    reader = asyncio.create_task(
        _reader(
            websocket,
            outbox,
            connection,
            idle_s=settings.ws_idle_timeout_seconds,
        )
    )
    writer = asyncio.create_task(_writer(websocket, outbox))
    try:
        done, _ = await asyncio.wait(
            {reader, writer}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in done:
            error = task.exception()
            if error is not None and not _is_gone(error):
                # El canal se rompió: se cierra igual y el rastro queda en el log.
                logger.error(
                    "el canal del arcade de %s se cortó", usuario.id, exc_info=error
                )
    finally:
        for task in (reader, writer):
            task.cancel()
        await asyncio.gather(reader, writer, return_exceptions=True)
        # Si el socket se fue a mitad de la corrida, la fila queda `playing`
        # para el barrendero; pero ya no está viva y no puede quedar en el
        # registro.
        await connection.release()
        await _close(websocket)


class _Connection:
    """Una sesión viva: el borde que elige ítems, persiste y rankea."""

    def __init__(
        self,
        *,
        db: AsyncSession,
        redis: Redis,
        runtime: ArcadeRuntime,
        store: SessionStore,
        user_id: uuid.UUID,
        outbox: _Outbox,
    ) -> None:
        self._db = db
        self._redis = redis
        self._runtime = runtime
        self._store = store
        self._user_id = user_id
        self._outbox = outbox
        self._session_id: str | None = None

    @property
    def user_id(self) -> uuid.UUID:
        return self._user_id

    async def release(self) -> None:
        """El socket se fue: la sesión ya no está viva, aunque su fila siga abierta."""
        if self._session_id is not None:
            await self._store.close(session_id=self._session_id)

    async def start(self) -> None:
        if self._session_id is not None:
            self._error("ALREADY_STARTED", "La corrida ya arrancó.")
            return

        session_id = uuid.uuid4()
        try:
            # La fila se escribe antes de servir la primera pregunta: si el
            # proceso muere después, queda `playing` y el barrendero la cierra.
            await sessions.start_session(
                self._db,
                session_id=session_id,
                mode=ARCADE_MODE,
                content_kind=CONTENT_KIND,
                play_format=PLAY_FORMAT,
                ruleset_version=RULESET_VERSION,
                config={},
                started_at=_datetime(self._runtime.now_ms()),
                owner_user_id=self._user_id,
            )
        except Exception:
            # No se juega sin fila: el cierre no tendría dónde escribir y la
            # corrida desaparecería sin que el jugador se entere.
            logger.exception("la corrida de %s no se pudo registrar", self._user_id)
            await self._db.rollback()
            self._error(
                "RUN_NOT_STARTED",
                "No se pudo registrar la corrida. Probá de nuevo.",
            )
            return

        try:
            opened = await self._store.open(
                session_id=str(session_id),
                owner_id=self._user_id,
                outbox=self._outbox,
                rules=ARCADE_RULES,
                next_item=self._next_item,
                on_finish=self._finish,
            )
        except Exception:
            # La fila quedó `playing`: el barrendero la invalida.
            logger.exception("la corrida %s no se pudo abrir", session_id)
            await self._db.rollback()
            self._error(
                "RUN_NOT_STARTED",
                "No se pudo registrar la corrida. Probá de nuevo.",
            )
            return

        if not opened:
            # El id es nuevo, así que no debería pasar; no se miente con un
            # arranque que no existe.
            self._error("ALREADY_STARTED", "La corrida ya arrancó.")
            return
        self._session_id = str(session_id)

    async def answer(self, *, round_index: int, choice: int) -> None:
        if self._session_id is None:
            self._error("NOT_PLAYING", "Primero hay que arrancar la corrida.")
            return
        await self._store.submit(
            session_id=self._session_id,
            round_index=round_index,
            choice=choice,
        )

    async def _next_item(
        self, run: SoloRun, seen: frozenset[str]
    ) -> NextQuestion | None:
        """Elige y carga la pregunta. La base y Redis son de afuera del store."""
        target = run.rules.difficulty_for(run.correct_count)
        # El pool se recorta al tramo cercano; si no alcanza, se abre a todo el
        # banco antes de aceptar una repetición (H-13 y §9.4).
        pool = await candidates(
            self._db,
            low=max(DIFFICULTY_MIN, target - 1),
            high=min(DIFFICULTY_MAX, target + 1),
        )
        if not pool:
            pool = await candidates(self._db)
        if not pool:
            return None

        viewed = await seen_ids(self._redis, self._user_id)
        excluded = seen | viewed
        selection = select(
            pool,
            category=self._runtime.rng.choice(CATEGORIES),
            difficulty=target,
            rng=self._runtime.rng,
            excluded=excluded,
        )
        if selection.strategy is SelectionStrategy.REPEAT:
            wider = await candidates(self._db)
            if len(wider) > len(pool):
                selection = select(
                    wider,
                    category=self._runtime.rng.choice(CATEGORIES),
                    difficulty=target,
                    rng=self._runtime.rng,
                    excluded=excluded,
                )

        question = await load(self._db, selection.question_id)
        if question is None:
            return None
        repeated = selection.strategy is SelectionStrategy.REPEAT
        if repeated:
            logger.warning(
                "el arcade de %s se quedó sin preguntas nuevas: repite",
                self._user_id,
            )
        # Se anota la vista antes de mandar la pregunta: si el cliente la recibe,
        # el historial ya está escrito (y si Redis falla, `remember_seen` degrada).
        await remember_seen(self._redis, self._user_id, question.question.id)
        return NextQuestion(question, repeated=repeated)

    async def _finish(
        self,
        state: SoloState,
        records: tuple[RoundRecord, ...],
        end: protocols.ArcadeEnd,
    ) -> protocols.ArcadeEnd:
        """Cierra la fila y completa el `arcade_end` con el ranking.

        Si la base falla, el jugador igual ve su final: la fila queda `playing`
        y el barrendero la invalida, sin resultado en el ranking.
        """
        try:
            await sessions.finish_session(
                self._db,
                session_id=uuid.UUID(state.session_id),
                state=sessions.SessionState(
                    ended_at=_datetime(self._runtime.now_ms()),
                    status="finished",
                    score=state.run.score,
                    correct_count=state.run.correct_count,
                    longest_streak=state.run.longest_streak,
                    max_difficulty=state.run.max_difficulty,
                ),
                items=_items(records),
                attempts=_attempts(records),
            )
        except Exception:
            logger.exception("la corrida %s no se pudo cerrar", state.session_id)
            await self._db.rollback()
            return end

        try:
            resumen = await leaderboard.run_summary(
                self._db,
                user_id=self._user_id,
                session_id=uuid.UUID(state.session_id),
                score=state.run.score,
                now=_datetime(self._runtime.now_ms()),
            )
        except Exception:
            # La corrida ya está guardada: lo único que se pierde es la posición
            # en este mensaje. El ranking la va a mostrar en la próxima consulta.
            logger.exception("el ranking de la corrida %s falló", state.session_id)
            await self._db.rollback()
            return end

        return replace(
            end,
            rank_global=resumen.rank_global,
            rank_weekly=resumen.rank_weekly,
            personal_best=resumen.personal_best,
            is_new_best=resumen.is_new_best,
        )

    def _error(self, code: str, message: str) -> None:
        self._outbox.push(protocols.Error(code=code, message=message))


async def _identify(websocket: WebSocket, session: AsyncSession) -> User:
    token = websocket.query_params.get("token")
    if not token:
        raise ApiError(401, "AUTH_REQUIRED", "Se necesita un token válido.")
    return await authenticate(session, token)


async def _reader(
    websocket: WebSocket,
    outbox: _Outbox,
    connection: _Connection,
    *,
    idle_s: float,
) -> None:
    """Lee el socket y traduce. Vuelve cuando el cliente se va o se queda mudo."""
    while True:
        try:
            raw = await asyncio.wait_for(websocket.receive_text(), idle_s)
        except WebSocketDisconnect:
            return
        except TimeoutError:
            logger.info("el arcade de %s cortó por inactividad", connection.user_id)
            return

        pedido = _parse(raw)
        if pedido is None:
            outbox.push(
                protocols.Error(
                    code="BAD_MESSAGE",
                    message="El mensaje no tiene la forma esperada.",
                )
            )
            continue
        tipo, datos, correlacion = pedido
        if tipo == "ping":
            outbox.push(protocols.Pong(), correlacion)
        elif tipo == "start":
            await connection.start()
        elif tipo == "answer":
            respuesta = _answer(datos)
            if respuesta is None:
                outbox.push(
                    protocols.Error(
                        code="BAD_MESSAGE", message="Respuesta mal formada."
                    ),
                    correlacion,
                )
                continue
            ronda, eleccion = respuesta
            await connection.answer(round_index=ronda, choice=eleccion)
        else:
            outbox.push(
                protocols.Error(
                    code="UNKNOWN_MESSAGE",
                    message=f"Tipo de mensaje desconocido: {tipo}",
                ),
                correlacion,
            )


async def _writer(websocket: WebSocket, outbox: _Outbox) -> None:
    """Lo único que escribe al socket: el `outbox` y su `id` de correlación."""
    while True:
        message, correlacion = await outbox.get()
        await websocket.send_json(protocols.encode(message, id=correlacion))


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


def _datetime(ms: int) -> datetime:
    """El instante del servidor, en UTC. La base guarda `timestamptz`."""
    return datetime.fromtimestamp(ms / 1000, tz=UTC)


def _submission(choice: int | None) -> dict[str, object]:
    """La respuesta del quiz; una omisión no inventa una opción."""
    if choice is None:
        return {}
    return {"type": "choice", "index": choice}


def _items(records: tuple[RoundRecord, ...]) -> list[sessions.ItemRecord]:
    return [
        sessions.ItemRecord(
            item_key=str(record.round_index),
            position=record.round_index,
            content_id=uuid.UUID(record.question_id),
            difficulty=record.difficulty,
            seconds=record.seconds,
            served_at=_datetime(record.served_at_ms),
            deadline_at=_datetime(record.served_at_ms + record.seconds * 1000),
            closed_at=_datetime(record.served_at_ms + record.elapsed_ms),
            solution={
                "v": SOLUTION_VERSION,
                "correct_index": record.correct_index,
            },
        )
        for record in records
    ]


def _attempts(records: tuple[RoundRecord, ...]) -> list[sessions.AttemptRecord]:
    return [
        sessions.AttemptRecord(
            item_key=str(record.round_index),
            attempt_seq=0,
            submitted_at=_datetime(record.served_at_ms + record.elapsed_ms),
            submission=_submission(record.choice),
            correct=record.correct,
            elapsed_ms=record.elapsed_ms,
            points=record.points,
            rejected=record.rejected.value if record.rejected is not None else None,
        )
        for record in records
    ]


def _is_gone(error: BaseException) -> bool:
    """Un corte esperado: el cliente se fue, no un error del handler."""
    return isinstance(error, (WebSocketDisconnect, WebSocketDisconnected))


async def _close(websocket: WebSocket) -> None:
    """Cierra el socket si sigue abierto; si el cliente se fue, no hay más que hacer."""
    with contextlib.suppress(WebSocketDisconnect, WebSocketDisconnected):
        await websocket.close()


def _system_now_ms() -> int:
    return int(time.time() * 1000)
