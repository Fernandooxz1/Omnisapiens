"""El importador: parseo, validación y hash sin base, y carga contra Postgres real.

Los tests de la mitad pura van sin fixtures: si validar un enunciado necesitara
una base, la validación estaría en el lugar equivocado. Los de la mitad con base
usan la `session` del conftest, así la carga entra en la transacción del test.
"""

import hashlib
from collections import Counter
from pathlib import Path
from typing import cast

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cli import SEED_FILE
from app.game.constants import CATEGORIES
from app.game.modes.quiz import QUIZ
from app.models import ContentItem, ContentSolution, Question
from app.services import importer
from app.services.importer import (
    ImportFormatError,
    RawRow,
    content_hash,
    normalize_prompt,
)
from app.services.question_bank import candidates, load

from .constraints import acepta
from .factories import content_item


def fila(**overrides: object) -> dict[str, object]:
    """Una fila cruda válida, con overrides; la base de los tests de validación."""
    base: dict[str, object] = {
        "category": "geography",
        "difficulty": "2",
        "prompt": "¿Cuál es el río más largo?",
        "option_a": "Paraná",
        "option_b": "Amazonas",
        "option_c": "Orinoco",
        "option_d": "Magdalena",
        "correct": "B",
        "explanation": "El Amazonas.",
        "source": "manual",
        "tags": "mundo;ríos",
    }
    return base | overrides


# --- normalización y hash ---------------------------------------------------


def test_normalize_drops_accents_punctuation_and_extra_spaces() -> None:
    assert normalize_prompt("  ¿Cuál   es el RÍO?  ") == "cual es el rio"


def test_the_same_prompt_with_and_without_accents_collides() -> None:
    assert content_hash("¿Cuál es el río?") == content_hash("Cual es el rio")


def test_different_prompts_do_not_collide() -> None:
    assert content_hash("¿Cuál es el río?") != content_hash("¿Cuál es el lago?")


def test_content_hash_is_sha256_of_the_normalized_prompt() -> None:
    esperado = hashlib.sha256(b"cual es el rio").hexdigest()
    assert content_hash("¿Cuál es el río?") == esperado


# --- validación de una fila --------------------------------------------------


def test_a_valid_row_is_parsed() -> None:
    draft = QUIZ.parse_row(fila())

    assert draft.categories == ("geography",)
    assert draft.difficulty == 2
    assert draft.public.payload["options"] == [
        "Paraná",
        "Amazonas",
        "Orinoco",
        "Magdalena",
    ]
    assert draft.solution.payload["correct_index"] == 1
    assert draft.solution.payload["explanation"] == "El Amazonas."


def test_options_are_kept_as_written() -> None:
    draft = QUIZ.parse_row(fila(option_a="Ñandú"))
    opciones = cast("list[str]", draft.public.payload["options"])
    assert opciones[0] == "Ñandú"


@pytest.mark.parametrize(
    ("overrides", "motivo"),
    [
        ({"category": "futbol"}, "categoría desconocida"),
        ({"category": ""}, "falta la categoría"),
        ({"difficulty": "x"}, "no es un número"),
        ({"difficulty": "0"}, "fuera de 1-5"),
        ({"difficulty": "6"}, "fuera de 1-5"),
        ({"prompt": "   "}, "enunciado está vacío"),
        ({"prompt": "a" * 301}, "máximo 300"),
        ({"option_c": ""}, "opción C está vacía"),
        ({"option_b": "paraná"}, "opciones repetidas"),
        ({"correct": "E"}, "debe ser A, B, C o D"),
    ],
)
def test_invalid_rows_are_rejected_with_a_reason(
    overrides: dict[str, object], motivo: str
) -> None:
    with pytest.raises(importer.RowError, match=motivo):
        QUIZ.parse_row(fila(**overrides))


# --- parseo de archivos ------------------------------------------------------


