"""El listado de preguntas del panel: pase, filtros y paginación.

El token se fija con `monkeypatch` y no se toma de `.env`: un test no debe
depender de qué valor de desarrollo tenga la máquina.
"""

from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Question

from .factories import question

ADMIN_TOKEN = "token-de-prueba"
_AUTH = {"X-Admin-Token": ADMIN_TOKEN}


@pytest.fixture(autouse=True)
def _admin_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "admin_token", ADMIN_TOKEN)


def _question(
    session: AsyncSession,
    *,
    created_at: datetime,
    **overrides: object,
) -> Question:
    fila = question(created_at=created_at, **overrides)
    session.add(fila)
    return fila


async def test_without_the_header_the_list_is_forbidden(
    client: httpx.AsyncClient,
) -> None:
    respuesta = await client.get("/admin/questions")

    assert respuesta.status_code == 401
    assert respuesta.json() == {
        "error": {
            "code": "ADMIN_REQUIRED",
            "message": "Se necesita el token de administración.",
        }
    }


@pytest.mark.parametrize("token", ["", "otro-token", ADMIN_TOKEN + "x"])
async def test_a_wrong_token_is_the_same_401(
    client: httpx.AsyncClient, token: str
) -> None:
    respuesta = await client.get("/admin/questions", headers={"X-Admin-Token": token})

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "ADMIN_REQUIRED"


async def test_the_page_lists_the_newest_first_and_counts_the_whole_bank(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ahora = datetime.now(UTC)
    vieja = _question(session, created_at=ahora - timedelta(hours=2), prompt="Vieja")
    media = _question(session, created_at=ahora - timedelta(hours=1), prompt="Media")
    nueva = _question(session, created_at=ahora, prompt="Nueva")
    await session.flush()

    respuesta = await client.get("/admin/questions", headers=_AUTH)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert [fila["id"] for fila in cuerpo["items"]] == [
        str(nueva.id),
        str(media.id),
        str(vieja.id),
    ]
    assert cuerpo["total"] == 3
    assert cuerpo["pages"] == 1
    assert (cuerpo["page"], cuerpo["page_size"]) == (1, 20)


async def test_every_filter_narrows_the_same_way_in_items_and_total(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ahora = datetime.now(UTC)
    _question(
        session,
        created_at=ahora,
        status="draft",
        category="geography",
        difficulty=1,
        prompt="¿Cuál es la capital de Francia?",
    )
    _question(
        session,
        created_at=ahora,
        status="published",
        category="history",
        difficulty=3,
        prompt="¿Quién pintó el Guernica?",
    )
    _question(
        session,
        created_at=ahora,
        status="archived",
        category="science",
        difficulty=5,
        prompt="¿Cuál es el símbolo químico del oro?",
    )
    await session.flush()

    casos = [
        ({"status": "published"}, "¿Quién pintó el Guernica?"),
        ({"category": "science"}, "¿Cuál es el símbolo químico del oro?"),
        ({"difficulty": 1}, "¿Cuál es la capital de Francia?"),
        ({"q": "guernica"}, "¿Quién pintó el Guernica?"),
        (
            {"status": "draft", "category": "geography", "difficulty": 1},
            "¿Cuál es la capital de Francia?",
        ),
    ]
    for filtros, esperado in casos:
        respuesta = await client.get("/admin/questions", params=filtros, headers=_AUTH)
        cuerpo = respuesta.json()
        assert [fila["prompt"] for fila in cuerpo["items"]] == [esperado], filtros
        assert cuerpo["total"] == 1, filtros


async def test_search_is_case_insensitive_and_treats_wildcards_as_text(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ahora = datetime.now(UTC)
    _question(
        session,
        created_at=ahora - timedelta(minutes=1),
        prompt="El Río de la Plata",
    )
    _question(
        session, created_at=ahora - timedelta(minutes=2), prompt="El río Amazonas"
    )
    _question(
        session, created_at=ahora - timedelta(minutes=3), prompt="Una montaña rusa"
    )
    _question(
        session,
        created_at=ahora - timedelta(minutes=4),
        prompt="Cien por ciento 100% puro",
    )
    await session.flush()

    rio = (
        await client.get("/admin/questions", params={"q": "río"}, headers=_AUTH)
    ).json()
    comodines = (
        await client.get("/admin/questions", params={"q": "%"}, headers=_AUTH)
    ).json()

    assert [fila["prompt"] for fila in rio["items"]] == [
        "El Río de la Plata",
        "El río Amazonas",
    ]
    # Si el `%` no se escapara, esto devolvería el banco entero.
    assert [fila["prompt"] for fila in comodines["items"]] == [
        "Cien por ciento 100% puro"
    ]


async def test_pagination_does_not_repeat_or_lose_rows(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    ahora = datetime.now(UTC)
    for indice in range(5):
        _question(
            session,
            created_at=ahora + timedelta(seconds=indice),
            prompt=f"Pregunta {indice}",
        )
    await session.flush()

    primera = (
        await client.get(
            "/admin/questions", params={"page": 1, "page_size": 2}, headers=_AUTH
        )
    ).json()
    segunda = (
        await client.get(
            "/admin/questions", params={"page": 2, "page_size": 2}, headers=_AUTH
        )
    ).json()
    vacia = (
        await client.get(
            "/admin/questions", params={"page": 4, "page_size": 2}, headers=_AUTH
        )
    ).json()

    assert [fila["prompt"] for fila in primera["items"]] == ["Pregunta 4", "Pregunta 3"]
    assert [fila["prompt"] for fila in segunda["items"]] == ["Pregunta 2", "Pregunta 1"]
    assert primera["total"] == segunda["total"] == 5
    assert primera["pages"] == segunda["pages"] == 3
    # Pasarse de página no es un error: el cliente vuelve para atrás.
    assert vacia["items"] == []
    assert vacia["total"] == 5


async def test_the_item_carries_the_answer_and_the_media_fields(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    creada = _question(
        session,
        created_at=datetime.now(UTC),
        options=["Rojo", "Verde", "Azul", "Amarillo"],
        correct_index=2,
        explanation="Es el color del mar.",
        source="manual",
        tags=["color", "mar"],
    )
    await session.flush()

    fila = (await client.get("/admin/questions", headers=_AUTH)).json()["items"][0]

    assert fila["id"] == str(creada.id)
    assert fila["correct_index"] == 2
    assert fila["options"] == ["Rojo", "Verde", "Azul", "Amarillo"]
    assert fila["explanation"] == "Es el color del mar."
    assert (fila["status"], fila["media_type"], fila["media_url"]) == (
        "draft",
        "none",
        None,
    )
    assert (fila["source"], fila["tags"]) == ("manual", ["color", "mar"])
    assert fila["created_at"] is not None
    assert fila["updated_at"] is not None


@pytest.mark.parametrize(
    "filtros",
    [
        {"status": "deleted"},
        {"category": "cinema"},
        {"category": "Geography"},
        {"difficulty": 0},
        {"difficulty": 6},
        {"page": 0},
        {"page_size": 0},
        {"page_size": 101},
        {"q": "x" * 301},
    ],
)
async def test_a_bad_filter_is_a_validation_error(
    client: httpx.AsyncClient, filtros: dict[str, object]
) -> None:
    respuesta = await client.get("/admin/questions", params=filtros, headers=_AUTH)

    assert respuesta.status_code == 422, filtros
    assert respuesta.json()["error"]["code"] == "VALIDATION_ERROR"
