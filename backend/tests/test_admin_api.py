"""El listado de preguntas del panel: pase, filtros y paginación.

El token se fija con `monkeypatch` y no se toma de `.env`: un test no debe
depender de qué valor de desarrollo tenga la máquina.
"""

from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import ContentItem, ContentSolution, Question
from app.services import importer
from app.services.question_bank import candidates

from .factories import content_item, content_solution

ADMIN_TOKEN = "token-de-prueba"
_AUTH = {"X-Admin-Token": ADMIN_TOKEN}


@pytest.fixture(autouse=True)
def _admin_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "admin_token", ADMIN_TOKEN)


def _content(
    session: AsyncSession,
    *,
    created_at: datetime,
    prompt: str = "¿Cuál es el río más largo?",
    options: list[str] | None = None,
    correct_index: int = 1,
    explanation: str | None = None,
    category: str | None = None,
    **overrides: object,
) -> ContentItem:
    """Un ítem con su solución; el panel ahora lista las tablas genéricas."""
    if category is not None:
        overrides["categories"] = [category]
    item = content_item(
        created_at=created_at,
        payload={
            "v": 1,
            "prompt": prompt,
            "options": options or ["Paraná", "Amazonas", "Orinoco", "Magdalena"],
            "media": {"type": "none", "url": None},
        },
        **overrides,
    )
    session.add(item)
    session.add(
        content_solution(
            item.id,
            payload={
                "v": 1,
                "correct_index": correct_index,
                "explanation": explanation,
            },
        )
    )
    return item


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
    vieja = _content(session, created_at=ahora - timedelta(hours=2), prompt="Vieja")
    media = _content(session, created_at=ahora - timedelta(hours=1), prompt="Media")
    nueva = _content(session, created_at=ahora, prompt="Nueva")
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
    _content(
        session,
        created_at=ahora,
        status="draft",
        category="geography",
        difficulty=1,
        prompt="¿Cuál es la capital de Francia?",
    )
    _content(
        session,
        created_at=ahora,
        status="published",
        category="history",
        difficulty=3,
        prompt="¿Quién pintó el Guernica?",
    )
    _content(
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
    _content(
        session,
        created_at=ahora - timedelta(minutes=1),
        prompt="El Río de la Plata",
    )
    _content(session, created_at=ahora - timedelta(minutes=2), prompt="El río Amazonas")
    _content(
        session, created_at=ahora - timedelta(minutes=3), prompt="Una montaña rusa"
    )
    _content(
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
        _content(
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
    creada = _content(
        session,
        created_at=datetime.now(UTC),
        options=["Rojo", "Verde", "Azul", "Amarillo"],
        correct_index=2,
        explanation="Es el color del mar.",
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
    # `source` y `tags` eran de `questions`; el contenido genérico no los guarda.
    assert (fila["source"], fila["tags"]) == (None, [])
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


# --- import por HTTP ---------------------------------------------------------

# El encabezado del formato (§13.1), tomado de la misma fuente que el parser.
_HEADER = ",".join(importer.COLUMNS)


def _row(prompt: str, **overrides: str) -> str:
    """Una fila CSV válida; el enunciado se cambia para no chocar por `content_hash`."""
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
    } | overrides
    return ",".join(valores[columna] for columna in importer.COLUMNS)


def _csv(*filas: str) -> bytes:
    return ("\n".join([_HEADER, *filas]) + "\n").encode("utf-8")


def _upload(nombre: str, contenido: bytes, **campos: str) -> dict[str, object]:
    return {
        "files": {"file": (nombre, contenido, "application/octet-stream")},
        "data": campos,
    }


async def test_the_import_without_the_header_is_forbidden(
    client: httpx.AsyncClient,
) -> None:
    respuesta = await client.post(
        "/admin/questions/import", **_upload("q.csv", _csv(_row("Una pregunta")))
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "ADMIN_REQUIRED"


async def test_the_report_counts_imported_duplicated_and_rejected(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    contenido = _csv(
        _row("¿Cuál es el río más largo de Chile?"),
        _row("¿Cuál es el río más largo de Perú?"),
        _row("¿Cuál es el río más largo de Chile?"),  # duplicada de la línea 2
        _row("Pregunta mala", category="cinema"),  # rechazada
    )

    respuesta = await client.post(
        "/admin/questions/import", headers=_AUTH, **_upload("q.csv", contenido)
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "total": 4,
        "imported": 2,
        "duplicated": 1,
        "rejected": [{"row": 5, "reason": "categoría desconocida: 'cinema'"}],
    }
    guardadas = (
        await session.execute(
            select(ContentItem.payload["prompt"].astext).where(
                ContentItem.status == "draft"
            )
        )
    ).scalars()
    assert sorted(guardadas) == [
        "¿Cuál es el río más largo de Chile?",
        "¿Cuál es el río más largo de Perú?",
    ]


async def test_a_published_import_lands_in_the_bank(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    respuesta = await client.post(
        "/admin/questions/import",
        headers=_AUTH,
        **_upload(
            "q.csv",
            _csv(_row("¿Cuál es el río más largo del mundo?")),
            status="published",
        ),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["imported"] == 1
    assert [c.category for c in await candidates(session)] == ["geography"]


async def test_json_is_imported_like_csv(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    contenido = (
        '[{"category": "history", "difficulty": "3", "prompt": "¿Quién pintó el'
        ' Guernica?", "option_a": "Dalí", "option_b": "Picasso", "option_c": "Miró",'
        ' "option_d": "Goya", "correct": "B", "explanation": "", "source": "manual",'
        ' "tags": ["arte"]}]'
    ).encode()

    respuesta = await client.post(
        "/admin/questions/import",
        headers=_AUTH,
        **_upload("q.json", contenido, status="published"),
    )

    assert respuesta.json() == {
        "total": 1,
        "imported": 1,
        "duplicated": 0,
        "rejected": [],
    }
    fila = (await session.execute(select(ContentItem))).scalar_one()
    assert (fila.categories, fila.status) == (["history"], "published")


async def test_importing_the_same_file_twice_is_duplicated_the_second_time(
    client: httpx.AsyncClient,
) -> None:
    carga = _upload("q.csv", _csv(_row("¿Cuántos lados tiene un triángulo?")))

    await client.post("/admin/questions/import", headers=_AUTH, **carga)
    segunda = await client.post("/admin/questions/import", headers=_AUTH, **carga)

    assert segunda.json() == {
        "total": 1,
        "imported": 0,
        "duplicated": 1,
        "rejected": [],
    }


async def test_a_bom_from_excel_does_not_break_the_header(
    client: httpx.AsyncClient,
) -> None:
    contenido = (
        "\ufeff" + _HEADER + "\n" + _row("¿Cuántos continentes hay?") + "\n"
    ).encode("utf-8")

    respuesta = await client.post(
        "/admin/questions/import", headers=_AUTH, **_upload("q.csv", contenido)
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["imported"] == 1


@pytest.mark.parametrize(
    ("nombre", "contenido", "motivo"),
    [
        ("preguntas.txt", _csv(_row("Pregunta")), "no sé leer"),
        ("preguntas.csv", b"category,difficulty\ngeography,2\n", "faltan"),
        ("preguntas.json", b"[{", "JSON inválido"),
        ("preguntas.json", b'{"category": "geography"}', "array de objetos"),
    ],
)
async def test_a_broken_file_is_a_format_error(
    client: httpx.AsyncClient, nombre: str, contenido: bytes, motivo: str
) -> None:
    respuesta = await client.post(
        "/admin/questions/import", headers=_AUTH, **_upload(nombre, contenido)
    )

    assert respuesta.status_code == 400, nombre
    cuerpo = respuesta.json()["error"]
    assert cuerpo["code"] == "IMPORT_FORMAT"
    assert motivo in cuerpo["message"]


async def test_a_file_that_is_not_utf8_is_rejected_with_a_reason(
    client: httpx.AsyncClient,
) -> None:
    respuesta = await client.post(
        "/admin/questions/import",
        headers=_AUTH,
        **_upload("q.csv", _HEADER.encode("latin-1") + b"\n\xff\xfe\n"),
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["error"]["code"] == "IMPORT_FORMAT"
    assert "UTF-8" in respuesta.json()["error"]["message"]


async def test_a_bad_status_is_a_validation_error(
    client: httpx.AsyncClient,
) -> None:
    respuesta = await client.post(
        "/admin/questions/import",
        headers=_AUTH,
        **_upload("q.csv", _csv(_row("Pregunta")), status="deleted"),
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "VALIDATION_ERROR"


# --- rutas genéricas ---------------------------------------------------------


async def test_the_content_route_returns_the_same_page_as_questions(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    _content(session, created_at=datetime.now(UTC), prompt="La misma pregunta")
    await session.flush()

    historica = (await client.get("/admin/questions", headers=_AUTH)).json()
    generica = (await client.get("/admin/content/quiz", headers=_AUTH)).json()

    assert generica == historica


async def test_an_unknown_kind_is_a_validation_error(
    client: httpx.AsyncClient,
) -> None:
    respuesta = await client.get("/admin/content/rosco", headers=_AUTH)

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "rosco" in respuesta.json()["error"]["message"]


async def test_importing_an_unknown_kind_is_a_validation_error(
    client: httpx.AsyncClient,
) -> None:
    respuesta = await client.post(
        "/admin/content/rosco",
        headers=_AUTH,
        **_upload("q.csv", _csv(_row("Pregunta"))),
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    "ruta",
    ["/admin/content/quiz", "/admin/content/quiz/import", "/admin/questions/import"],
)
async def test_importing_through_any_route_writes_only_the_generic_tables(
    client: httpx.AsyncClient, session: AsyncSession, ruta: str
) -> None:
    respuesta = await client.post(
        ruta,
        headers=_AUTH,
        **_upload("q.csv", _csv(_row("¿Cuántos lados tiene un cuadrado?"))),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["imported"] == 1
    item = (await session.execute(select(ContentItem))).scalar_one()
    assert item.kind == "quiz"
    assert await session.get(ContentSolution, item.id) is not None
    # La tabla vieja quedó de solo lectura: la importación no la toca.
    assert (await session.execute(select(Question))).scalars().all() == []
