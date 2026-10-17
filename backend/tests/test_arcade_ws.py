"""El WebSocket del arcade, de punta a punta.

Los clientes corren la app en el mismo event loop del test (`ws_client.py`), así
el handler comparte la sesión y el reloj falso: una corrida entera, con
vencimientos, corre en milisegundos y sin tocar `trivia_test`.
"""

import asyncio
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from random import Random
from typing import Any

import pytest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import settings
from app.main import app
from app.models import Question, User
from app.security.tokens import create_guest_token
from app.ws.arcade_ws import (
    ArcadeRuntime,
    get_arcade_redis,
    get_arcade_runtime,
)

from .clock import FakeClock
from .factories import question, user
from .ws_client import WebSocketClient, WebSocketClosed


@dataclass(frozen=True)
class Api:
    session: AsyncSession
    redis: Redis
    user: User
    clock: FakeClock
    runtime: ArcadeRuntime


@pytest.fixture
async def api(session: AsyncSession, redis: Redis) -> AsyncIterator[Api]:
    usuario = user(nick="ana")
    session.add(usuario)
    await session.flush()

    clock = FakeClock()
    runtime = ArcadeRuntime(now_ms=clock.now_ms, sleep=clock.sleep, rng=Random(7))

    async def _sesion() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = _sesion
    app.dependency_overrides[get_arcade_runtime] = lambda: runtime
    app.dependency_overrides[get_arcade_redis] = lambda: redis
    try:
        yield Api(
            session=session, redis=redis, user=usuario, clock=clock, runtime=runtime
        )
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def connect(api: Api) -> Callable[[User], WebSocketClient]:
    def _connect(usuario: User) -> WebSocketClient:
        token = create_guest_token(usuario.id, usuario.nick)
        return WebSocketClient(app, "/ws/arcade", query=f"token={token}")

    return _connect


async def sembrar(
    session: AsyncSession, *, dificultades: tuple[int, ...] = (1,), cuantas: int = 3
) -> list[Question]:
    """Preguntas con una respuesta correcta reconocible después del barajado."""
    filas = [
        question(
            category="geography",
            difficulty=dificultad,
            status="published",
            prompt=f"pregunta {dificultad}-{indice}",
            options=["correcta", "a", "b", "c"],
            correct_index=0,
        )
        for dificultad in dificultades
        for indice in range(cuantas)
    ]
    session.add_all(filas)
    await session.flush()
    return filas


def correcta(mensaje: dict[str, Any]) -> int:
    opciones: list[str] = mensaje["d"]["options"]
    return opciones.index("correcta")


def _seen_key(usuario: User) -> str:
    return f"arcade:seen:{usuario.id}"