def test_csv_is_read_by_name_and_numbered_by_line() -> None:
    texto = (
        "difficulty,correct,prompt,option_a,option_b,option_c,option_d,"
        "category,explanation,source,tags\n"
        "2,B,¿Río?,Paraná,Amazonas,Orinoco,Magdalena,geography,,manual,\n"
    )
    filas = importer.parse_csv(texto)
    assert filas[0].position == 2  # la línea 1 es el encabezado
    assert filas[0].values["category"] == "geography"


def test_csv_with_a_missing_column_is_a_format_error() -> None:
    with pytest.raises(ImportFormatError, match="faltan"):
        importer.parse_csv("category,difficulty\ngeography,2\n")


def test_csv_with_an_extra_column_is_a_format_error() -> None:
    encabezado = ",".join(importer.COLUMNS) + ",spam"
    with pytest.raises(ImportFormatError, match="sobran"):
        importer.parse_csv(f"{encabezado}\n")


def test_json_must_be_an_array_of_objects() -> None:
    with pytest.raises(ImportFormatError, match="array de objetos"):
        importer.parse_json('{"category": "geography"}')
    with pytest.raises(ImportFormatError, match="no es un objeto"):
        importer.parse_json('["geography"]')


def test_broken_json_is_a_format_error() -> None:
    with pytest.raises(ImportFormatError, match="JSON inválido"):
        importer.parse_json("[{")


def test_unknown_extension_has_no_format() -> None:
    with pytest.raises(ImportFormatError, match="no sé leer"):
        importer.detect_format(Path("preguntas.txt"))


# --- carga contra la base ----------------------------------------------------


async def test_imports_valid_rows_and_reports_the_rest(session: AsyncSession) -> None:
    rows = [
        RawRow(2, fila()),
        RawRow(3, fila(prompt="Otra pregunta")),
        RawRow(4, fila(correct="Z")),  # rechazada
        RawRow(5, fila()),  # duplicada de la fila 2
    ]
    report = await importer.import_rows(session, rows, status="published")

    assert report.imported == 2
    assert report.duplicated == 1
    assert [(r.row, r.reason) for r in report.rejected] == [
        (4, "la respuesta correcta debe ser A, B, C o D")
    ]
    assert report.total == 4


