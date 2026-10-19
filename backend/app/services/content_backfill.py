"""Backfill de la tabla vieja `questions` a las tablas genéricas de contenido.

Es un comando de mantenimiento, no una migración: una migración no debería
depender de datos que pueden faltar. El backfill conserva el UUID y el
`content_hash` de cada pregunta, así que se puede correr dos veces sin
duplicar nada y el `ON CONFLICT` de la base es la última red.

El payload público del quiz incluye `media` además de las columnas
`media_type`/`media_url`: las columnas son para filtrar, el payload es lo que
viaja al cliente.
"""

import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ContentItem, ContentSolution, Question

QUIZ_KIND = "quiz"
QUIZ_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class RejectedItem:
    content_id: uuid.UUID
    reason: str


@dataclass(frozen=True)
class BackfillReport:
    read: int
    created: int
    existing: int
    rejected: list[RejectedItem] = field(default_factory=list)


def _public_payload(pregunta: Question) -> dict[str, object]:
    return {
        "v": QUIZ_SCHEMA_VERSION,
        "prompt": pregunta.prompt,
        "options": pregunta.options,
        "media": {"type": pregunta.media_type, "url": pregunta.media_url},
    }


def _solution_payload(pregunta: Question) -> dict[str, object]:
    return {
        "v": QUIZ_SCHEMA_VERSION,
        "correct_index": pregunta.correct_index,
        "explanation": pregunta.explanation,
    }


async def _insert_item(session: AsyncSession, pregunta: Question) -> bool:
    """Inserta el ítem si el id no existe. Devuelve si lo creó."""
    resultado = await session.execute(
        pg_insert(ContentItem)
        .values(
            id=pregunta.id,
            kind=QUIZ_KIND,
            schema_version=QUIZ_SCHEMA_VERSION,
            status=pregunta.status,
            language=pregunta.language,
            difficulty=pregunta.difficulty,
            categories=[pregunta.category],
            payload=_public_payload(pregunta),
            media_type=pregunta.media_type,
            media_url=pregunta.media_url,
            content_hash=pregunta.content_hash,
        )
        .on_conflict_do_nothing(index_elements=["id"])
        .returning(ContentItem.id)
    )
    return resultado.scalar_one_or_none() is not None


async def _insert_solution(session: AsyncSession, pregunta: Question) -> None:
    await session.execute(
        pg_insert(ContentSolution)
        .values(content_id=pregunta.id, payload=_solution_payload(pregunta))
        .on_conflict_do_nothing(index_elements=["content_id"])
    )


async def backfill_quiz(session: AsyncSession) -> BackfillReport:
    """Copia cada `questions` a `content_items(kind='quiz')` + `content_solutions`.

    No borra la tabla vieja. Un `content_hash` que ya pertenece a otro ítem se
    informa como rechazado en vez de reventar el comando: la base lo prohíbe
    (es UNIQUE) y adivinar qué fila gana sería peor.
    """
    existentes = await session.execute(select(ContentItem.id, ContentItem.content_hash))
    ids_existentes: set[uuid.UUID] = set()
    hashes_existentes: set[str] = set()
    for content_id, content_hash in existentes.all():
        ids_existentes.add(content_id)
        hashes_existentes.add(content_hash)

    preguntas = (
        await session.execute(select(Question).order_by(Question.id))
    ).scalars()
    leidas = creadas = existentes_count = 0
    rechazadas: list[RejectedItem] = []

    for pregunta in preguntas:
        leidas += 1
        if pregunta.id in ids_existentes:
            # Un backfill anterior pudo cortarse entre el ítem y su solución.
            await _insert_solution(session, pregunta)
            existentes_count += 1
            continue
        if pregunta.content_hash in hashes_existentes:
            rechazadas.append(
                RejectedItem(
                    pregunta.id,
                    f"el content_hash ya pertenece a otro ítem "
                    f"({pregunta.content_hash})",
                )
            )
            continue

        if not await _insert_item(session, pregunta):
            existentes_count += 1
            continue
        await _insert_solution(session, pregunta)
        ids_existentes.add(pregunta.id)
        hashes_existentes.add(pregunta.content_hash)
        creadas += 1

    return BackfillReport(
        read=leidas,
        created=creadas,
        existing=existentes_count,
        rejected=rechazadas,
    )
