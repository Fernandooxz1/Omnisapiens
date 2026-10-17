"""El WebSocket de la sala: dos clientes simulados hasta el final de la partida.

Los clientes corren la app en el mismo event loop del test (`ws_client.py`), así
el handler comparte la sesión y el reloj falso del `RoomStore`: una partida
entera, con corte y reconexión, corre en milisegundos y sin tocar `trivia_test`.
"""

import asyncio
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import settings
from app.main import app
from app.models import Room, User
from app.security.tokens import create_guest_token
from app.ws.room_ws import get_room_store

from . import test_room_manager
from .factories import user
from .test_room_manager import Harness
from .ws_client import WebSocketClient, WebSocketClosed

# El armado y el reloj falso son del `RoomStore`: un solo dueño, no una copia.
abrir = test_room_manager.abrir
sala_armada = test_room_manager.sala_armada


@dataclass(frozen=True)
class Api:
    harness: Harness
    session: AsyncSession
    host: User
    guest: User
    room: Room


@pytest.fixture
async def api(
    session: AsyncSession, abrir: Callable[..., Harness]
) -> AsyncIterator[Api]:
    harness, ana, beto, fila = await sala_armada(session, abrir)

    async def _sesion() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = _sesion
    app.dependency_overrides[get_room_store] = lambda: harness.store
    try:
        yield Api(harness=harness, session=session, host=ana, guest=beto, room=fila)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def connect(api: Api) -> Callable[..., WebSocketClient]:
    def _connect(quien: User, *, code: str | None = None) -> WebSocketClient:
        token = create_guest_token(quien.id, quien.nick)
        return WebSocketClient(
            app, f"/ws/room/{code or api.room.code}", query=f"token={token}"
        )

    return _connect


async def test_the_two_players_see_each_other_and_the_third_is_rejected(
    api: Api, connect: Callable[..., WebSocketClient]
) -> None:
    async with connect(api.host) as ana:
        estado = await ana.receive()
        assert estado["t"] == "room_state"
        assert estado["d"]["players"] == [
            {"id": str(api.host.id), "nick": api.host.nick}
        ]
        assert estado["d"]["status"] == "waiting"
        assert estado["d"]["match_id"] is None

        async with connect(api.guest) as beto:
            esperados = [str(api.host.id), str(api.guest.id)]
            for socket in (ana, beto):
                estado = await socket.until("room_state")
                assert [
                    jugador["id"] for jugador in estado["d"]["players"]
                ] == esperados
            assert api.harness.store.player_count(api.room.code) == 2

    caro = user(nick="caro")
    api.session.add(caro)
    await api.session.flush()
    async with connect(caro) as intruso:
        error = await intruso.receive()
        assert error["t"] == "error"
        assert error["d"]["code"] == "ROOM_FULL"
        with pytest.raises(WebSocketClosed) as cierre:
            await intruso.receive()
        assert cierre.value.code == 1008


async def test_a_complete_match_between_two_clients(
    api: Api, connect: Callable[..., WebSocketClient]
) -> None:
    async with connect(api.host) as ana, connect(api.guest) as beto:
        await ana.until("room_state")
        await beto.until("room_state")

        await ana.send({"t": "start"})
        assert (await ana.until("match_start"))["d"]["rounds_total"] == 3
        await beto.until("match_start")

        for ronda in range(3):
            await ana.until("round_start")
            await beto.until("round_start")
            await ana.send({"t": "answer", "d": {"round": ronda, "choice": 1}})
            await beto.send({"t": "answer", "d": {"round": ronda, "choice": 0}})
            resultado = await ana.until("round_result")
            assert resultado["d"]["round"] == ronda
            assert resultado["d"]["correct_index"] == 1
            assert resultado["d"]["you"]["correct"] is True
            assert resultado["d"]["opponent"]["correct"] is False
            await beto.until("round_result")

        fin = await ana.until("match_end")
        assert fin["d"]["reason"] == "completed"
        assert fin["d"]["winner"] == "you"
        assert fin["d"]["scores"]["you"] > fin["d"]["scores"]["opponent"]
        assert (await beto.until("match_end"))["d"]["winner"] == "opponent"


async def test_hello_repaints_the_current_round(
    api: Api, connect: Callable[..., WebSocketClient]
) -> None:
    async with connect(api.host) as ana, connect(api.guest) as beto:
        await ana.until("room_state")
        await beto.until("room_state")
        await ana.send({"t": "start"})
        servida = await ana.until("round_start")
        await beto.until("round_start")

        # `hello` es lo que hace el cliente al reconectar: repinta el estado y la
        # ronda en curso, con el `ends_at` original.
        await ana.send({"t": "hello", "id": "h-1"})
        assert (await ana.until("room_state"))["d"]["you"]["nick"] == api.host.nick
        assert (await ana.until("round_start"))["d"]["ends_at"] == servida["d"][
            "ends_at"
        ]


