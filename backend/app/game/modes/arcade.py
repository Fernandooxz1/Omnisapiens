"""El formato arcade: los valores fijos de su `ruleset_version=1`.

Los números son del formato, no del motor: `solo_engine` los aplica sin
conocerlos. La fase 6 registra en este módulo el `GameMode` `trivia_arcade`.
"""

from app.game.constants import (
    ARCADE_DIFFICULTY_TIERS,
    ARCADE_LIVES,
    ARCADE_SECONDS_FLOOR,
    ARCADE_SECONDS_START,
    ARCADE_SECONDS_STEP_EVERY,
    ARCADE_STREAK_BONUS_MAX,
    ARCADE_STREAK_BONUS_STEP,
)
from app.game.solo_engine import SoloRules

ARCADE_RULES = SoloRules(
    lives=ARCADE_LIVES,
    difficulty_tiers=ARCADE_DIFFICULTY_TIERS,
    seconds_start=ARCADE_SECONDS_START,
    seconds_floor=ARCADE_SECONDS_FLOOR,
    seconds_step_every=ARCADE_SECONDS_STEP_EVERY,
    streak_bonus_step=ARCADE_STREAK_BONUS_STEP,
    streak_bonus_max=ARCADE_STREAK_BONUS_MAX,
)

__all__ = ["ARCADE_RULES"]
