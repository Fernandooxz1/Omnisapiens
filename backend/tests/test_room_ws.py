"""El WebSocket de la sala: dos clientes simulados hasta el final de la partida.

Los clientes corren la app en el mismo event loop del test (`ws_client.py`), así
el handler comparte la sesión, el reloj falso y el `Random` del
`InMemorySessionStore`: una partida entera, con corte y reconexión, corre en
milisegundos y sin tocar `trivia_test`.
"""

import asyncio
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass

import pytest
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import rate_limit
from app.api.deps import get_session
from app.config import settings
from app.main import app
from app.models import (
    GameParticipant,
    GameSession,
    Match,
    MatchRound,
    Room,
    SessionAttempt,
    SessionItem,
    User,
)
from app.security.tokens import create_guest_token
from app.ws.room_ws import (
    get_room_runtime,
    get_room_session_factory,
    get_room_store,
)

from . import room_harness
from .factories import user
from .room_harness import Harness, correr
from .ws_client import WebSocketClient, WebSocketClosed

# El armado y el reloj falso son del store: un solo dueño, no una copia.
abrir = room_harness.abrir
sala_armada = room_harness.sala_armada


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
    app.dependency_overrides[get_room_runtime] = lambda: harness.runtime
    app.dependency_overrides[get_room_session_factory] = lambda: harness.session_factory
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


async def test_an_expired_room_is_rejected(
    api: Api, connect: Callable[..., WebSocketClient], session: AsyncSession
) -> None:
    api.room.status = "expired"
    await session.flush()

    async with connect(api.host) as socket:
        error = await socket.receive()
        assert error["d"]["code"] == "ROOM_NOT_FOUND"


async def test_the_websocket_is_limited_per_ip(
    api: Api,
    connect: Callable[..., WebSocketClient],
    redis: Redis,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rate_limit, "redis_client", redis)
    monkeypatch.setattr(rate_limit.settings, "rate_limit_room_per_minute", 1)

    async with connect(api.host) as primera:
        assert (await primera.receive())["t"] == "room_state"
        async with connect(api.host) as segunda:
            error = await segunda.receive()
            assert error["d"]["code"] == "RATE_LIMITED"


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


async def test_a_complete_match_writes_the_generic_session_history(
    api: Api, connect: Callable[..., WebSocketClient]
) -> None:
    async with connect(api.host) as ana, connect(api.guest) as beto:
        await ana.until("room_state")
        await beto.until("room_state")
        await ana.send({"t": "start"})
        arranque = await ana.until("match_start")
        await beto.until("match_start")

        for ronda in range(3):
            await ana.until("round_start")
            await beto.until("round_start")
            await ana.send({"t": "answer", "d": {"round": ronda, "choice": 1}})
            await beto.send({"t": "answer", "d": {"round": ronda, "choice": 0}})
            await ana.until("round_result")
            await beto.until("round_result")
        await ana.until("match_end")
        await beto.until("match_end")

    match_id = uuid.UUID(arranque["d"]["match_id"])
    partida = await api.session.get(GameSession, match_id)
    assert partida is not None
    assert partida.mode == "trivia_versus"
    assert partida.content_kind == "quiz"
    assert partida.play_format == "versus"
    assert partida.status == "finished"
    assert partida.room_id == api.room.id
    assert partida.owner_user_id is None
    assert partida.config == {"rounds": 3, "seconds": 10}
    assert partida.score > 0
    assert partida.correct_count == 3
    assert partida.longest_streak == 3
    assert partida.ended_at is not None

    sillas = (
        await api.session.scalars(
            select(GameParticipant)
            .where(GameParticipant.session_id == match_id)
            .order_by(GameParticipant.seat)
        )
    ).all()
    assert [(silla.seat, silla.user_id) for silla in sillas] == [
        (0, api.host.id),
        (1, api.guest.id),
    ]
    assert [silla.score for silla in sillas] == [partida.score, 0]
    assert [silla.outcome for silla in sillas] == ["win", "lose"]

    items = (
        await api.session.scalars(
            select(SessionItem)
            .where(SessionItem.session_id == match_id)
            .order_by(SessionItem.position)
        )
    ).all()
    assert [item.item_key for item in items] == ["0", "1", "2"]
    assert all(item.content_id is not None for item in items)
    assert all(item.solution_snapshot["v"] == 1 for item in items)

    intentos = (
        await api.session.scalars(
            select(SessionAttempt)
            .join(SessionItem, SessionAttempt.item_id == SessionItem.id)
            .where(SessionItem.session_id == match_id)
        )
    ).all()
    assert len(intentos) == 6
    assert sum(1 for intento in intentos if intento.correct) == 3

    # La tabla vieja sigue escribiéndose hasta la fase 10.
    vieja = await api.session.get(Match, match_id)
    assert vieja is not None
    assert vieja.status == "finished"
    assert vieja.winner_id == api.host.id
    rondas = (
        await api.session.scalars(
            select(MatchRound).where(MatchRound.match_id == match_id)
        )
    ).all()
    assert len(rondas) == 3


async def test_an_abandoned_match_is_closed_for_both_players(
    api: Api, connect: Callable[..., WebSocketClient]
) -> None:
    async with connect(api.host) as ana:
        await ana.until("room_state")
        async with connect(api.guest) as beto:
            await ana.until("room_state")
            await beto.until("room_state")
            await ana.send({"t": "start"})
            arranque = await ana.until("match_start")
            await beto.until("match_start")
            await ana.until("round_start")
            await beto.until("round_start")

        assert (await ana.until("reconnect_pending"))["d"]["seconds_left"] == 20
        await correr(api.harness, 20_000)
        fin = await ana.until("match_end")
        assert fin["d"]["reason"] == "abandoned"

    match_id = uuid.UUID(arranque["d"]["match_id"])
    partida = await api.session.get(GameSession, match_id)
    assert partida is not None
    assert partida.status == "abandoned"
    assert partida.ended_at is not None
    assert partida.score == 0
    sillas = (
        await api.session.scalars(
            select(GameParticipant).where(GameParticipant.session_id == match_id)
        )
    ).all()
    assert {silla.outcome for silla in sillas} == {"abandoned"}

    vieja = await api.session.get(Match, match_id)
    assert vieja is not None
    assert vieja.status == "abandoned"
    assert vieja.winner_id == api.host.id

    # Al irse uno de una sala terminada, vuelve al lobby en la base.
    sala = await api.session.get(Room, api.room.id)
    assert sala is not None
    assert sala.status == "waiting"
