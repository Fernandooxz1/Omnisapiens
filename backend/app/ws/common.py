"""Piezas compartidas por los WebSockets de sesión.

El arcade viejo y el canal canónico comparten el transporte: una sola cola por
conexión, un solo escritor y las mismas reglas para leer el sobre. Cambia el
protocolo, no el socket.
"""

import asyncio
import contextlib
import json
import logging
import time
from datetime import UTC, datetime
from typing import Any, TypeGuard

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketDisconnected

from app.game import protocols
from app.runtime.session_store import OUTBOX_MAX

logger = logging.getLogger(__name__)

# El `id` viaja con el mensaje: el escritor es el único que toca el socket y el
# `pong` tiene que poder correlacionar sin un lock de escritura.
Envelope = tuple[protocols.Message, str | None]


class ConnectionOutbox:
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
            logger.warning("el outbox de la sesión se llenó: se descartó un mensaje")

    def get_nowait(self) -> Envelope:
        return self._queue.get_nowait()

    async def get(self) -> Envelope:
        return await self._queue.get()


async def write_socket(websocket: WebSocket, outbox: ConnectionOutbox) -> None:
    """Lo único que escribe al socket: el `outbox` y su `id` de correlación."""
    while True:
        message, correlation = await outbox.get()
        await websocket.send_json(protocols.encode(message, id=correlation))


def parse_envelope(raw: str) -> tuple[str, dict[str, Any], str | None] | None:
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


def parse_answer(datos: dict[str, Any]) -> tuple[int, int] | None:
    """`(ronda, opción)` si los dos son enteros. `bool` es `int`: se descarta."""
    ronda = datos.get("round")
    eleccion = datos.get("choice")
    if not _is_int(ronda) or not _is_int(eleccion):
        return None
    return ronda, eleccion


def _is_int(valor: object) -> TypeGuard[int]:
    return isinstance(valor, int) and not isinstance(valor, bool)


def to_datetime(ms: int) -> datetime:
    """El instante del servidor, en UTC. La base guarda `timestamptz`."""
    return datetime.fromtimestamp(ms / 1000, tz=UTC)


def system_now_ms() -> int:
    return int(time.time() * 1000)


def is_gone(error: BaseException) -> bool:
    """Un corte esperado: el cliente se fue, no un error del handler."""
    return isinstance(error, (WebSocketDisconnect, WebSocketDisconnected))


async def close_quietly(websocket: WebSocket) -> None:
    """Cierra el socket si sigue abierto; si el cliente se fue, no hay más que hacer."""
    with contextlib.suppress(WebSocketDisconnect, WebSocketDisconnected):
        await websocket.close()


__all__ = [
    "ConnectionOutbox",
    "Envelope",
    "close_quietly",
    "is_gone",
    "parse_answer",
    "parse_envelope",
    "system_now_ms",
    "to_datetime",
    "write_socket",
]