async def test_ping_is_answered_with_the_same_id(
    api: Api, connect: Callable[..., WebSocketClient]
) -> None:
    async with connect(api.host) as ana:
        await ana.until("room_state")
        await ana.send({"t": "ping", "id": "latido-1"})
        assert (await ana.until("pong"))["id"] == "latido-1"


async def test_a_malformed_message_is_rejected_without_cutting_the_channel(
    api: Api, connect: Callable[..., WebSocketClient]
) -> None:
    async with connect(api.host) as ana:
        await ana.until("room_state")

        await ana.send_raw("no soy json")
        assert (await ana.receive())["d"]["code"] == "BAD_MESSAGE"

        await ana.send({"t": "answer", "d": {"round": "uno", "choice": 1}})
        assert (await ana.receive())["d"]["code"] == "BAD_MESSAGE"

        await ana.send({"t": "volar"})
        assert (await ana.receive())["d"]["code"] == "UNKNOWN_MESSAGE"

        # El canal siguió vivo: un ping sigue recibiendo su pong.
        await ana.send({"t": "ping"})
        assert (await ana.receive())["t"] == "pong"


async def test_only_the_host_starts(
    api: Api, connect: Callable[..., WebSocketClient]
) -> None:
    async with connect(api.host) as ana, connect(api.guest) as beto:
        await ana.until("room_state")
        await beto.until("room_state")
        await beto.send({"t": "start"})
        assert (await beto.until("error"))["d"]["code"] == "NOT_HOST"


async def test_without_a_token_the_socket_is_rejected(api: Api) -> None:
    async with WebSocketClient(app, f"/ws/room/{api.room.code}") as socket:
        assert (await socket.receive())["d"]["code"] == "AUTH_REQUIRED"
        with pytest.raises(WebSocketClosed) as cierre:
            await socket.receive()
        assert cierre.value.code == 1008


async def test_an_unknown_room_is_rejected(
    api: Api, connect: Callable[..., WebSocketClient]
) -> None:
    async with connect(api.host, code="ZZZZZZ") as socket:
        error = await socket.receive()
        assert error["d"]["code"] == "ROOM_NOT_FOUND"


async def test_a_disconnect_and_reconnect_inside_the_grace(
    api: Api, connect: Callable[..., WebSocketClient]
) -> None:
    async with connect(api.host) as ana:
        await ana.until("room_state")
        async with connect(api.guest) as beto:
            await ana.until("room_state")
            await ana.send({"t": "start"})
            primera = await ana.until("round_start")
            await beto.until("round_start")
        # Se fue Beto: la ronda se pausa y Ana ve la ventana de gracia.
        assert (await ana.until("reconnect_pending"))["d"]["seconds_left"] == 20

        async with connect(api.guest) as beto:
            await ana.until("opponent_returned")
            await beto.until("room_state")
            reanudada = await beto.until("round_start")
            # El hueco de la pausa corrió el reloj de la ronda, no la regaló:
            # con el reloj falso quieto, el `ends_at` es el mismo.
            assert reanudada["d"]["ends_at"] == primera["d"]["ends_at"]

            await ana.send({"t": "answer", "d": {"round": 0, "choice": 1}})
            await beto.send({"t": "answer", "d": {"round": 0, "choice": 0}})
            assert (await ana.until("round_result"))["d"]["round"] == 0


async def test_a_mute_socket_is_cut_by_inactivity(
    api: Api, connect: Callable[..., WebSocketClient], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "ws_idle_timeout_seconds", 2)
    async with connect(api.host) as ana, connect(api.guest) as beto:
        await ana.until("room_state")
        await beto.until("room_state")

        async def latido() -> None:
            # Ana se mantiene viva con pings; a Beto lo corta el silencio.
            while True:
                await ana.send({"t": "ping"})
                await asyncio.sleep(0.2)

        tarea = asyncio.create_task(latido())
        try:
            # En partida, el que se queda mudo entra en la ventana de gracia.
            await ana.send({"t": "start"})
            await ana.until("round_start")
            await beto.until("round_start")

            aviso = await asyncio.wait_for(ana.until("reconnect_pending"), timeout=10)
            assert aviso["d"]["seconds_left"] == 20
        finally:
            tarea.cancel()
            await asyncio.gather(tarea, return_exceptions=True)
