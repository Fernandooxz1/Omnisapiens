"""El WebSocket del arcade, de punta a punta.

Los clientes corren la app en el mismo event loop del test (`ws_client.py`), así
el handler comparte la sesión y el reloj falso: una corrida entera, con
vencimientos, corre en milisegundos y sin tocar `trivia_test`.
"""

import asyncio
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from random import Random
from typing import Any

import pytest
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import settings
from app.main import app
from app.models import ArcadeAnswer, ArcadeRun, Question, User
from app.runtime.live import live_arcade_runs
from app.security.tokens import create_guest_token
from app.services import arcade_runs, leaderboard
from app.ws.arcade_ws import (
    ArcadeRuntime,
    get_arcade_redis,
    get_arcade_runtime,
)

from .clock import FakeClock
from .factories import arcade_run, question, user
from .ws_client import WebSocketClient, WebSocketClosed


@dataclass(frozen=True)
class Api:
    session: AsyncSession
    redis: Redis
    user: User
    clock: FakeClock
    runtime: ArcadeRuntime


@pytest.fixture
async def api(
    session: AsyncSession, redis: Redis, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[Api]:
    usuario = user(nick="ana")
    session.add(usuario)
    await session.flush()

    clock = FakeClock()
    # La pausa de revelación se prueba en sus propios tests: acá no suma tiempo.
    monkeypatch.setattr(settings, "reveal_seconds", 0.0)

    async def despierto() -> None:
        return None

    def dormir(seconds: float) -> Coroutine[object, object, None]:
        # El reloj falso calcula el vencimiento al llamar, no al ejecutar: el
        # wrapper tiene que ser sincrónico para no perder ese registro.
        if settings.reveal_seconds and seconds == settings.reveal_seconds:
            clock.advance(int(seconds * 1000))
            return despierto()
        return clock.sleep(seconds)

    runtime = ArcadeRuntime(now_ms=clock.now_ms, sleep=dormir, rng=Random(7))

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


async def test_the_reveal_pauses_before_the_next_question_and_the_clock_starts_after(
    api: Api,
    connect: Callable[[User], WebSocketClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "reveal_seconds", 2.5)
    await sembrar(api.session)

    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        await socket.until("arcade_start")
        primera = await socket.until("arcade_question")
        contestada_en = api.clock.now_ms()

        await socket.send(
            {"t": "answer", "d": {"round": 0, "choice": correcta(primera)}}
        )
        assert (await socket.until("arcade_result"))["d"]["round"] == 0

        siguiente = await socket.until("arcade_question")
        # La pausa corre antes de servir: el reloj de la próxima arranca 2,5 s después.
        assert api.clock.now_ms() == contestada_en + 2_500
        assert siguiente["d"]["ends_at"] == (
            contestada_en + 2_500 + siguiente["d"]["seconds"] * 1000
        )


async def test_the_end_does_not_take_an_extra_pause(
    api: Api,
    connect: Callable[[User], WebSocketClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "reveal_seconds", 2.5)
    await sembrar(api.session)

    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        await socket.until("arcade_start")
        arranco = api.clock.now_ms()

        for _ in range(3):
            pregunta = await socket.until("arcade_question")
            api.clock.advance(pregunta["d"]["ends_at"] - api.clock.now_ms())
            await socket.until("arcade_result")

        await socket.until("arcade_end")

    # Tres rondas de 20 s y solo dos revelaciones: la última cierra la corrida.
    assert api.clock.now_ms() == arranco + 3 * 20_000 + 2 * 2_500


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
            "rank_global": 1,
            "rank_weekly": 1,
            "personal_best": 0,
            "is_new_best": True,
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


# ------------------------------------------------------------------ persistencia


async def _run_row(api: Api, run_id: str) -> Any:
    """La fila tal como está en Postgres.

    Columnas sueltas y no `session.get`: el objeto que agregó `start_run` sigue en
    el identity map con los contadores sin cargar (los pone el `server_default`).
    """
    return (
        await api.session.execute(
            select(
                ArcadeRun.status,
                ArcadeRun.user_id,
                ArcadeRun.score,
                ArcadeRun.correct_count,
                ArcadeRun.longest_streak,
                ArcadeRun.max_difficulty,
                ArcadeRun.ended_at,
            ).where(ArcadeRun.id == uuid.UUID(run_id))
        )
    ).one()


async def test_start_writes_the_run_playing(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    await sembrar(api.session)

    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        inicio = await socket.until("arcade_start")

    fila = await _run_row(api, inicio["d"]["run_id"])
    assert fila.status == "playing"
    assert fila.user_id == api.user.id
    assert (fila.score, fila.correct_count, fila.longest_streak) == (0, 0, 0)
    assert fila.max_difficulty == 1
    assert fila.ended_at is None


async def test_a_finished_run_closes_with_all_its_rounds(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    preguntas = await sembrar(api.session)

    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        inicio = await socket.until("arcade_start")

        for _ in range(2):
            ronda = await socket.until("arcade_question")
            api.clock.advance(ronda["d"]["ends_at"] - api.clock.now_ms())
            await socket.until("arcade_result")

        # A mitad de corrida no hay historial: las rondas se escriben al cerrar.
        assert (await _run_row(api, inicio["d"]["run_id"])).status == "playing"
        assert (
            await api.session.scalar(select(func.count()).select_from(ArcadeAnswer))
        ) == 0

        ultima = await socket.until("arcade_question")
        api.clock.advance(ultima["d"]["ends_at"] - api.clock.now_ms())
        await socket.until("arcade_result")
        fin = await socket.until("arcade_end")

    fila = await _run_row(api, fin["d"]["run_id"])
    assert fila.status == "finished"
    assert fila.ended_at is not None
    assert (fila.score, fila.correct_count, fila.longest_streak) == (0, 0, 0)
    assert fila.max_difficulty == 1

    respuestas = (
        (
            await api.session.execute(
                select(ArcadeAnswer)
                .where(ArcadeAnswer.run_id == uuid.UUID(fin["d"]["run_id"]))
                .order_by(ArcadeAnswer.round_index)
            )
        )
        .scalars()
        .all()
    )
    assert [fila.round_index for fila in respuestas] == [0, 1, 2]
    assert {fila.question_id for fila in respuestas} == {p.id for p in preguntas}
    assert all(fila.chosen_index is None for fila in respuestas)
    assert all(fila.is_correct is False for fila in respuestas)
    assert all(fila.rejected is None for fila in respuestas)
    assert [fila.ms for fila in respuestas] == [20_000, 20_000, 20_000]
    assert [fila.points for fila in respuestas] == [0, 0, 0]
    assert all(fila.difficulty == 1 and fila.seconds == 20 for fila in respuestas)


async def test_a_run_that_cannot_be_saved_is_reported_and_can_retry(
    api: Api,
    connect: Callable[[User], WebSocketClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await sembrar(api.session)
    # En producción el usuario y el banco ya están commiteados; acá viven en la
    # transacción del fixture, y el `rollback` del intento fallido los borraría.
    # Commitear suelta ese SAVEPOINT: el rollback final del fixture deshace igual.
    await api.session.commit()
    original = arcade_runs.start_run
    intentos = 0

    async def _falla_la_primera(*args: Any, **kwargs: Any) -> None:
        nonlocal intentos
        intentos += 1
        if intentos == 1:
            raise RuntimeError("la base no contesta")
        await original(*args, **kwargs)

    monkeypatch.setattr(arcade_runs, "start_run", _falla_la_primera)

    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        error = await socket.until("error")
        assert error["d"]["code"] == "RUN_NOT_STARTED"

        # La corrida no quedó a medias: el jugador puede volver a intentar.
        await socket.send({"t": "start"})
        assert (await socket.until("arcade_start"))["d"]["lives"] == 3
        await socket.until("arcade_question")


async def test_a_run_that_cannot_be_closed_still_ends_for_the_player(
    api: Api,
    connect: Callable[[User], WebSocketClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await sembrar(api.session)

    async def _rompe(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("la base no contesta")

    monkeypatch.setattr(arcade_runs, "finish_run", _rompe)

    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        inicio = await socket.until("arcade_start")

        for _ in range(3):
            ronda = await socket.until("arcade_question")
            api.clock.advance(ronda["d"]["ends_at"] - api.clock.now_ms())
            await socket.until("arcade_result")

        fin = await socket.until("arcade_end")

    assert fin["d"]["score"] == 0
    # La fila quedó `playing`: el barrendero la invalida en el próximo arranque.
    assert (await _run_row(api, inicio["d"]["run_id"])).status == "playing"
    # Y sin cierre no hay ranking que mostrar.
    assert fin["d"]["rank_global"] is None
    assert fin["d"]["personal_best"] is None


# --------------------------------------------------------------------- ranking


def _finished(usuario: User, *, score: int, ended_at: datetime) -> ArcadeRun:
    return arcade_run(
        usuario.id,
        score=score,
        status="finished",
        started_at=ended_at - timedelta(minutes=1),
        ended_at=ended_at,
    )


async def test_the_end_message_includes_the_position_in_both_rankings(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    await sembrar(api.session)
    rival = user(nick="rival")
    api.session.add(rival)
    await api.session.flush()
    api.session.add(
        _finished(rival, score=500, ended_at=datetime.now(UTC) - timedelta(minutes=5))
    )
    await api.session.flush()

    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        await socket.until("arcade_start")
        for _ in range(3):
            ronda = await socket.until("arcade_question")
            api.clock.advance(ronda["d"]["ends_at"] - api.clock.now_ms())
            await socket.until("arcade_result")
        fin = await socket.until("arcade_end")

    assert fin["d"]["rank_global"] == 2
    assert fin["d"]["rank_weekly"] == 2
    assert fin["d"]["personal_best"] == 0
    assert fin["d"]["is_new_best"] is True


async def test_a_worse_run_keeps_the_previous_personal_best(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    await sembrar(api.session)
    api.session.add(
        _finished(
            api.user, score=250, ended_at=datetime.now(UTC) - timedelta(minutes=5)
        )
    )
    await api.session.flush()

    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        await socket.until("arcade_start")
        for _ in range(3):
            ronda = await socket.until("arcade_question")
            api.clock.advance(ronda["d"]["ends_at"] - api.clock.now_ms())
            await socket.until("arcade_result")
        fin = await socket.until("arcade_end")

    assert fin["d"]["personal_best"] == 250
    assert fin["d"]["is_new_best"] is False
    # Su mejor corrida sigue siendo la de 250, así que es el primero de la tabla.
    assert fin["d"]["rank_global"] == 1


async def test_a_ranking_failure_does_not_break_the_end(
    api: Api,
    connect: Callable[[User], WebSocketClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await sembrar(api.session)

    async def _rompe(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("la base no contesta")

    monkeypatch.setattr(leaderboard, "run_summary", _rompe)

    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        inicio = await socket.until("arcade_start")
        for _ in range(3):
            ronda = await socket.until("arcade_question")
            api.clock.advance(ronda["d"]["ends_at"] - api.clock.now_ms())
            await socket.until("arcade_result")
        fin = await socket.until("arcade_end")

    assert fin["d"]["score"] == 0
    assert fin["d"]["rank_global"] is None
    assert fin["d"]["is_new_best"] is False
    # La corrida sí se guardó: lo único que faltó fue la posición del mensaje.
    assert (await _run_row(api, inicio["d"]["run_id"])).status == "finished"


async def test_a_live_run_is_registered_until_it_ends(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    await sembrar(api.session)

    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        inicio = await socket.until("arcade_start")
        run_id = uuid.UUID(inicio["d"]["run_id"])

        # Mientras se juega, el barrendero no puede invalidarla por vieja.
        assert run_id in live_arcade_runs.ids()

        for _ in range(3):
            ronda = await socket.until("arcade_question")
            api.clock.advance(ronda["d"]["ends_at"] - api.clock.now_ms())
            await socket.until("arcade_result")
        await socket.until("arcade_end")

        assert run_id not in live_arcade_runs.ids()


async def test_a_socket_cut_mid_run_releases_it_but_leaves_the_row_playing(
    api: Api, connect: Callable[[User], WebSocketClient]
) -> None:
    await sembrar(api.session)

    async with connect(api.user) as socket:
        await socket.send({"t": "start"})
        inicio = await socket.until("arcade_start")
        run_id = uuid.UUID(inicio["d"]["run_id"])
        assert run_id in live_arcade_runs.ids()

    assert run_id not in live_arcade_runs.ids()
    # La fila queda abierta a propósito: el barrido la invalida tras el umbral.
    assert (await _run_row(api, str(run_id))).status == "playing"