async def test_start_sends_the_run_and_the_first_question(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    await sembrar(api.session)
    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        inicio = await socket.until("arcade_start")

        assert inicio["d"]["lives"] == 3
        assert inicio["d"]["seconds"] == 20
        uuid.UUID(inicio["d"]["run_id"])

        pregunta = await socket.until("arcade_question")
        assert pregunta["d"]["round"] == 0
        assert pregunta["d"]["ends_at"] == api.clock.now_ms() + 20_000
        assert pregunta["d"]["score"] == 0
        assert pregunta["d"]["lives"] == 3
        assert pregunta["d"]["streak"] == 0
        assert pregunta["d"]["correct_count"] == 0
        # La respuesta no viaja con la pregunta.
        assert "correct_index" not in pregunta["d"]


async def test_a_correct_answer_scores_and_serves_the_next_question(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    await sembrar(api.session)
    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        await socket.until("arcade_start")
        primera = await socket.until("arcade_question")

        await socket.send(
            {"t": "answer", "d": {"round": 0, "choice": correcta(primera)}}
        )
        resultado = await socket.until("arcade_result")

        assert resultado["d"]["you"]["correct"] is True
        assert resultado["d"]["you"]["ms"] == 0
        assert resultado["d"]["you"]["points"] == 150
        assert resultado["d"]["score"] == 150
        assert resultado["d"]["lives"] == 3
        assert resultado["d"]["streak"] == 1
        assert resultado["d"]["correct_count"] == 1

        siguiente = await socket.until("arcade_question")
        assert siguiente["d"]["round"] == 1
        assert siguiente["d"]["score"] == 150
        assert siguiente["d"]["streak"] == 1
        assert siguiente["d"]["correct_count"] == 1


async def test_a_wrong_answer_loses_a_life(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    await sembrar(api.session)
    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        await socket.until("arcade_start")
        primera = await socket.until("arcade_question")
        incorrecta = (correcta(primera) + 1) % 4

        await socket.send({"t": "answer", "d": {"round": 0, "choice": incorrecta}})
        resultado = await socket.until("arcade_result")

        assert resultado["d"]["you"]["correct"] is False
        assert resultado["d"]["you"]["choice"] == incorrecta
        assert resultado["d"]["you"]["points"] == 0
        assert resultado["d"]["score"] == 0
        assert resultado["d"]["lives"] == 2
        assert resultado["d"]["streak"] == 0

        siguiente = await socket.until("arcade_question")
        assert siguiente["d"]["lives"] == 2
        assert siguiente["d"]["round"] == 1


async def test_ping_malformed_and_unknown_messages(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    async with connect(api.user) as socket:
        await socket.send({"t": "ping", "id": "latido-1"})
        pong = await socket.receive()
        assert pong["t"] == "pong"
        assert pong["id"] == "latido-1"

        await socket.send_raw("no soy json")
        assert (await socket.receive())["d"]["code"] == "BAD_MESSAGE"

        await socket.send({"t": "answer", "d": {"round": "uno", "choice": 1}})
        assert (await socket.receive())["d"]["code"] == "BAD_MESSAGE"

        await socket.send({"t": "volar"})
        assert (await socket.receive())["d"]["code"] == "UNKNOWN_MESSAGE"

        # El canal siguió vivo.
        await socket.send({"t": "ping"})
        assert (await socket.receive())["t"] == "pong"


async def test_answering_before_start_is_rejected(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    async with connect(api.user) as socket:
        await socket.send({"t": "answer", "d": {"round": 0, "choice": 0}})
        error = await socket.receive()
        assert error["d"]["code"] == "NOT_PLAYING"


async def test_start_is_only_once_per_connection(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    await sembrar(api.session)
    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        await socket.until("arcade_start")
        await socket.until("arcade_question")

        await socket.send({"t": "start"})
        assert (await socket.until("error"))["d"]["code"] == "ALREADY_STARTED"


async def test_without_questions_the_run_warns_and_waits(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        assert (await socket.until("arcade_start"))["t"] == "arcade_start"
        assert (await socket.until("error"))["d"]["code"] == "NO_QUESTIONS"


async def test_without_a_token_the_socket_is_rejected() -> None:
    async with WebSocketClient(app, "/ws/arcade") as socket:
        assert (await socket.receive())["d"]["code"] == "AUTH_REQUIRED"
        with pytest.raises(WebSocketClosed) as cierre:
            await socket.receive()
        assert cierre.value.code == 1008


async def test_the_websocket_is_limited_per_ip(
    api: Api,
    connect: Callable[[User], WebSocketClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "rate_limit_arcade_per_minute", 1)

    async with connect(api.user), connect(api.user) as segunda:
        error = await segunda.receive()
        assert error["d"]["code"] == "RATE_LIMITED"


async def test_a_mute_socket_is_cut_by_inactivity(
    api: Api,
    connect: Callable[[User], WebSocketClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ws_idle_timeout_seconds", 2)
    await sembrar(api.session)

    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        await socket.until("arcade_start")
        await socket.until("arcade_question")

        async def drenar() -> None:
            while True:
                await socket.receive()

        with pytest.raises(WebSocketClosed) as cierre:
            await asyncio.wait_for(drenar(), timeout=10)
        assert cierre.value.code == 1000


async def test_a_question_that_expires_loses_a_life_and_serves_the_next(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    await sembrar(api.session)
    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        await socket.until("arcade_start")
        primera = await socket.until("arcade_question")

        api.clock.advance(primera["d"]["ends_at"] - api.clock.now_ms())

        resultado = await asyncio.wait_for(socket.until("arcade_result"), timeout=10)
        assert resultado["d"]["you"]["choice"] is None
        assert resultado["d"]["you"]["ms"] == 20_000
        assert resultado["d"]["lives"] == 2

        siguiente = await socket.until("arcade_question")
        assert siguiente["d"]["round"] == 1
        assert siguiente["d"]["lives"] == 2


async def test_three_misses_end_the_run_and_close_the_circuit(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    await sembrar(api.session)
    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        inicio = await socket.until("arcade_start")

        for _ in range(3):
            pregunta = await socket.until("arcade_question")
            api.clock.advance(pregunta["d"]["ends_at"] - api.clock.now_ms())
            resultado = await socket.until("arcade_result")
            assert resultado["d"]["you"]["choice"] is None

        fin = await socket.until("arcade_end")
        assert fin["d"] == {
            "run_id": inicio["d"]["run_id"],
            "score": 0,
            "correct_count": 0,
            "max_difficulty": 1,
            "longest_streak": 0,
            "rank_global": None,
            "rank_weekly": None,
            "personal_best": None,
            "is_new_best": False,
        }

        await socket.send({"t": "answer", "d": {"round": 3, "choice": 0}})
        assert (await socket.receive())["d"]["code"] == "NOT_PLAYING"

        await socket.send({"t": "start"})
        assert (await socket.until("error"))["d"]["code"] == "ALREADY_STARTED"


async def test_the_served_question_is_written_to_the_seen_history(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    filas = await sembrar(api.session, cuantas=1)

    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        await socket.until("arcade_start")
        await socket.until("arcade_question")

        vistos = await api.redis.zrange(_seen_key(api.user), 0, -1)
        assert vistos == [str(filas[0].id)]


async def test_a_question_seen_before_is_not_served_again(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    filas = await sembrar(api.session, cuantas=2)
    await api.redis.zadd(_seen_key(api.user), {str(filas[0].id): 1.0})

    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        await socket.until("arcade_start")
        pregunta = await socket.until("arcade_question")

        assert pregunta["d"]["prompt"] == filas[1].prompt


async def test_the_run_repeats_only_when_the_pool_is_exhausted(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    await sembrar(api.session, cuantas=1)

    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        await socket.until("arcade_start")
        primera = await socket.until("arcade_question")

        await socket.send(
            {"t": "answer", "d": {"round": 0, "choice": correcta(primera)}}
        )
        await socket.until("arcade_result")
        repetida = await socket.until("arcade_question")

        assert repetida["d"]["round"] == 1
        assert repetida["d"]["prompt"] == primera["d"]["prompt"]
