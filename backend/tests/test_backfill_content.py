"""El backfill de `questions` a las tablas genéricas de contenido.

Contra Postgres real: lo que se prueba es el mapeo fila a fila y la
idempotencia, y las dos cosas dependen de constraints y del `ON CONFLICT`.
"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cli import SEED_FILE
from app.models import ContentItem, ContentSolution, Question
from app.services import importer
from app.services.content_backfill import backfill_quiz

from .constraints import acepta
from .factories import content_item, question

SEED_SIZE = 120


async def _conteo(session: AsyncSession, modelo: Any) -> int:
    resultado = await session.execute(select(func.count()).select_from(modelo))
    return resultado.scalar_one()


async def test_the_seed_is_fully_backfilled(session: AsyncSession) -> None:
    await importer.import_file(session, SEED_FILE, status="published")

    report = await backfill_quiz(session)

    assert report.read == SEED_SIZE
    assert report.created == SEED_SIZE
    assert report.existing == 0
    assert report.rejected == []
    assert await _conteo(session, ContentItem) == SEED_SIZE
    assert await _conteo(session, ContentSolution) == SEED_SIZE


async def test_running_it_twice_creates_nothing_the_second_time(
    session: AsyncSession,
) -> None:
    await importer.import_file(session, SEED_FILE, status="published")
    await backfill_quiz(session)

    segunda = await backfill_quiz(session)

    assert segunda.read == SEED_SIZE
    assert segunda.created == 0
    assert segunda.existing == SEED_SIZE
    assert segunda.rejected == []
    assert await _conteo(session, ContentItem) == SEED_SIZE
    assert await _conteo(session, ContentSolution) == SEED_SIZE


async def test_the_payload_and_the_solution_keep_the_question(
    session: AsyncSession,
) -> None:
    original = question(
        prompt="¿Cuál es el río más largo?",
        options=["Paraná", "Amazonas", "Orinoco", "Magdalena"],
        correct_index=1,
        explanation="El Amazonas.",
        media_type="image",
        media_url="https://x/rio.png",
        status="published",
    )
    original.content_hash = importer.content_hash(original.prompt)
    await acepta(session, original)

    await backfill_quiz(session)

    item = await session.get(ContentItem, original.id)
    assert item is not None
    assert item.id == original.id
    assert item.kind == "quiz"
    assert item.schema_version == 1
    assert item.status == "published"
    assert item.language == "es"
    assert item.difficulty == original.difficulty
    assert item.categories == [original.category]
    assert item.content_hash == original.content_hash
    assert item.media_type == "image"
    assert item.media_url == "https://x/rio.png"
    assert item.payload == {
        "v": 1,
        "prompt": "¿Cuál es el río más largo?",
        "options": ["Paraná", "Amazonas", "Orinoco", "Magdalena"],
        "media": {"type": "image", "url": "https://x/rio.png"},
    }

    solution = await session.get(ContentSolution, original.id)
    assert solution is not None
    assert solution.payload == {
        "v": 1,
        "correct_index": 1,
        "explanation": "El Amazonas.",
    }


async def test_a_hash_that_belongs_to_another_item_is_rejected(
    session: AsyncSession,
) -> None:
    original = question(prompt="Pregunta con hash tomado")
    original.content_hash = importer.content_hash(original.prompt)
    await acepta(session, original)
    await acepta(session, content_item(content_hash=original.content_hash))

    report = await backfill_quiz(session)

    assert report.read == 1
    assert report.created == 0
    assert report.existing == 0
    assert len(report.rejected) == 1
    assert report.rejected[0].content_id == original.id
    assert "content_hash" in report.rejected[0].reason
    # La pregunta vieja queda intacta: el backfill no borra `questions`.
    assert await _conteo(session, Question) == 1


async def test_an_empty_bank_is_a_noop(session: AsyncSession) -> None:
    report = await backfill_quiz(session)

    assert (report.read, report.created, report.existing, report.rejected) == (
        0,
        0,
        0,
        [],
    )
