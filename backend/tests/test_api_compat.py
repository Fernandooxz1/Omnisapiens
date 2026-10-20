"""La matriz de compatibilidad: cada alias responde igual que su ruta nueva.

La tabla de `docs/api.md` §Compatibilidad es el contrato. Acá se verifica lo que
el cliente viejo nota: mismo status y mismo body. No alcanza con que la ruta
exista; un alias que cambia la forma rompe al cliente que todavía no migró.
"""

from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User
from app.security.tokens import create_guest_token
from app.services import importer

from .factories import game_session, user

ADMIN_TOKEN = "token-de-prueba"
_AUTH = {"X-Admin-Token": ADMIN_TOKEN}

_HEADER = ",".join(importer.COLUMNS)


@pytest.fixture(autouse=True)
def _admin_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "admin_token", ADMIN_TOKEN)


def _bearer(usuario: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_guest_token(usuario.id, usuario.nick)}"}


async def _player(session: AsyncSession, nick: str) -> User:
    fila = user(nick=nick)
    session.add(fila)
    await session.flush()
    return fila


def _row(prompt: str) -> str:
    valores = {
        "category": "geography",
        "difficulty": "2",
        "prompt": prompt,
        "option_a": "Paraná",
        "option_b": "Amazonas",
        "option_c": "Orinoco",
        "option_d": "Magdalena",
        "correct": "B",
        "explanation": "El Amazonas.",
        "source": "manual",
        "tags": "mundo",
    }
    return ",".join(valores[columna] for columna in importer.COLUMNS)


def _csv(prompt: str) -> bytes:
    return ("\n".join([_HEADER, _row(prompt)]) + "\n").encode("utf-8")


async def test_the_ranking_alias_matches_both_mode_routes(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ana = await _player(session, "ana")
    ended_at = datetime.now(UTC) - timedelta(minutes=5)
    session.add(
        game_session(
            status="finished",
            owner_user_id=ana.id,
            score=900,
            started_at=ended_at - timedelta(minutes=1),
            ended_at=ended_at,
        )
    )
    await session.flush()

    for suffix in ("", "/me"):
        alias = await client.get(f"/leaderboard/arcade{suffix}", headers=_bearer(ana))
        nueva = await client.get(
            f"/leaderboard/trivia_arcade{suffix}", headers=_bearer(ana)
        )

        assert alias.status_code == nueva.status_code == 200
        assert alias.json() == nueva.json()


async def test_every_import_alias_returns_the_same_report(
    client: httpx.AsyncClient,
) -> None:
    rutas = (
        "/admin/content/quiz",
        "/admin/content/quiz/import",
        "/admin/questions/import",
    )
    reportes = []
    for posicion, ruta in enumerate(rutas):
        respuesta = await client.post(
            ruta,
            headers=_AUTH,
            files={
                "file": (
                    "q.csv",
                    _csv(f"¿Pregunta {posicion}?"),
                    "application/octet-stream",
                )
            },
        )
        assert respuesta.status_code == 200, ruta
        reportes.append(respuesta.json())

    assert reportes[0] == {
        "total": 1,
        "imported": 1,
        "duplicated": 0,
        "rejected": [],
    }
    assert reportes[1] == reportes[0]
    assert reportes[2] == reportes[0]
