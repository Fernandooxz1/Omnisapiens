"""Elegir y cargar el próximo ítem de una sesión solo.

El store solo sirve lo que el borde le entrega: candidatas, dificultad, Redis y
carga son I/O. Este módulo junta ese camino para que el arcade viejo y el canal
canónico no repitan la misma selección con dos criterios distintos.
"""

import logging
import uuid
from random import Random

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.game.constants import CATEGORIES, DIFFICULTY_MAX, DIFFICULTY_MIN
from app.game.solo_engine import SoloRun
from app.runtime.session_store import NextQuestion
from app.services.question_bank import (
    candidates,
    load,
    remember_seen,
    seen_ids,
)
from app.services.questions import SelectionStrategy, select

logger = logging.getLogger(__name__)


async def choose_item(
    db: AsyncSession,
    redis: Redis,
    *,
    user_id: uuid.UUID,
    run: SoloRun,
    seen: frozenset[str],
    rng: Random,
) -> NextQuestion | None:
    """Elige y carga la pregunta del tramo. `None` si el banco está vacío."""
    target = run.rules.difficulty_for(run.correct_count)
    # El pool se recorta al tramo cercano; si no alcanza, se abre a todo el
    # banco antes de aceptar una repetición (H-13 y §9.4).
    pool = await candidates(
        db,
        low=max(DIFFICULTY_MIN, target - 1),
        high=min(DIFFICULTY_MAX, target + 1),
    )
    if not pool:
        pool = await candidates(db)
    if not pool:
        return None

    viewed = await seen_ids(redis, user_id)
    excluded = seen | viewed
    selection = select(
        pool,
        category=rng.choice(CATEGORIES),
        difficulty=target,
        rng=rng,
        excluded=excluded,
    )
    if selection.strategy is SelectionStrategy.REPEAT:
        wider = await candidates(db)
        if len(wider) > len(pool):
            selection = select(
                wider,
                category=rng.choice(CATEGORIES),
                difficulty=target,
                rng=rng,
                excluded=excluded,
            )

    question = await load(db, selection.question_id)
    if question is None:
        return None
    repeated = selection.strategy is SelectionStrategy.REPEAT
    if repeated:
        logger.warning(
            "la sesión de %s se quedó sin preguntas nuevas: repite",
            user_id,
        )
    # Se anota la vista antes de mandar la pregunta: si el cliente la recibe,
    # el historial ya está escrito (y si Redis falla, `remember_seen` degrada).
    await remember_seen(redis, user_id, question.question.id)
    return NextQuestion(question, repeated=repeated)


__all__ = ["choose_item"]
