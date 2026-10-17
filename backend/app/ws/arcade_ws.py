"""El WebSocket del arcade: traduce §10.2 a una corrida por conexión.

Es el controlador del canal en vivo. Analogía Java: un `@ServerEndpoint`, que
vive mientras dura la conexión y no por pedido. La partida la decide
`runtime/arcade_session.py`; acá viven el socket, el reloj, la selección de
preguntas y la entrega.

Tres cosas que sorprenden a primera vista:

- El token llega por `?token=`: el navegador no deja mandar headers en
  `new WebSocket`, así que el `Authorization` de HTTP no sirve acá.
- El socket lo escribe **una sola corrutina** en régimen: la que drena el
  `outbox`. Hasta el `pong` y los errores pasan por la cola, con su `id` de
  correlación; el lector nunca toca el socket y no hace falta lock de escritura.
- La corrida es de una conexión, no de una sala: no hay store global. Si el
  socket se cae, la corrida se pierde y la fila queda `playing` para que el
  barrendero la invalide: media corrida no compite en el ranking.
"""

import asyncio
import contextlib
import json
import logging
import time
import uuid
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, replace
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
from app.game.arcade_engine import RoundRecord, difficulty_for
from app.game.constants import CATEGORIES, DIFFICULTY_MAX, DIFFICULTY_MIN
from app.models import User
from app.redis import redis_client
from app.runtime import arcade_session
from app.runtime.arcade_session import ArcadeState
from app.runtime.room_manager import OUTBOX_MAX
from app.services import arcade_runs, leaderboard
from app.services.question_bank import (
    LoadedQuestion,
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

Clock = Callable[[], int]
Sleeper = Callable[[float], Coroutine[object, object, None]]
# El `id` viaja con el mensaje: el escritor es el único que toca el socket y el
# `pong` tiene que poder correlacionar sin un lock de escritura.
Envelope = tuple[protocols.Message, str | None]
Outbox = asyncio.Queue[Envelope]


@dataclass(frozen=True)
class ArcadeRuntime:
    """Lo que el handler no puede inventar: el reloj, el `sleep` y el azar."""

    now_ms: Clock
    sleep: Sleeper
    rng: Random


def get_arcade_runtime() -> ArcadeRuntime:
    return ArcadeRuntime(now_ms=_system_now_ms, sleep=asyncio.sleep, rng=Random())


def get_arcade_redis() -> Redis:
    return redis_client


RuntimeDep = Annotated[ArcadeRuntime, Depends(get_arcade_runtime)]
RedisDep = Annotated[Redis, Depends(get_arcade_redis)]


@router.websocket("/ws/arcade")
async def arcade_socket(
    websocket: WebSocket,
    session: SessionDep,
    runtime: RuntimeDep,
    redis: RedisDep,
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

    outbox: Outbox = asyncio.Queue(maxsize=OUTBOX_MAX)
    run = _Run(
        db=session,
        redis=redis,
        runtime=runtime,
        user_id=usuario.id,
        outbox=outbox,
    )
    reader = asyncio.create_task(
        _reader(
            websocket,
            outbox,
            run,
            idle_s=settings.ws_idle_timeout_seconds,
        )
    )
    writer = asyncio.create_task(_writer(websocket, outbox))
    timer = asyncio.create_task(run.timer())
    try:
        done, _ = await asyncio.wait(
            {reader, writer, timer}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in done:
            error = task.exception()
            if error is not None and not _is_gone(error):
                # El canal se rompió: se cierra igual y el rastro queda en el log.
                logger.error(
                    "el canal del arcade de %s se cortó", usuario.id, exc_info=error
                )
    finally:
        for task in (reader, writer, timer):
            task.cancel()
        await asyncio.gather(reader, writer, timer, return_exceptions=True)
        await _close(websocket)


class _Run:
    """Una corrida viva: el estado puro más el lock, el reloj y la entrega."""

    def __init__(
        self,
        *,
        db: AsyncSession,
        redis: Redis,
        runtime: ArcadeRuntime,
        user_id: uuid.UUID,
        outbox: Outbox,
    ) -> None:
        self._db = db
        self._redis = redis
        self._runtime = runtime
        self._user_id = user_id
        self._outbox = outbox
        self.state: ArcadeState | None = None
        # El motor devuelve una `RoundRecord` por ronda y no la guarda: acá se
        # acumulan hasta el cierre, que es cuando se escriben todas juntas.
        self._records: list[RoundRecord] = []
        self._lock = asyncio.Lock()
        # Despierta al reloj cuando cambió la ronda: contesta una pregunta o se
        # sirve la siguiente. Evita polling y recalcula el plazo con el estado quieto.
        self._wakeup = asyncio.Event()

    @property
    def user_id(self) -> uuid.UUID:
        return self._user_id

    async def start(self) -> None:
        async with self._lock:
            if self.state is not None:
                self._error("ALREADY_STARTED", "La corrida ya arrancó.")
                return
            run_id = uuid.uuid4()
            try:
                # La fila se escribe antes de servir la primera pregunta: si el
                # proceso muere después, queda `playing` y el barrendero la cierra.
                await arcade_runs.start_run(
                    self._db, run_id=run_id, user_id=self._user_id
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
            step = arcade_session.start(str(run_id))
            self.state = step.state
            self._deliver(step.effects)
            await self._serve_next()
            self._wakeup.set()

    async def answer(self, *, round_index: int, choice: int) -> None:
        async with self._lock:
            if self.state is None:
                self._error("NOT_PLAYING", "Primero hay que arrancar la corrida.")
                return
            step = arcade_session.answer(
                self.state,
                round_index=round_index,
                choice=choice,
                now_ms=self._runtime.now_ms(),
            )
            await self._apply(step)
            if step.state.needs_next_question:
                await self._serve_next()
            self._wakeup.set()

    async def timer(self) -> None:
        """Vence la ronda servida; el `sleep` es inyectable para los tests."""
        while True:
            self._wakeup.clear()
            deadline = _deadline(self.state)
            if deadline is None:
                await self._wakeup.wait()
                continue
            if not await self._wait(deadline):
                continue
            async with self._lock:
                state = self.state
                # Bajo el lock el estado pudo moverse: otra acción pudo resolver
                # la ronda o servirse una nueva.
                if state is None or state.round is None:
                    continue
                if state.round.served.ends_at_ms != deadline:
                    continue
                if self._runtime.now_ms() < deadline:
                    continue
                step = arcade_session.expire(state, now_ms=self._runtime.now_ms())
                await self._apply(step)
                if step.state.needs_next_question:
                    await self._serve_next()
                self._wakeup.set()

    async def _apply(self, step: arcade_session.Transition) -> None:
        """Aplica la transición, acumula su ronda y entrega lo que produjo.

        El cierre va **antes** de entregar el `arcade_end`: el ranking se calcula
        sobre la fila ya cerrada y el cliente ve su posición real.
        """
        self.state = step.state
        resumen: leaderboard.RunSummary | None = None
        if step.record is not None:
            self._records.append(step.record)
            if step.state.finished:
                resumen = await self._finish()
        self._deliver(_ranked(step.effects, resumen))

    async def _finish(self) -> leaderboard.RunSummary | None:
        """Cierra la fila y sus rondas. Si falla, el jugador igual ve su final."""
        state = self.state
        assert state is not None
        run_id = uuid.UUID(state.run_id)
        try:
            await arcade_runs.finish_run(
                self._db,
                run_id=run_id,
                run=state.run,
                records=tuple(self._records),
            )
        except Exception:
            # La fila queda `playing` y el barrendero la invalida. El jugador no
            # se queda sin resultado por un problema de persistencia.
            logger.exception("la corrida %s no se pudo cerrar", state.run_id)
            await self._db.rollback()
            return None
        try:
            return await leaderboard.run_summary(
                self._db,
                user_id=self._user_id,
                run_id=run_id,
                score=state.run.score,
            )
        except Exception:
            # La corrida ya está guardada: lo único que se pierde es la posición
            # en este mensaje. El ranking la va a mostrar en la próxima consulta.
            logger.exception("el ranking de la corrida %s falló", state.run_id)
            await self._db.rollback()
            return None

    async def _serve_next(self) -> None:
        state = self.state
        if state is None or not state.needs_next_question:
            return
        question, repeated = await self._pick(state)
        if question is None:
            self._error("NO_QUESTIONS", "No hay preguntas para servir.")
            return
        if repeated:
            logger.warning(
                "el arcade de %s se quedó sin preguntas nuevas: repite", self._user_id
            )
        step = arcade_session.serve(
            state,
            question=question,
            now_ms=self._runtime.now_ms(),
            rng=self._runtime.rng,
            allow_repeat=repeated,
        )
        self.state = step.state
        # Se anota la vista antes de mandar la pregunta: si el cliente la recibe,
        # el historial ya está escrito (y si Redis falla, `remember_seen` degrada).
        await remember_seen(self._redis, self._user_id, question.question.id)
        self._deliver(step.effects)

    async def _pick(self, state: ArcadeState) -> tuple[LoadedQuestion | None, bool]:
        """Elige y carga la pregunta. La base y Redis son de afuera."""
        target = difficulty_for(state.run.correct_count)
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
            return None, False

        viewed = await seen_ids(self._redis, self._user_id)
        excluded = state.seen | viewed
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
        return (
            await load(self._db, selection.question_id),
            selection.strategy is SelectionStrategy.REPEAT,
        )

    def _deliver(self, effects: tuple[protocols.Message, ...]) -> None:
        for message in effects:
            _push(self._outbox, (message, None))

    def _error(self, code: str, message: str) -> None:
        _push(self._outbox, (protocols.Error(code=code, message=message), None))

    async def _wait(self, deadline: int) -> bool:
        """`True` si venció el plazo; `False` si la corrida se despertó antes."""
        timeout_s = (deadline - self._runtime.now_ms()) / 1000
        if timeout_s <= 0:
            return True
        reloj = asyncio.create_task(self._runtime.sleep(timeout_s))
        despertar = asyncio.create_task(self._wakeup.wait())
        try:
            hechos, _ = await asyncio.wait(
                {reloj, despertar}, return_when=asyncio.FIRST_COMPLETED
            )
        finally:
            reloj.cancel()
            despertar.cancel()
            await asyncio.gather(reloj, despertar, return_exceptions=True)
        return reloj in hechos and despertar not in hechos


async def _identify(websocket: WebSocket, session: AsyncSession) -> User:
    token = websocket.query_params.get("token")
    if not token:
        raise ApiError(401, "AUTH_REQUIRED", "Se necesita un token válido.")
    return await authenticate(session, token)


async def _reader(
    websocket: WebSocket,
    outbox: Outbox,
    run: _Run,
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
            logger.info("el arcade de %s cortó por inactividad", run.user_id)
            return

        pedido = _parse(raw)
        if pedido is None:
            _push(
                outbox,
                (
                    protocols.Error(
                        code="BAD_MESSAGE",
                        message="El mensaje no tiene la forma esperada.",
                    ),
                    None,
                ),
            )
            continue
        tipo, datos, correlacion = pedido
        if tipo == "ping":
            _push(outbox, (protocols.Pong(), correlacion))
        elif tipo == "start":
            await run.start()
        elif tipo == "answer":
            respuesta = _answer(datos)
            if respuesta is None:
                _push(
                    outbox,
                    (
                        protocols.Error(
                            code="BAD_MESSAGE", message="Respuesta mal formada."
                        ),
                        correlacion,
                    ),
                )
                continue
            ronda, eleccion = respuesta
            await run.answer(round_index=ronda, choice=eleccion)
        else:
            _push(
                outbox,
                (
                    protocols.Error(
                        code="UNKNOWN_MESSAGE",
                        message=f"Tipo de mensaje desconocido: {tipo}",
                    ),
                    correlacion,
                ),
            )


async def _writer(websocket: WebSocket, outbox: Outbox) -> None:
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


def _deadline(state: ArcadeState | None) -> int | None:
    if state is None or state.round is None:
        return None
    return state.round.served.ends_at_ms


def _ranked(
    effects: tuple[protocols.Message, ...], resumen: leaderboard.RunSummary | None
) -> tuple[protocols.Message, ...]:
    """Completa el `arcade_end` con la posición y la mejor marca.

    Sin resumen (la base no contestó), el final sale con los campos en `None`:
    el jugador ve su puntaje igual, que es lo que vino a buscar.
    """
    if resumen is None:
        return effects
    return tuple(
        replace(
            message,
            rank_global=resumen.rank_global,
            rank_weekly=resumen.rank_weekly,
            personal_best=resumen.personal_best,
            is_new_best=resumen.is_new_best,
        )
        if isinstance(message, protocols.ArcadeEnd)
        else message
        for message in effects
    )


def _push(outbox: Outbox, envelope: Envelope) -> None:
    try:
        outbox.put_nowait(envelope)
    except asyncio.QueueFull:
        # El cliente dejó de leer (TCP sin drenar). Se descarta el mensaje más
        # viejo y queda el más nuevo; la conexión la corta el timeout de inactividad.
        outbox.get_nowait()
        outbox.put_nowait(envelope)
        logger.warning("el outbox del arcade se llenó: se descartó un mensaje")


def _is_gone(error: BaseException) -> bool:
    """Un corte esperado: el cliente se fue, no un error del handler."""
    return isinstance(error, (WebSocketDisconnect, WebSocketDisconnected))


async def _close(websocket: WebSocket) -> None:
    """Cierra el socket si sigue abierto; si el cliente se fue, no hay más que hacer."""
    with contextlib.suppress(WebSocketDisconnect, WebSocketDisconnected):
        await websocket.close()


def _system_now_ms() -> int:
    return int(time.time() * 1000)
