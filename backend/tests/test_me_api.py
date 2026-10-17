"""`/me` contra la API real y la base real del test."""

import uuid

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.security.tokens import read_guest_token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _guest(client: httpx.AsyncClient, nick: str | None = None) -> dict:
    cuerpo = {} if nick is None else {"nick": nick}
    return (await client.post("/auth/guest", json=cuerpo)).json()


async def test_without_a_token_is_a_401(client: httpx.AsyncClient) -> None:
    respuesta = await client.get("/me")

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "AUTH_REQUIRED"


async def test_the_token_identifies_the_user(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.get("/me", headers=_auth(alta["token"]))

    assert respuesta.status_code == 200
    assert respuesta.json()["id"] == alta["user"]["id"]
    assert respuesta.json()["nick"] == "ana"


async def test_reading_the_profile_refreshes_last_seen(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    alta = await _guest(client, "ana")
    usuario = await session.get(User, uuid.UUID(alta["user"]["id"]))
    assert usuario is not None
    antes = usuario.last_seen_at

    await client.get("/me", headers=_auth(alta["token"]))
    await session.refresh(usuario)

    assert usuario.last_seen_at > antes


async def test_patch_changes_the_nick(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.patch(
        "/me", json={"nick": "  ana  maría "}, headers=_auth(alta["token"])
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["user"]["nick"] == "ana maría"
    usuario = await session.get(User, uuid.UUID(alta["user"]["id"]))
    assert usuario is not None
    assert usuario.nick == "ana maría"


async def test_patch_returns_a_token_that_carries_the_new_nick(
    client: httpx.AsyncClient,
) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.patch(
        "/me", json={"nick": "beto"}, headers=_auth(alta["token"])
    )

    assert read_guest_token(respuesta.json()["token"]).nick == "beto"


async def test_patch_rejects_a_nick_already_in_use(client: httpx.AsyncClient) -> None:
    await _guest(client, "ana")
    beto = await _guest(client, "beto")

    respuesta = await client.patch(
        "/me", json={"nick": "ana"}, headers=_auth(beto["token"])
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "NICK_TAKEN"


async def test_patch_rejects_a_nick_that_only_differs_in_case(
    client: httpx.AsyncClient,
) -> None:
    await _guest(client, "Ana")
    beto = await _guest(client, "beto")

    respuesta = await client.patch(
        "/me", json={"nick": "ANA"}, headers=_auth(beto["token"])
    )

    assert respuesta.status_code == 409


async def test_patch_rejects_a_forbidden_nick(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.patch(
        "/me", json={"nick": "puto"}, headers=_auth(alta["token"])
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["error"]["code"] == "NICK_FORBIDDEN"


async def test_patch_rejects_a_nick_that_is_too_long(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.patch(
        "/me", json={"nick": "a" * 17}, headers=_auth(alta["token"])
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["error"]["code"] == "NICK_LENGTH"


async def test_patch_without_a_token_is_a_401(client: httpx.AsyncClient) -> None:
    respuesta = await client.patch("/me", json={"nick": "ana"})

    assert respuesta.status_code == 401


async def test_patch_can_keep_the_same_nick(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.patch(
        "/me", json={"nick": "ana"}, headers=_auth(alta["token"])
    )

    assert respuesta.status_code == 200


async def test_delete_marks_the_user_as_deleted(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    alta = await _guest(client, "ana")

    respuesta = await client.delete("/me", headers=_auth(alta["token"]))

    assert respuesta.status_code == 204
    usuario = await session.get(User, uuid.UUID(alta["user"]["id"]))
    assert usuario is not None
    assert usuario.deleted_at is not None


async def test_after_delete_the_token_is_no_longer_valid(
    client: httpx.AsyncClient,
) -> None:
    alta = await _guest(client, "ana")
    await client.delete("/me", headers=_auth(alta["token"]))

    respuesta = await client.get("/me", headers=_auth(alta["token"]))

    assert respuesta.status_code == 401


async def test_delete_frees_the_nick(client: httpx.AsyncClient) -> None:
    alta = await _guest(client, "ana")
    await client.delete("/me", headers=_auth(alta["token"]))

    respuesta = await client.post("/auth/guest", json={"nick": "ana"})

    assert respuesta.status_code == 201


async def test_delete_without_a_token_is_a_401(client: httpx.AsyncClient) -> None:
    respuesta = await client.delete("/me")

    assert respuesta.status_code == 401
