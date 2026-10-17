"""Cliente WebSocket de test: corre la app en el mismo loop que el test.

`httpx.ASGITransport` habla HTTP por ASGI, pero no WebSocket, y el `TestClient`
de Starlette levanta la app en otro hilo y otro event loop: la sesión de asyncpg
de la fixture no cruza de loop, y el rollback del test no vería lo que escribió
el handler. Acá se maneja el `scope: "websocket"` a mano, igual que
`ASGITransport` hace con el de HTTP, así el handler comparte la sesión del test.

El test ve la app como la vería un navegador: mensajes JSON de ida y vuelta, y
un `WebSocketClosed` con el código cuando el servidor cierra.
"""

import asyncio
import json
from types import TracebackType
from typing import Any, Self

from starlette.types import ASGIApp, Message, Scope


class WebSocketClosed(Exception):
    """El servidor cerró el socket: el test ya no puede mandar ni recibir."""

    def __init__(self, code: int) -> None:
        super().__init__(f"el socket se cerró con {code}")
        self.code = code


class WebSocketClient:
    def __init__(self, app: ASGIApp, path: str, *, query: str = "") -> None:
        self._app = app
        self._path = path
        self._query = query
        self._hacia_la_app: asyncio.Queue[Message] = asyncio.Queue()
        self._desde_la_app: asyncio.Queue[Message] = asyncio.Queue()
        self._tarea: asyncio.Task[None] | None = None
        self.close_code: int | None = None

    async def __aenter__(self) -> Self:
        scope: Scope = {
            "type": "websocket",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "scheme": "ws",
            "path": self._path,
            "raw_path": self._path.encode(),
            "query_string": self._query.encode(),
            "root_path": "",
            "headers": [(b"host", b"test")],
            "client": ("test", 1),
            "server": ("test", 80),
            "subprotocols": [],
            "state": {},
        }
        self._tarea = asyncio.create_task(self._app(scope, self._recibir, self._enviar))
        await self._hacia_la_app.put({"type": "websocket.connect"})
        evento = await self._desde_la_app.get()
        if evento["type"] == "websocket.close":
            self.close_code = evento.get("code", 1000)
            await self._terminar()
            raise WebSocketClosed(self.close_code)
        assert evento["type"] == "websocket.accept", evento
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _tb: TracebackType | None,
    ) -> bool:
        # Si el test ya está fallando, no lo tapo con el error del cierre.
        await self._terminar(propagar=exc_type is None)
        return False

    async def _recibir(self) -> Message:
        return await self._hacia_la_app.get()

    async def _enviar(self, message: Message) -> None:
        await self._desde_la_app.put(message)

    async def send(self, payload: dict[str, Any]) -> None:
        await self._hacia_la_app.put(
            {"type": "websocket.receive", "text": json.dumps(payload)}
        )

    async def send_raw(self, raw: str) -> None:
        """Para probar lo que no es JSON válido; el handler lo tiene que rechazar."""
        await self._hacia_la_app.put({"type": "websocket.receive", "text": raw})

    async def receive(self) -> dict[str, Any]:
        while True:
            evento = await self._desde_la_app.get()
            if evento["type"] == "websocket.send":
                return json.loads(evento["text"])
            if evento["type"] == "websocket.close":
                self.close_code = evento.get("code", 1000)
                await self._terminar()
                raise WebSocketClosed(self.close_code)

    async def until(self, tipo: str) -> dict[str, Any]:
        """El próximo mensaje de ese tipo, salteando los demás que ya llegaron."""
        while True:
            mensaje = await self.receive()
            if mensaje["t"] == tipo:
                return mensaje

    async def wait_closed(self) -> int:
        assert self._tarea is not None
        await self._tarea
        assert self.close_code is not None
        return self.close_code

    async def _terminar(self, *, propagar: bool = True) -> None:
        tarea, self._tarea = self._tarea, None
        if tarea is None:
            return
        if not tarea.done():
            await self._hacia_la_app.put({"type": "websocket.disconnect", "code": 1000})
        try:
            await tarea
        except Exception:
            if propagar:
                raise
