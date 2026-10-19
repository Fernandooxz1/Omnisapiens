"""El formato arcade: sus valores y la fachada sobre el motor solo.

Hasta la fase 4, el arcade sigue siendo la implementación de referencia y estos
nombres son el contrato que usan el WebSocket, los servicios y los tests. Los
números viven acá, que es el formato, no en `solo_engine`, que es el motor.
"""

from dataclasses import dataclass

from app.game.answers import Answer, ServedQuestion
from app.game.constants import (
    ARCADE_DIFFICULTY_TIERS,
    ARCADE_LIVES,
    ARCADE_SECONDS_FLOOR,
    ARCADE_SECONDS_START,
    ARCADE_SECONDS_STEP_EVERY,
    ARCADE_STREAK_BONUS_MAX,
    ARCADE_STREAK_BONUS_STEP,
)
from app.game.solo_engine import (
    Resolved,
    RoundRecord,
    RunStatus,
    SoloEngine,
    SoloRules,
    SoloRun,
)

__all__ = [
    "ARCADE_ENGINE",
    "ARCADE_RULES",
    "ArcadeRun",
    "Resolved",
    "RoundRecord",
    "RunStatus",
    "SoloEngine",
    "SoloRules",
    "difficulty_for",
    "next_question",
    "resolve",
    "seconds_for",
]

ARCADE_RULES = SoloRules(
    lives=ARCADE_LIVES,
    difficulty_tiers=ARCADE_DIFFICULTY_TIERS,
    seconds_start=ARCADE_SECONDS_START,
    seconds_floor=ARCADE_SECONDS_FLOOR,
    seconds_step_every=ARCADE_SECONDS_STEP_EVERY,
    streak_bonus_step=ARCADE_STREAK_BONUS_STEP,
    streak_bonus_max=ARCADE_STREAK_BONUS_MAX,
)

ARCADE_ENGINE = SoloEngine(ARCADE_RULES)


@dataclass(frozen=True)
class ArcadeRun(SoloRun):
    """La corrida arcade con sus reglas fijas.

    El motor es genérico, pero el arcade de producción todavía espera este tipo:
    se conserva hasta el port de la fase 4.
    """

    rules: SoloRules = ARCADE_RULES
    lives: int = ARCADE_LIVES


def difficulty_for(correct_count: int) -> int:
    return ARCADE_RULES.difficulty_for(correct_count)


def seconds_for(correct_count: int) -> int:
    return ARCADE_RULES.seconds_for(correct_count)


def next_question(run: SoloRun, *, question_id: str, now_ms: int) -> ServedQuestion:
    return ARCADE_ENGINE.next_question(run, question_id=question_id, now_ms=now_ms)


def resolve[RunT: SoloRun](
    run: RunT,
    served: ServedQuestion,
    *,
    correct_index: int,
    answer: Answer | None,
) -> Resolved[RunT]:
    return ARCADE_ENGINE.resolve(
        run, served, correct_index=correct_index, answer=answer
    )
