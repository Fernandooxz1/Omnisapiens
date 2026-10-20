"""El formato arcade y el modo registrado `trivia_arcade`.

Los números son del formato, no del motor: `solo_engine` los aplica sin
conocerlos. La progresión y el puntaje de este módulo traducen esas curvas al
contrato de `modes.base`; el catálogo es la única lista de modos.
"""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from app.game.constants import (
    ARCADE_DIFFICULTY_TIERS,
    ARCADE_LIVES,
    ARCADE_SECONDS_FLOOR,
    ARCADE_SECONDS_START,
    ARCADE_SECONDS_STEP_EVERY,
    ARCADE_STREAK_BONUS_MAX,
    ARCADE_STREAK_BONUS_STEP,
)
from app.game.core import Verdict
from app.game.modes.base import (
    ConnectionPolicy,
    GameMode,
    Players,
    RankingPolicy,
    Schedule,
    SessionState,
    Step,
)
from app.game.modes.quiz import QUIZ, QUIZ_RULES, QuizPayload
from app.game.scoring import round_points
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


class ArcadeConfig(BaseModel):
    """La corrida arcade no tiene parámetros: sus reglas son fijas."""

    model_config = ConfigDict(extra="forbid")


@dataclass(frozen=True)
class ArcadeProgression:
    """Las curvas del arcade: dificultad y segundos por aciertos."""

    rules: SoloRules

    def next(self, state: SessionState, format: str) -> Step:
        return Step(
            difficulty=self.rules.difficulty_for(state.correct_count),
            seconds=self.rules.seconds_for(state.correct_count),
            finished=state.finished,
        )


@dataclass(frozen=True)
class ArcadeScoring:
    """Puntos de ronda con el bonus de racha del formato arcade."""

    rules: SoloRules

    def points(
        self,
        verdict: Verdict[object],
        elapsed_ms: int,
        seconds: int,
        state: SessionState,
    ) -> int:
        if not verdict.correct:
            return 0
        return round_points(
            correct=True, elapsed_ms=elapsed_ms, total_seconds=seconds
        ) + self.rules.streak_bonus(state.streak)


TRIVIA_ARCADE = GameMode(
    code="trivia_arcade",
    name="Arcade",
    content_kind=QUIZ.code,
    play_format="arcade",
    ruleset_version=1,
    content=QUIZ,
    rules=QUIZ_RULES,
    progression=ArcadeProgression(ARCADE_RULES),
    scoring=ArcadeScoring(ARCADE_RULES),
    config_schema=ArcadeConfig,
    public_schema=QuizPayload,
    input="choice",
    media=("none", "image", "audio"),
    ranking=RankingPolicy(),
    players=Players.SOLO,
    connection=ConnectionPolicy.EPHEMERAL,
    schedule=Schedule.LINEAR,
    solo_rules=ARCADE_RULES,
)

__all__ = [
    "ARCADE_RULES",
    "TRIVIA_ARCADE",
    "ArcadeConfig",
    "ArcadeProgression",
    "ArcadeScoring",
]
