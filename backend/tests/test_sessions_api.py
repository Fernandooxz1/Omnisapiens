"""`POST /sessions`: el modo, su configuración y la fila en `playing`."""

import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GameSession


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _guest(client: httpx.AsyncClient, nick: str | None = None) -> dict:
    cuerpo = {} if nick is None else {"nick": nick}
    return (await client.post("/auth/guest", json=cuerpo)).json()


async def test_creating_a_session_requires_a_token(
    client: httpx.AsyncClient,
) -> None:
    respuesta = await client.post("/sessions", json={"mode": "trivia_arcade"})

    assert respuesta.status_code == 401


async def test_creates_an_arcade_session(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.post(
        "/sessions", json={"mode": "trivia_arcade"}, headers=_auth(alta["token"])
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    session_id = uuid.UUID(cuerpo["session_id"])
    assert cuerpo["ws_url"] == f"/ws/session/{cuerpo['session_id']}"

    fila = await session.scalar(select(GameSession).where(GameSession.id == session_id))
    assert fila is not None
    assert fila.status == "playing"
    assert fila.mode == "trivia_arcade"
    assert fila.content_kind == "quiz"
    assert fila.play_format == "arcade"
    assert fila.ruleset_version == 1
    assert fila.config == {}
    assert fila.owner_user_id == uuid.UUID(alta["user"]["id"])
    assert fila.started_at is not None
    assert fila.ended_at is None


async def test_an_unknown_mode_is_a_404(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.post(
        "/sessions", json={"mode": "trivia_nope"}, headers=_auth(alta["token"])
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "MODE_NOT_FOUND"


async def test_a_versus_mode_is_rejected(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.post(
        "/sessions", json={"mode": "trivia_versus"}, headers=_auth(alta["token"])
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "MODE_NOT_SOLO"


async def test_an_invalid_config_is_rejected(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.post(
        "/sessions",
        json={"mode": "trivia_arcade", "config": {"vidas": 5}},
        headers=_auth(alta["token"]),
    )

    assert respuesta.status_code == 422
    error = respuesta.json()["error"]
    assert error["code"] == "INVALID_CONFIG"
    assert "vidas" in error["message"]


async def test_the_body_is_validated_by_fastapi(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.post(
        "/sessions", json={"config": {}}, headers=_auth(alta["token"])
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_creating_sessions_is_rate_limited(
    client: httpx.AsyncClient, monkeypatch
) -> None:
    from app.api import rate_limit

    monkeypatch.setattr(rate_limit.settings, "rate_limit_session_per_minute", 1)
    alta = await _guest(client, "ana")

    primera = await client.post(
        "/sessions", json={"mode": "trivia_arcade"}, headers=_auth(alta["token"])
    )
    segunda = await client.post(
        "/sessions", json={"mode": "trivia_arcade"}, headers=_auth(alta["token"])
    )

    assert primera.status_code == 201
    assert segunda.status_code == 429
    assert segunda.json()["error"]["code"] == "RATE_LIMITED"
