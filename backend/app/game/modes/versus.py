"""El formato versus y el modo registrado `trivia_versus`.

La partida en vivo la gobierna `game.versus_engine`: rondas, tramos de
dificultad, gracia y revancha. Acá el modo solo declara el contrato del
catálogo: el esquema de configuración de la sala y el puntaje compartido.
"""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, field_validator

from app.game.constants import (
    DIFFICULTY_MIN,
    ONLINE_ROUNDS_OPTIONS,
    ONLINE_SECONDS_OPTIONS,
)
from app.game.core import Verdict
from app.game.modes.base import (
    ConnectionPolicy,
    GameMode,
    Players,
    Schedule,
    SessionState,
    Step,
)
from app.game.modes.quiz import QUIZ, QUIZ_RULES, QuizPayload
from app.game.scoring import round_points

DEFAULT_ROUNDS = 5
DEFAULT_SECONDS = 20


class VersusModeConfig(BaseModel):
    """Los parámetros de una partida 1v1: rondas y segundos por ronda."""

    model_config = ConfigDict(extra="forbid")

    rounds: int = DEFAULT_ROUNDS
    seconds: int = DEFAULT_SECONDS

    @field_validator("rounds")
    @classmethod
    def _rounds_permitidos(cls, valor: int) -> int:
        if valor not in ONLINE_ROUNDS_OPTIONS:
            raise ValueError(f"debe ser uno de {ONLINE_ROUNDS_OPTIONS}")
        return valor

    @field_validator("seconds")
    @classmethod
    def _seconds_permitidos(cls, valor: int) -> int:
        if valor not in ONLINE_SECONDS_OPTIONS:
            raise ValueError(f"debe ser uno de {ONLINE_SECONDS_OPTIONS}")
        return valor


@dataclass(frozen=True)
class VersusProgression:
    """Progresión declarada del versus.

    El motor del versus fija la dificultad por tramo y los segundos con el
    `config` de la partida; esta progresión describe el paso por defecto para un
    runtime lineal y no reemplaza a `VersusEngine`.
    """

    difficulty: int = DIFFICULTY_MIN
    seconds: int = DEFAULT_SECONDS

    def next(self, state: SessionState, format: str) -> Step:
        return Step(
            difficulty=self.difficulty,
            seconds=self.seconds,
            finished=state.finished,
        )


@dataclass(frozen=True)
class VersusScoring:
    """Puntos de ronda del versus: bonus de tiempo, sin racha."""

    def points(
        self,
        verdict: Verdict[object],
        elapsed_ms: int,
        seconds: int,
        state: SessionState,
    ) -> int:
        return round_points(
            correct=verdict.correct, elapsed_ms=elapsed_ms, total_seconds=seconds
        )


TRIVIA_VERSUS = GameMode(
    code="trivia_versus",
    name="1v1",
    content_kind=QUIZ.code,
    play_format="versus",
    ruleset_version=1,
    content=QUIZ,
    rules=QUIZ_RULES,
    progression=VersusProgression(),
    scoring=VersusScoring(),
    config_schema=VersusModeConfig,
    public_schema=QuizPayload,
    input="choice",
    media=("none", "image", "audio"),
    ranking=None,
    players=Players.VERSUS,
    connection=ConnectionPolicy.RESILIENT,
    schedule=Schedule.LINEAR,
)

__all__ = [
    "DEFAULT_ROUNDS",
    "DEFAULT_SECONDS",
    "TRIVIA_VERSUS",
    "VersusModeConfig",
    "VersusProgression",
    "VersusScoring",
]
