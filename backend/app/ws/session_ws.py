"""El WebSocket de una sesión solo: el protocolo canónico.

La sesión ya existe: la creó `POST /sessions` en `playing` y acá solo se juega.
El motor, el reloj y los vencimientos son los del store; lo que cambia respecto
del arcade viejo es el presentador, que traduce el mismo estado a
`session_start`, `item_start`, `item_result` y `session_end`.

Dos reglas del canal:

- El `payload` de `item_start` sale del `public_schema` del modo: no hay una
  clase de mensaje por modo ni un campo de la solución que se pueda colar.
- La solución recién viaja en `item_result`, cuando el ítem ya se cerró.
"""

import asyncio
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from random import Random
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SessionDep, authenticate
from app.api.errors import ApiError
from app.api.rate_limit import session_limit
from app.config import settings
from app.game import protocols
from app.game.answers import ServedQuestion
from app.game.modes import GameMode, Players
from app.game.modes import get as get_mode
from app.game.solo_engine import RoundRecord, SoloRun
from app.models import GameSession, User
from app.redis import redis_client
from app.runtime.session_store import (
    NextQuestion,
    SessionStore,
    SoloState,
    session_store,
)
from app.services import leaderboard, sessions
from app.services.question_bank import LoadedQuestion
from app.services.solo_records import attempt_records, item_records, submission
from app.ws.common import (
    ConnectionOutbox,
    close_quietly,
    is_gone,
    parse_answer,
    parse_envelope,
    system_now_ms,
    to_datetime,
    write_socket,
)
from app.ws.selection import choose_item

logger = logging.getLogger(__name__)

router = APIRouter()

# Rechazo de entrada (token, sesión ajena, rate limit): no reintentar igual.
_CLOSE_POLICY = 1008

Clock = Callable[[], int]


@dataclass(frozen=True)
class SessionRuntime:
    """Lo que el handler no puede inventar: el reloj y el azar."""

    now_ms: Clock
    rng: Random


def get_session_runtime() -> SessionRuntime:
    return SessionRuntime(now_ms=system_now_ms, rng=Random())


def get_session_redis() -> Redis:
    return redis_client


def get_store() -> SessionStore:
    """El estado vivo del proceso; el test lo reemplaza por uno con reloj falso."""
    return session_store


RuntimeDep = Annotated[SessionRuntime, Depends(get_session_runtime)]
RedisDep = Annotated[Redis, Depends(get_session_redis)]
StoreDep = Annotated[SessionStore, Depends(get_store)]


