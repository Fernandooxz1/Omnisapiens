"""`POST /rooms` y `GET /rooms/{code}` contra la API y la base reales."""

import re
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.game.constants import ROOM_CODE_ALPHABET, ROOM_CODE_LENGTH
from app.game.match_engine import MatchConfig
from app.models import Room
from app.runtime.room_manager import Outbox, room_store

from .factories import room, user

CODIGO_RE = re.compile(f"^[{ROOM_CODE_ALPHABET}]{{{ROOM_CODE_LENGTH}}}$")


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _guest(client: httpx.AsyncClient, nick: str | None = None) -> dict:
    cuerpo = {} if nick is None else {"nick": nick}
    return (await client.post("/auth/guest", json=cuerpo)).json()


async def test_creating_a_room_requires_a_token(client: httpx.AsyncClient) -> None:
    respuesta = await client.post("/rooms", json={})

    assert respuesta.status_code == 401


async def test_creates_a_room_with_defaults(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.post("/rooms", json={}, headers=_auth(alta["token"]))

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert CODIGO_RE.fullmatch(cuerpo["code"])
    assert cuerpo["config"] == {"rounds": 5, "seconds": 20}

    sala = await session.scalar(select(Room).where(Room.code == cuerpo["code"]))
    assert sala is not None
    assert sala.host_user_id == uuid.UUID(alta["user"]["id"])
    assert sala.status == "waiting"
    assert sala.expires_at > datetime.now(UTC)


async def test_honors_the_requested_config(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.post(
        "/rooms", json={"rounds": 7, "seconds": 30}, headers=_auth(alta["token"])
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["config"] == {"rounds": 7, "seconds": 30}


async def test_rejects_a_rounds_value_out_of_the_options(
    client: httpx.AsyncClient,
) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.post(
        "/rooms", json={"rounds": 4}, headers=_auth(alta["token"])
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "rounds:" in respuesta.json()["error"]["message"]


async def test_rejects_a_seconds_value_out_of_the_options(
    client: httpx.AsyncClient,
) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.post(
        "/rooms", json={"seconds": 15}, headers=_auth(alta["token"])
    )

    assert respuesta.status_code == 422


async def test_two_rooms_get_different_codes(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")

    primero = (
        await client.post("/rooms", json={}, headers=_auth(alta["token"]))
    ).json()
    segundo = (
        await client.post("/rooms", json={}, headers=_auth(alta["token"]))
    ).json()

    assert primero["code"] != segundo["code"]


async def test_preview_returns_the_room_and_its_host(
    client: httpx.AsyncClient,
) -> None:
    alta = await _guest(client, "ana")
    creada = (await client.post("/rooms", json={}, headers=_auth(alta["token"]))).json()

    respuesta = await client.get(f"/rooms/{creada['code']}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["code"] == creada["code"]
    assert cuerpo["status"] == "waiting"
    assert cuerpo["config"] == creada["config"]
    assert cuerpo["host_nick"] == "ana"
    assert cuerpo["players"] == 0


async def test_preview_reports_the_connected_players(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    """`players` sale del estado vivo del proceso, no de la base."""
    alta = await _guest(client, "ana")
    creada = (await client.post("/rooms", json={}, headers=_auth(alta["token"]))).json()
    sala = await session.scalar(select(Room).where(Room.code == creada["code"]))
    assert sala is not None

    await room_store.open(
        code=sala.code,
        room_id=str(sala.id),
        config=MatchConfig(**sala.config),
        host_id=str(sala.host_user_id),
    )
    try:
        await room_store.join(
            code=sala.code,
            user_id=str(sala.host_user_id),
            nick="ana",
            outbox=Outbox(),
        )

        respuesta = await client.get(f"/rooms/{sala.code}")

        assert respuesta.status_code == 200
        assert respuesta.json()["players"] == 1
    finally:
        await room_store.close()


async def test_preview_does_not_require_a_token(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")
    creada = (await client.post("/rooms", json={}, headers=_auth(alta["token"]))).json()

    respuesta = await client.get(f"/rooms/{creada['code']}")

    assert respuesta.status_code == 200


async def test_preview_normalizes_a_lowercase_code(
    client: httpx.AsyncClient,
) -> None:
    alta = await _guest(client, "ana")
    creada = (await client.post("/rooms", json={}, headers=_auth(alta["token"]))).json()

    respuesta = await client.get(f"/rooms/{creada['code'].lower()}")

    assert respuesta.status_code == 200
    assert respuesta.json()["code"] == creada["code"]


async def test_preview_of_an_unknown_code_is_a_404(client: httpx.AsyncClient) -> None:
    respuesta = await client.get("/rooms/ZZZZZZ")

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "ROOM_NOT_FOUND"


async def test_preview_of_an_expired_room_is_a_404(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ana = user(nick="ana")
    session.add(ana)
    await session.flush()
    vencida = room(ana.id, status="expired")
    session.add(vencida)
    await session.flush()

    respuesta = await client.get(f"/rooms/{vencida.code}")

    assert respuesta.status_code == 404


async def test_preview_of_a_waiting_room_past_its_deadline_is_a_404(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ana = user(nick="ana")
    session.add(ana)
    await session.flush()
    vencida = room(ana.id, expires_at=datetime.now(UTC) - timedelta(minutes=1))
    session.add(vencida)
    await session.flush()

    respuesta = await client.get(f"/rooms/{vencida.code}")

    assert respuesta.status_code == 404
