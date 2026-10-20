"""El WebSocket de sesión genérica, con el protocolo canónico.

La sesión se crea por `POST /sessions` y se juega por `/ws/session/{id}`. La app
corre en el mismo event loop del test, así el handler comparte la sesión de base
y el reloj falso: una partida entera corre en milisegundos.
"""

import uuid
from typing import Any

import pytest
from sqlalchemy import select

from app.main import app
from app.models import ContentItem, GameSession, SessionAttempt, SessionItem
from app.security.tokens import create_guest_token

from . import ws_fixtures
from .factories import quiz_content, user
from .ws_client import WebSocketClient, WebSocketClosed

session_api = ws_fixtures.session_api
session_connect = ws_fixtures.session_connect


async def sembrar(
    api: Any, *, dificultades: tuple[int, ...] = (1,), cuantas: int = 3
) -> list[ContentItem]:
    """Preguntas con una respuesta correcta reconocible después del barajado."""
    pares = [
        quiz_content(
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
    api.session.add_all([fila for par in pares for fila in par])
    await api.session.flush()
    return [item for item, _ in pares]


def correcta(item: dict[str, Any]) -> int:
    opciones: list[str] = item["d"]["payload"]["options"]
    return opciones.index("correcta")


async def _perder_las_tres_vidas(api: Any, socket: Any) -> dict[str, Any]:
    for _ in range(3):
        item = await socket.until("item_start")
        api.clock.advance(item["d"]["ends_at"] - api.clock.now_ms())
        await socket.until("item_result")
    return await socket.until("session_end")


async def test_the_session_starts_and_serves_the_first_item(
    session_api: Any, session_connect: Any
) -> None:
    await sembrar(session_api)
    session_id = await session_api.create()

    async with session_connect(session_id) as socket:
        inicio = await socket.until("session_start")
        assert inicio["d"]["session_id"] == session_id
        assert inicio["d"]["mode"] == "trivia_arcade"
        assert inicio["d"]["config"] == {}
        assert inicio["d"]["lives"] == 3

        item = await socket.until("item_start")
        assert item["d"]["item_key"] == "0"
        assert item["d"]["position"] == 0
        assert item["d"]["total_seconds"] == 20
        assert item["d"]["ends_at"] == session_api.clock.now_ms() + 20_000
        assert set(item["d"]["payload"]) == {"v", "prompt", "options", "media"}
        assert "correct_index" not in item["d"]["payload"]


async def test_a_correct_answer_scores_and_serves_the_next_item(
    session_api: Any, session_connect: Any
) -> None:
    await sembrar(session_api)
    session_id = await session_api.create()

    async with session_connect(session_id) as socket:
        primera = await socket.until("item_start")
        await socket.send(
            {
                "t": "answer",
                "d": {"round": 0, "choice": correcta(primera)},
            }
        )
        resultado = await socket.until("item_result")

        assert resultado["d"]["item_key"] == "0"
        assert resultado["d"]["correct"] is True
        assert resultado["d"]["points"] == 150
        assert resultado["d"]["scores"] == {
            "score": 150,
            "lives": 3,
            "streak": 1,
            "correct_count": 1,
        }

        siguiente = await socket.until("item_start")
        assert siguiente["d"]["position"] == 1


async def test_the_result_reveals_the_shuffled_solution(
    session_api: Any, session_connect: Any
) -> None:
    await sembrar(session_api)
    session_id = await session_api.create()

    async with session_connect(session_id) as socket:
        item = await socket.until("item_start")
        eleccion = correcta(item)
        await socket.send({"t": "answer", "d": {"round": 0, "choice": eleccion}})
        resultado = await socket.until("item_result")

        assert resultado["d"]["solution"]["correct_index"] == eleccion
        assert resultado["d"]["submission"] == {"type": "choice", "index": eleccion}


async def test_a_wrong_answer_loses_a_life(
    session_api: Any, session_connect: Any
) -> None:
    await sembrar(session_api)
    session_id = await session_api.create()

    async with session_connect(session_id) as socket:
        item = await socket.until("item_start")
        incorrecta = (correcta(item) + 1) % 4
        await socket.send({"t": "answer", "d": {"round": 0, "choice": incorrecta}})
        resultado = await socket.until("item_result")

        assert resultado["d"]["correct"] is False
        assert resultado["d"]["points"] == 0
        assert resultado["d"]["solution"]["correct_index"] == correcta(item)
        assert resultado["d"]["scores"]["lives"] == 2


async def test_an_expired_item_is_resolved_without_a_submission(
    session_api: Any, session_connect: Any
) -> None:
    await sembrar(session_api)
    session_id = await session_api.create()

    async with session_connect(session_id) as socket:
        item = await socket.until("item_start")
        session_api.clock.advance(item["d"]["ends_at"] - session_api.clock.now_ms())
        resultado = await socket.until("item_result")

        assert resultado["d"]["submission"] is None
        assert resultado["d"]["correct"] is False
        assert resultado["d"]["scores"]["lives"] == 2


async def test_state_returns_the_item_in_flight(
    session_api: Any, session_connect: Any
) -> None:
    await sembrar(session_api)
    session_id = await session_api.create()

    async with session_connect(session_id) as socket:
        item = await socket.until("item_start")
        await socket.send({"t": "state"})
        estado = await socket.until("session_state")

        assert estado["d"]["session_id"] == session_id
        assert estado["d"]["position"] == 0
        assert estado["d"]["ends_at"] == item["d"]["ends_at"]
        assert estado["d"]["total_seconds"] == 20
        assert estado["d"]["payload"] == item["d"]["payload"]
        assert estado["d"]["finished"] is False
        assert estado["d"]["scores"]["lives"] == 3


async def test_ping_malformed_and_unknown_messages(
    session_api: Any, session_connect: Any
) -> None:
    await sembrar(session_api)
    session_id = await session_api.create()

    async with session_connect(session_id) as socket:
        await socket.until("item_start")

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

        await socket.send({"t": "ping"})
        assert (await socket.receive())["t"] == "pong"


async def test_the_end_closes_the_row_and_includes_the_ranking(
    session_api: Any, session_connect: Any
) -> None:
    await sembrar(session_api)
    session_id = await session_api.create()

    async with session_connect(session_id) as socket:
        fin = await _perder_las_tres_vidas(session_api, socket)

    assert fin["d"]["session_id"] == session_id
    assert fin["d"]["score"] == 0
    assert fin["d"]["correct_count"] == 0
    assert fin["d"]["longest_streak"] == 0
    assert fin["d"]["max_difficulty"] == 1
    assert fin["d"]["ranking"] == {
        "rank_global": 1,
        "rank_weekly": 1,
        "personal_best": 0,
        "is_new_best": True,
    }

    fila = await _session_row(session_api, session_id)
    assert fila.status == "finished"
    assert fila.ended_at is not None


async def test_a_finished_session_is_persisted_with_its_history(
    session_api: Any, session_connect: Any
) -> None:
    preguntas = await sembrar(session_api)
    session_id = await session_api.create()

    async with session_connect(session_id) as socket:
        await _perder_las_tres_vidas(session_api, socket)

    items, attempts = await _history(session_api, session_id)
    assert [item.position for item in items] == [0, 1, 2]
    assert [item.item_key for item in items] == ["0", "1", "2"]
    assert {item.content_id for item in items} == {
        pregunta.id for pregunta in preguntas
    }
    assert all(item.solution_snapshot["v"] == 1 for item in items)
    assert [attempt.item_id for attempt in attempts] == [item.id for item in items]
    assert all(attempt.submission == {} for attempt in attempts)


async def test_answering_after_the_end_is_rejected(
    session_api: Any, session_connect: Any
) -> None:
    await sembrar(session_api)
    session_id = await session_api.create()

    async with session_connect(session_id) as socket:
        await _perder_las_tres_vidas(session_api, socket)

        await socket.send({"t": "answer", "d": {"round": 3, "choice": 0}})
        assert (await socket.receive())["d"]["code"] == "NOT_PLAYING"


async def test_a_session_cut_mid_run_is_abandoned(
    session_api: Any, session_connect: Any
) -> None:
    await sembrar(session_api)
    session_id = await session_api.create()

    async with session_connect(session_id) as socket:
        await socket.until("item_start")
        assert uuid.UUID(session_id) in session_api.store.live()

    assert uuid.UUID(session_id) not in session_api.store.live()
    fila = await _session_row(session_api, session_id)
    assert fila.status == "abandoned"
    assert fila.ended_at is not None


async def test_a_finished_session_cannot_be_reopened(
    session_api: Any, session_connect: Any
) -> None:
    await sembrar(session_api)
    session_id = await session_api.create()

    async with session_connect(session_id) as socket:
        await _perder_las_tres_vidas(session_api, socket)

    async with session_connect(session_id) as socket:
        error = await socket.receive()
        assert error["d"]["code"] == "NOT_PLAYING"
        with pytest.raises(WebSocketClosed) as cierre:
            await socket.receive()
        assert cierre.value.code == 1008


async def test_a_session_of_another_user_is_rejected(session_api: Any) -> None:
    await sembrar(session_api)
    session_id = await session_api.create()

    beto = user(nick="beto")
    session_api.session.add(beto)
    await session_api.session.flush()
    token = create_guest_token(beto.id, beto.nick)

    async with WebSocketClient(
        app, f"/ws/session/{session_id}", query=f"token={token}"
    ) as socket:
        assert (await socket.receive())["d"]["code"] == "NOT_PLAYING"
        with pytest.raises(WebSocketClosed) as cierre:
            await socket.receive()
        assert cierre.value.code == 1008


async def test_an_unknown_session_id_is_rejected(session_api: Any) -> None:
    token = create_guest_token(session_api.user.id, session_api.user.nick)

    async with WebSocketClient(
        app, f"/ws/session/{uuid.uuid4()}", query=f"token={token}"
    ) as socket:
        assert (await socket.receive())["d"]["code"] == "NOT_PLAYING"
        with pytest.raises(WebSocketClosed) as cierre:
            await socket.receive()
        assert cierre.value.code == 1008


async def test_a_malformed_session_id_is_rejected(session_api: Any) -> None:
    token = create_guest_token(session_api.user.id, session_api.user.nick)

    async with WebSocketClient(
        app, "/ws/session/no-es-un-id", query=f"token={token}"
    ) as socket:
        assert (await socket.receive())["d"]["code"] == "NOT_PLAYING"


async def test_without_a_token_the_socket_is_rejected() -> None:
    async with WebSocketClient(app, f"/ws/session/{uuid.uuid4()}") as socket:
        assert (await socket.receive())["d"]["code"] == "AUTH_REQUIRED"
        with pytest.raises(WebSocketClosed) as cierre:
            await socket.receive()
        assert cierre.value.code == 1008


async def _session_row(api: Any, session_id: str) -> Any:
    return (
        await api.session.execute(
            select(
                GameSession.status,
                GameSession.owner_user_id,
                GameSession.mode,
                GameSession.score,
                GameSession.correct_count,
                GameSession.longest_streak,
                GameSession.max_difficulty,
                GameSession.started_at,
                GameSession.ended_at,
            ).where(GameSession.id == uuid.UUID(session_id))
        )
    ).one()


async def _history(api: Any, session_id: str) -> tuple[list[Any], list[Any]]:
    items = (
        (
            await api.session.execute(
                select(SessionItem)
                .where(SessionItem.session_id == uuid.UUID(session_id))
                .order_by(SessionItem.position)
            )
        )
        .scalars()
        .all()
    )
    attempts = (
        (
            await api.session.execute(
                select(SessionAttempt)
                .join(SessionItem, SessionAttempt.item_id == SessionItem.id)
                .where(SessionItem.session_id == uuid.UUID(session_id))
                .order_by(SessionItem.position, SessionAttempt.attempt_seq)
            )
        )
        .scalars()
        .all()
    )
    return list(items), list(attempts)