@router.websocket("/ws/session/{session_id}")
async def session_socket(
    websocket: WebSocket,
    session_id: str,
    session: SessionDep,
    runtime: RuntimeDep,
    redis: RedisDep,
    store: StoreDep,
) -> None:
    # Se acepta antes de autenticar: si no, un token malo no tiene por dónde
    # recibir el `error` con el que el cliente vuelve al inicio.
    await websocket.accept()
    try:
        await session_limit(websocket.client.host if websocket.client else None)
        usuario = await _identify(websocket, session)
        row, mode, config = await _playable(session, session_id, usuario.id)
    except ApiError as exc:
        await _reject(websocket, exc)
        return

    outbox = ConnectionOutbox()
    connection = _Connection(
        db=session,
        redis=redis,
        runtime=runtime,
        store=store,
        user_id=usuario.id,
        started_at=row.started_at,
        mode=mode,
        config=config,
        outbox=outbox,
    )

    try:
        opened = await connection.open(str(row.id))
    except Exception:
        logger.exception("la sesión %s no se pudo abrir", row.id)
        await session.rollback()
        await _reject(
            websocket,
            ApiError(500, "SESSION_NOT_STARTED", "No se pudo abrir la sesión."),
        )
        return
    if not opened:
        await _reject(
            websocket,
            ApiError(409, "ALREADY_STARTED", "La sesión ya está en juego."),
        )
        return

    reader = asyncio.create_task(
        _reader(
            websocket,
            outbox,
            connection,
            idle_s=settings.ws_idle_timeout_seconds,
        )
    )
    writer = asyncio.create_task(write_socket(websocket, outbox))
    try:
        done, _ = await asyncio.wait(
            {reader, writer}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in done:
            error = task.exception()
            if error is not None and not is_gone(error):
                logger.error(
                    "el canal de la sesión %s se cortó",
                    row.id,
                    exc_info=error,
                )
    finally:
        for task in (reader, writer):
            task.cancel()
        await asyncio.gather(reader, writer, return_exceptions=True)
        await connection.release()
        await close_quietly(websocket)


class _Connection:
    """Una sesión viva: el borde que elige ítems, persiste y rankea."""

    def __init__(
        self,
        *,
        db: AsyncSession,
        redis: Redis,
        runtime: SessionRuntime,
        store: SessionStore,
        user_id: uuid.UUID,
        started_at: datetime,
        mode: GameMode,
        config: dict[str, object],
        outbox: ConnectionOutbox,
    ) -> None:
        self._db = db
        self._redis = redis
        self._runtime = runtime
        self._store = store
        self._user_id = user_id
        self._started_at = started_at
        self._mode = mode
        self._config = config
        self._outbox = outbox
        self._presenter = CanonicalPresenter(mode, config)
        self._session_id: str | None = None

    async def open(self, session_id: str) -> bool:
        rules = self._mode.solo_rules
        if rules is None:  # el POST ya lo validó; el guardia cierra el tipo
            raise RuntimeError(f"el modo {self._mode.code!r} no tiene reglas solo")
        self._session_id = session_id
        return await self._store.open(
            session_id=session_id,
            owner_id=self._user_id,
            outbox=self._outbox,
            rules=rules,
            next_item=self._next_item,
            presenter=self._presenter,
            on_finish=self._finish,
        )

    async def release(self) -> None:
        """El socket se fue: la sesión no se retoma, la fila se abandona.

        El canal es de una conexión (`connection=EPHEMERAL`): una corrida a
        medias no compite en el ranking y no se puede reanudar. Si el cierre ya
        la había terminado, `abandon_session` no toca nada.
        """
        if self._session_id is None:
            return
        await self._store.close(session_id=self._session_id)
        ended_at = max(to_datetime(self._runtime.now_ms()), self._started_at)
        try:
            await sessions.abandon_session(
                self._db,
                session_id=uuid.UUID(self._session_id),
                ended_at=ended_at,
            )
        except Exception:
            logger.exception("la sesión %s no se pudo abandonar", self._session_id)
            await self._db.rollback()

    async def answer(self, *, round_index: int, choice: int) -> None:
        if self._session_id is None:
            self._error("NOT_PLAYING", "La sesión no está en juego.")
            return
        await self._store.submit(
            session_id=self._session_id,
            round_index=round_index,
            choice=choice,
        )

    async def send_state(self) -> None:
        if self._session_id is None:
            self._error("NOT_PLAYING", "La sesión no está en juego.")
            return
        view = self._store.sessions().get(self._session_id)
        if view is None:
            self._error("NOT_PLAYING", "La sesión no está en juego.")
            return
        self._outbox.push(self._presenter.state(view.state))

    async def _next_item(
        self, run: SoloRun, seen: frozenset[str]
    ) -> NextQuestion | None:
        return await choose_item(
            self._db,
            self._redis,
            user_id=self._user_id,
            run=run,
            seen=seen,
            rng=self._runtime.rng,
        )

    async def _finish(
        self,
        state: SoloState,
        records: tuple[RoundRecord, ...],
        end: protocols.Message,
    ) -> protocols.Message:
        """Cierra la fila y completa el `session_end` con el ranking."""
        try:
            await sessions.finish_session(
                self._db,
                session_id=uuid.UUID(state.session_id),
                state=sessions.SessionState(
                    ended_at=to_datetime(self._runtime.now_ms()),
                    status="finished",
                    score=state.run.score,
                    correct_count=state.run.correct_count,
                    longest_streak=state.run.longest_streak,
                    max_difficulty=state.run.max_difficulty,
                ),
                items=item_records(records),
                attempts=attempt_records(records),
            )
        except Exception:
            # La fila queda `playing`; el barrendero la invalida. El jugador
            # igual ve su final, sin ranking.
            logger.exception("la sesión %s no se pudo cerrar", state.session_id)
            await self._db.rollback()
            return end

        ranking = await self._ranking(state)
        if not isinstance(end, protocols.SessionEnd):
            # El presentador de este canal siempre cierra con `session_end`.
            return end
        return replace(end, ranking=ranking)

    async def _ranking(self, state: SoloState) -> dict[str, object] | None:
        if self._mode.ranking is None:
            return None
        try:
            resumen = await leaderboard.run_summary(
                self._db,
                user_id=self._user_id,
                session_id=uuid.UUID(state.session_id),
                score=state.run.score,
                mode=self._mode.code,
                now=to_datetime(self._runtime.now_ms()),
            )
        except Exception:
            # La sesión ya está guardada: lo único que se pierde es la posición
            # en este mensaje.
            logger.exception("el ranking de la sesión %s falló", state.session_id)
            await self._db.rollback()
            return None
        return {
            "rank_global": resumen.rank_global,
            "rank_weekly": resumen.rank_weekly,
            "personal_best": resumen.personal_best,
            "is_new_best": resumen.is_new_best,
        }

    def _error(self, code: str, message: str) -> None:
        self._outbox.push(protocols.Error(code=code, message=message))


class CanonicalPresenter:
    """Traduce el estado del motor a los mensajes canónicos del modo."""

    def __init__(self, mode: GameMode, config: dict[str, object]) -> None:
        self._mode = mode
        self._config = config

    def start(self, state: SoloState) -> protocols.Message:
        return protocols.SessionStart(
            session_id=state.session_id,
            mode=self._mode.code,
            config=dict(self._config),
            lives=state.run.lives,
        )

    def item_start(
        self,
        state: SoloState,
        served: ServedQuestion,
        question: LoadedQuestion,
    ) -> protocols.Message:
        return protocols.ItemStart(
            item_key=str(served.round_index),
            position=served.round_index,
            ends_at=served.ends_at_ms,
            total_seconds=served.seconds,
            payload=self.payload(question),
        )

    def item_result(
        self,
        run: SoloRun,
        record: RoundRecord,
        question: LoadedQuestion,
    ) -> protocols.Message:
        solution = dict(question.solution)
        return protocols.ItemResult(
            item_key=str(record.round_index),
            correct=record.correct,
            submission=submission(record.choice) or None,
            solution=solution or None,
            points=record.points,
            scores=self.scores(run),
        )

    def end(self, state: SoloState) -> protocols.Message:
        return protocols.SessionEnd(
            session_id=state.session_id,
            score=state.run.score,
            correct_count=state.run.correct_count,
            max_difficulty=state.run.max_difficulty,
            longest_streak=state.run.longest_streak,
            ranking=None,
        )

    def state(self, state: SoloState) -> protocols.Message:
        round_ = state.round
        payload = None
        ends_at = None
        total_seconds = None
        if round_ is not None:
            payload = self.payload(round_.question)
            ends_at = round_.served.ends_at_ms
            total_seconds = round_.served.seconds
        return protocols.SessionState(
            session_id=state.session_id,
            mode=self._mode.code,
            config=dict(self._config),
            position=state.run.round_index,
            ends_at=ends_at,
            total_seconds=total_seconds,
            payload=payload,
            scores=self.scores(state.run),
            finished=state.finished,
        )

    def is_end(self, message: protocols.Message) -> bool:
        return isinstance(message, protocols.SessionEnd)

    def payload(self, question: LoadedQuestion) -> dict[str, object]:
        """Lo público, validado por el esquema del modo. La solución no entra."""
        return self._mode.public_schema.model_validate(question.public).model_dump()

    @staticmethod
    def scores(run: SoloRun) -> dict[str, int]:
        return {
            "score": run.score,
            "lives": run.lives,
            "streak": run.streak,
            "correct_count": run.correct_count,
        }


async def _playable(
    session: AsyncSession, raw_id: str, user_id: uuid.UUID
) -> tuple[GameSession, GameMode, dict[str, object]]:
    """La fila que este usuario puede jugar, o `ApiError` con el motivo."""
    try:
        session_id = uuid.UUID(raw_id)
    except ValueError:
        raise ApiError(
            404, "NOT_PLAYING", "La sesión no existe o no está en juego."
        ) from None

    row = await session.get(GameSession, session_id)
    if row is None or row.owner_user_id != user_id:
        raise ApiError(404, "NOT_PLAYING", "La sesión no existe o no está en juego.")
    if row.status != "playing":
        raise ApiError(409, "NOT_PLAYING", "La sesión ya terminó.")

    try:
        mode = get_mode(row.mode)
    except KeyError:
        raise ApiError(
            404,
            "MODE_NOT_FOUND",
            f"No hay un modo registrado con el código {row.mode!r}.",
        ) from None
    if mode.players is not Players.SOLO or mode.solo_rules is None:
        raise ApiError(
            422,
            "MODE_NOT_SOLO",
            f"El modo {mode.code!r} no se juega en una sesión solo.",
        )

    try:
        config = mode.config_schema.model_validate(row.config).model_dump()
    except ValidationError as exc:
        detalle = "; ".join(error["msg"] for error in exc.errors())
        raise ApiError(
            422, "INVALID_CONFIG", detalle or "La configuración no es válida."
        ) from None
    return row, mode, config


async def _identify(websocket: WebSocket, session: AsyncSession) -> User:
    token = websocket.query_params.get("token")
    if not token:
        raise ApiError(401, "AUTH_REQUIRED", "Se necesita un token válido.")
    return await authenticate(session, token)


async def _reject(websocket: WebSocket, exc: ApiError) -> None:
    await websocket.send_json(
        protocols.encode(protocols.Error(code=exc.code, message=exc.message))
    )
    await websocket.close(code=_CLOSE_POLICY)


async def _reader(
    websocket: WebSocket,
    outbox: ConnectionOutbox,
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
            logger.info("la sesión cortó por inactividad")
            return

        pedido = parse_envelope(raw)
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
        elif tipo == "state":
            await connection.send_state()
        elif tipo == "answer":
            respuesta = parse_answer(datos)
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


__all__ = ["CanonicalPresenter", "SessionRuntime", "router"]
