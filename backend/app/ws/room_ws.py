"""El WebSocket de una sala: traduce §10.1 a llamadas del `RoomStore`.

Es el controlador del canal en vivo. Analogía Java: un `@ServerEndpoint`, que
vive mientras dura la conexión y no por pedido. Acá no hay lógica de juego: el
estado lo decide `runtime/room.py` y lo ejecuta `room_manager.py`; este módulo
lee el socket, llama, y empuja lo que el store dejó en el `outbox`.

Tres cosas que sorprenden a primera vista:

- El token llega por `?token=`: el navegador no deja mandar headers en
  `new WebSocket`, así que el `Authorization` de HTTP no sirve acá.
- El socket lo escribe una sola corrutina en régimen: la que drena el `outbox`.
  El lector, cuando responde por su cuenta (`pong`, un error), pasa por el mismo
  lock: dos `send` en paralelo sobre el mismo socket no son seguros.
- Un corte de red silencioso no genera `disconnect`: lo detecta el timeout de
  inactividad, y recién ahí el `RoomStore` abre la ventana de gracia.
"""

import asyncio
import contextlib
import json
import logging
from typing import Annotated, Any, TypeGuard

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketDisconnected

from app.api.deps import SessionDep, authenticate
from app.api.errors import ApiError
from app.config import settings
from app.game import protocols
from app.game.match_engine import MatchConfig
from app.models import Room, User
from app.runtime.room_manager import Outbox, RoomStore, room_store
from app.services.rooms import get_by_code

logger = logging.getLogger(__name__)

router = APIRouter()

# Rechazo de entrada (token, sala, sala llena): el cliente no debe reintentar igual.
_CLOSE_POLICY = 1008


def get_room_store() -> RoomStore:
    """El store del proceso, inyectado.

    Los tests ponen uno con reloj falso y su propia sesión; en producción es el
    global del proceso, el mismo que apaga el lifespan.
    """
    return room_store


StoreDep = Annotated[RoomStore, Depends(get_room_store)]


@router.websocket("/ws/room/{code}")
async def room_socket(
    websocket: WebSocket, code: str, session: SessionDep, store: StoreDep
) -> None:
    # Se acepta antes de autenticar: si no, un token malo no tiene por dónde
    # recibir el `error` con el que el cliente vuelve al inicio (§12).
    await websocket.accept()
    try:
        usuario = await _identify(websocket, session)
        sala = await _load_room(session, code)
    except ApiError as exc:
        await _send(websocket, protocols.Error(code=exc.code, message=exc.message))
        await websocket.close(code=_CLOSE_POLICY)
        return

    codigo = sala.code
    user_id = str(usuario.id)
    await store.open(
        code=codigo,
        room_id=str(sala.id),
        config=MatchConfig(**sala.config),
        host_id=str(sala.host_user_id),
    )

    outbox: Outbox = asyncio.Queue()
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


async def _identify(websocket: WebSocket, session: AsyncSession) -> User:
    token = websocket.query_params.get("token")
    if not token:
        raise ApiError(401, "AUTH_REQUIRED", "Se necesita un token válido.")
    return await authenticate(session, token)


async def _load_room(session: AsyncSession, code: str) -> Room:
    sala = await get_by_code(session, code)
    if sala is None:
        raise ApiError(404, "ROOM_NOT_FOUND", "No hay una sala con ese código.")
    return sala


async def _reader(
    websocket: WebSocket,
    lock: asyncio.Lock,
    store: RoomStore,
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
    store: RoomStore,
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


async def _writer(websocket: WebSocket, lock: asyncio.Lock, outbox: Outbox) -> None:
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


async def _flush(websocket: WebSocket, outbox: Outbox) -> None:
    while not outbox.empty():
        await _send(websocket, outbox.get_nowait())


def _is_gone(error: BaseException) -> bool:
    """Un corte esperado: el cliente se fue, no un error del handler."""
    return isinstance(error, (WebSocketDisconnect, WebSocketDisconnected))


async def _close(websocket: WebSocket) -> None:
    """Cierra el socket si sigue abierto; si el cliente se fue, no hay más que hacer."""
    with contextlib.suppress(WebSocketDisconnect, WebSocketDisconnected):
        await websocket.close()