async def test_the_insert_goes_in_batches(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Con lotes de 2, cinco filas son tres INSERT de contenido: prueba el bucle
    # sin cargar 500. Lo que se cuenta es el INSERT contra `content_items`.
    monkeypatch.setattr(importer, "INSERT_BATCH", 2)
    ejecutadas: list[object] = []
    original = session.execute

    async def espia(*args: object, **kwargs: object):
        ejecutadas.append(args[0])
        return await original(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(session, "execute", espia)
    rows = [RawRow(n, fila(prompt=f"Pregunta número {n}")) for n in range(2, 7)]

    report = await importer.import_rows(session, rows, status="published")

    insert_content = [
        sentencia
        for sentencia in ejecutadas
        if getattr(getattr(sentencia, "table", None), "name", None) == "content_items"
    ]
    assert report.imported == 5
    assert len(insert_content) == 3


async def test_imported_questions_are_playable_when_published(
    session: AsyncSession,
) -> None:
    await importer.import_rows(session, [RawRow(2, fila())], status="published")

    (candidata,) = await candidates(session)
    assert candidata.category == "geography"
    cargada = await load(session, candidata.question_id)
    assert cargada is not None
    assert cargada.question.prompt == "¿Cuál es el río más largo?"
    assert cargada.correct_index == 1


async def test_draft_questions_stay_out_of_the_bank(session: AsyncSession) -> None:
    await importer.import_rows(session, [RawRow(2, fila())], status="draft")

    assert await candidates(session) == []


async def test_an_existing_hash_is_reported_as_duplicated(
    session: AsyncSession,
) -> None:
    # Un contenido ya en la base cuyo hash coincide con la fila que vamos a cargar.
    await acepta(
        session,
        content_item(content_hash=content_hash("¿Cuál es el río más largo?")),
    )

    report = await importer.import_rows(session, [RawRow(2, fila())])
    assert report.imported == 0
    assert report.duplicated == 1
    # Ni el contenido ni la tabla vieja crecen: no hay dual-write que acompañe.
    assert await _count(session, ContentItem) == 1
    assert await _count(session, Question) == 0


async def test_importing_the_seed_file_loads_all_the_questions(
    session: AsyncSession,
) -> None:
    report = await importer.import_file(session, SEED_FILE, status="published")

    assert report.imported == 120
    assert report.rejected == []
    assert report.duplicated == 0

    filas = await session.execute(select(ContentItem.categories))
    categorias = {categoria for (cats,) in filas for categoria in cats}
    assert categorias == set(CATEGORIES)


async def test_the_seed_file_keeps_medium_and_hard_questions_in_every_category(
    session: AsyncSession,
) -> None:
    await importer.import_file(session, SEED_FILE, status="published")

    filas = await session.execute(
        select(ContentItem.categories, ContentItem.difficulty)
    )
    counts = Counter((cats[0], dificultad) for cats, dificultad in filas)

    for categoria in CATEGORIES:
        for dificultad in (3, 4, 5):
            assert counts[(categoria, dificultad)] >= 3, (
                f"{categoria} tiene solo {counts[(categoria, dificultad)]} "
                f"preguntas de dificultad {dificultad}"
            )
        duras = counts[(categoria, 4)] + counts[(categoria, 5)]
        assert duras >= 6, f"{categoria} tiene solo {duras} preguntas difíciles"


async def test_running_the_seed_twice_imports_nothing_the_second_time(
    session: AsyncSession,
) -> None:
    await importer.import_file(session, SEED_FILE, status="published")
    segunda = await importer.import_file(session, SEED_FILE, status="published")

    assert segunda.imported == 0
    assert segunda.duplicated == 120
    assert len(await candidates(session)) == 120


# --- una sola escritura ------------------------------------------------------


async def _count(session: AsyncSession, modelo: type[object]) -> int:
    return await session.scalar(select(func.count()).select_from(modelo)) or 0


async def test_the_seed_lands_only_in_the_generic_tables(
    session: AsyncSession,
) -> None:
    await importer.import_file(session, SEED_FILE, status="published")

    items = (await session.execute(select(ContentItem))).scalars().all()
    soluciones = (await session.execute(select(ContentSolution))).scalars().all()

    assert len(items) == 120
    assert {item.id for item in items} == {
        solucion.content_id for solucion in soluciones
    }
    for item in items:
        assert item.kind == "quiz"
        assert item.schema_version == 1
        assert item.status == "published"
        assert item.payload["v"] == 1
        assert len(item.categories) == 1
        solucion = await session.get(ContentSolution, item.id)
        assert solucion is not None
        assert solucion.payload["correct_index"] in range(4)
    # La tabla vieja queda de solo lectura: el importador ya no la escribe.
    assert await _count(session, Question) == 0


async def test_running_the_seed_twice_does_not_grow_either_table(
    session: AsyncSession,
) -> None:
    await importer.import_file(session, SEED_FILE, status="published")
    await importer.import_file(session, SEED_FILE, status="published")

    assert await _count(session, ContentItem) == 120
    assert await _count(session, ContentSolution) == 120
    assert await _count(session, Question) == 0


async def test_a_rejected_row_writes_nothing_to_any_table(
    session: AsyncSession,
) -> None:
    report = await importer.import_rows(
        session, [RawRow(2, fila(correct="Z"))], status="published"
    )

    assert [fila.reason for fila in report.rejected] == [
        "la respuesta correcta debe ser A, B, C o D"
    ]
    assert await _count(session, ContentItem) == 0
    assert await _count(session, ContentSolution) == 0
    assert await _count(session, Question) == 0
