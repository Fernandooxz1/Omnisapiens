"""`POST /auth/guest` contra la API real y la base real del test."""

import re
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User
from app.security.tokens import create_guest_token, read_guest_token

from .constraints import acepta
from .factories import user


async def _cantidad_de_usuarios(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(User)) or 0


async def test_a_guest_without_a_nick_gets_a_generated_one(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    respuesta = await client.post("/auth/guest", json={})

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert re.fullmatch(r"Jugador\d{4}", cuerpo["user"]["nick"])
    assert cuerpo["user"]["is_guest"] is True

    # Y la fila quedó de verdad: el id del cuerpo es el mismo de la base.
    guardado = await session.get(User, uuid.UUID(cuerpo["user"]["id"]))
    assert guardado is not None
    assert guardado.nick == cuerpo["user"]["nick"]


async def test_the_token_that_comes_back_says_who_the_user_is(
    client: httpx.AsyncClient,
) -> None:
    cuerpo = (await client.post("/auth/guest", json={"nick": "ana"})).json()

    identidad = read_guest_token(cuerpo["token"])

    assert identidad.user_id == uuid.UUID(cuerpo["user"]["id"])
    assert identidad.nick == "ana"


async def test_the_nick_is_cleaned_before_saving(client: httpx.AsyncClient) -> None:
    respuesta = await client.post("/auth/guest", json={"nick": "  ana   maría "})

    assert respuesta.status_code == 201
    assert respuesta.json()["user"]["nick"] == "ana maría"


async def test_a_taken_nick_is_rejected(client: httpx.AsyncClient) -> None:
    await client.post("/auth/guest", json={"nick": "ana"})

    respuesta = await client.post("/auth/guest", json={"nick": "ana"})

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "NICK_TAKEN"


async def test_a_nick_that_differs_only_in_case_is_taken_too(
    client: httpx.AsyncClient,
) -> None:
    await client.post("/auth/guest", json={"nick": "Ana"})

    respuesta = await client.post("/auth/guest", json={"nick": "ANA"})

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "NICK_TAKEN"


async def test_a_forbidden_nick_is_rejected(client: httpx.AsyncClient) -> None:
    respuesta = await client.post("/auth/guest", json={"nick": "puto"})

    assert respuesta.status_code == 400
    assert respuesta.json()["error"]["code"] == "NICK_FORBIDDEN"


async def test_a_nick_that_is_too_long_is_rejected(client: httpx.AsyncClient) -> None:
    respuesta = await client.post("/auth/guest", json={"nick": "a" * 17})

    assert respuesta.status_code == 400
    assert respuesta.json()["error"]["code"] == "NICK_LENGTH"


async def test_an_absurd_nick_never_reaches_the_nick_rules(
    client: httpx.AsyncClient,
) -> None:
    # El tope del schema actúa antes de `clean_nick`: no se procesa un nick enorme.
    respuesta = await client.post("/auth/guest", json={"nick": "a" * 65})

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_a_valid_token_reuses_the_same_user_instead_of_creating_another(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    primero = (await client.post("/auth/guest", json={"nick": "ana"})).json()
    antes = await _cantidad_de_usuarios(session)

    segundo = await client.post(
        "/auth/guest",
        json={"nick": "otro"},
        headers={"Authorization": f"Bearer {primero['token']}"},
    )

    assert segundo.status_code == 201
    assert segundo.json()["user"]["id"] == primero["user"]["id"]
    # El nick del body se ignora: la identidad la manda el token.
    assert segundo.json()["user"]["nick"] == "ana"
    assert await _cantidad_de_usuarios(session) == antes


async def test_a_deleted_user_frees_its_nick(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    # El único de `nick` es parcial (WHERE deleted_at IS NULL): un usuario borrado
    # lógico no bloquea el nick para siempre.
    await acepta(session, user(nick="ana", deleted_at=datetime.now(UTC)))

    respuesta = await client.post("/auth/guest", json={"nick": "ana"})

    assert respuesta.status_code == 201


async def test_a_garbage_token_is_rejected(client: httpx.AsyncClient) -> None:
    respuesta = await client.post(
        "/auth/guest", json={}, headers={"Authorization": "Bearer no-es-un-token"}
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "AUTH_REQUIRED"


async def test_a_header_without_bearer_is_rejected(client: httpx.AsyncClient) -> None:
    respuesta = await client.post(
        "/auth/guest", json={}, headers={"Authorization": "el-token-pelado"}
    )

    assert respuesta.status_code == 401


async def test_an_expired_token_is_rejected(client: httpx.AsyncClient) -> None:
    vencido = datetime.now(UTC) - timedelta(days=settings.jwt_ttl_days, seconds=1)
    token = create_guest_token(uuid.uuid4(), "ana", now=vencido)

    respuesta = await client.post(
        "/auth/guest", json={}, headers={"Authorization": f"Bearer {token}"}
    )

    assert respuesta.status_code == 401


async def test_a_token_of_a_user_that_is_no_longer_there_is_rejected(
    client: httpx.AsyncClient,
) -> None:
    # Firma válida, usuario que no existe: el token ya no es de nadie.
    fantasma = create_guest_token(uuid.uuid4(), "fantasma")

    respuesta = await client.post(
        "/auth/guest", json={}, headers={"Authorization": f"Bearer {fantasma}"}
    )

    assert respuesta.status_code == 401


async def test_a_token_of_a_logically_deleted_user_is_rejected(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    cuerpo = (await client.post("/auth/guest", json={"nick": "ana"})).json()
    usuario = await session.get(User, uuid.UUID(cuerpo["user"]["id"]))
    assert usuario is not None
    usuario.deleted_at = datetime.now(UTC)
    await session.flush()

    respuesta = await client.post(
        "/auth/guest", json={}, headers={"Authorization": f"Bearer {cuerpo['token']}"}
    )

    assert respuesta.status_code == 401
