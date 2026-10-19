"""Motor puro de una corrida de un jugador.

El formato aporta sus curvas (`SoloRules`); el motor solo las aplica: vidas,
racha, dificultad, segundos y fin de corrida. El historial no vive en el estado:
cada `resolve` devuelve el registro de la ronda para que la capa de arriba lo
persista y el estado quede chico.
"""

from dataclasses import dataclass, replace
from enum import StrEnum
from itertools import pairwise

from app.game.answers import Answer, RejectReason, ServedQuestion, settle
from app.game.constants import CHOICES, DIFFICULTY_MAX, DIFFICULTY_MIN
from app.game.errors import InvalidTransition
from app.game.scoring import round_points


class RunStatus(StrEnum):
    PLAYING = "playing"
    FINISHED = "finished"


@dataclass(frozen=True)
class SoloRules:
    """Las curvas de un formato solo.

    Sin defaults a propósito: cada formato fija sus valores y el motor no
    esconde números del arcade.
    """

    lives: int
    # El índice es (dificultad - 1): aciertos mínimos para llegar a cada nivel.
    difficulty_tiers: tuple[int, ...]
    seconds_start: int
    seconds_floor: int
    seconds_step_every: int
    streak_bonus_step: int
    streak_bonus_max: int

    def __post_init__(self) -> None:
        if self.lives <= 0:
            raise ValueError(f"lives debe ser positivo: {self.lives}")
        if not self.difficulty_tiers:
            raise ValueError("difficulty_tiers no puede estar vacío")
        if self.difficulty_tiers[0] != 0:
            raise ValueError("difficulty_tiers debe empezar en 0")
        if len(self.difficulty_tiers) > DIFFICULTY_MAX - DIFFICULTY_MIN + 1:
            raise ValueError("difficulty_tiers supera la dificultad máxima")
        if any(low >= high for low, high in pairwise(self.difficulty_tiers)):
            raise ValueError("difficulty_tiers debe ser creciente")
        if self.seconds_start <= 0:
            raise ValueError(f"seconds_start debe ser positivo: {self.seconds_start}")
        if self.seconds_floor <= 0:
            raise ValueError(f"seconds_floor debe ser positivo: {self.seconds_floor}")
        if self.seconds_floor > self.seconds_start:
            raise ValueError("seconds_floor no puede superar seconds_start")
        if self.seconds_step_every <= 0:
            raise ValueError(
                f"seconds_step_every debe ser positivo: {self.seconds_step_every}"
            )
        if self.streak_bonus_step < 0:
            raise ValueError("streak_bonus_step no puede ser negativo")
        if self.streak_bonus_max < 0:
            raise ValueError("streak_bonus_max no puede ser negativo")

    def difficulty_for(self, correct_count: int) -> int:
        if correct_count < 0:
            raise ValueError(f"correct_count negativo: {correct_count}")

        level = DIFFICULTY_MIN
        for index, threshold in enumerate(self.difficulty_tiers):
            if correct_count >= threshold:
                level = index + DIFFICULTY_MIN
        return level

    def seconds_for(self, correct_count: int) -> int:
        if correct_count < 0:
            raise ValueError(f"correct_count negativo: {correct_count}")

        return max(
            self.seconds_floor,
            self.seconds_start - correct_count // self.seconds_step_every,
        )

    def streak_bonus(self, streak: int) -> int:
        """streak = aciertos consecutivos *antes* de esta pregunta."""
        if streak < 0:
            raise ValueError(f"streak no puede ser negativo: {streak}")

        return min(self.streak_bonus_step * streak, self.streak_bonus_max)


@dataclass(frozen=True)
class SoloRun:
    rules: SoloRules
    lives: int
    round_index: int = 0
    score: int = 0
    streak: int = 0
    correct_count: int = 0
    longest_streak: int = 0
    max_difficulty: int = DIFFICULTY_MIN
    status: RunStatus = RunStatus.PLAYING

    def __post_init__(self) -> None:
        if self.round_index < 0:
            raise ValueError(f"round_index negativo: {self.round_index}")
        if self.score < 0:
            raise ValueError(f"score negativo: {self.score}")
        if not 0 <= self.lives <= self.rules.lives:
            raise ValueError(f"lives fuera de rango: {self.lives}")
        if not 0 <= self.streak <= self.correct_count:
            raise ValueError("streak no puede superar correct_count")
        if not self.streak <= self.longest_streak <= self.correct_count:
            raise ValueError("longest_streak debe estar entre streak y correct_count")
        if not DIFFICULTY_MIN <= self.max_difficulty <= DIFFICULTY_MAX:
            raise ValueError(f"max_difficulty fuera de rango: {self.max_difficulty}")
        if (self.status is RunStatus.PLAYING) != (self.lives > 0):
            raise ValueError("status y vidas se contradicen")

    @property
    def finished(self) -> bool:
        return self.status is RunStatus.FINISHED


@dataclass(frozen=True)
class RoundRecord:
    round_index: int
    question_id: str
    difficulty: int
    seconds: int
    # El instante en que se sirvió: el borde lo necesita para escribir
    # `served_at`/`deadline_at` sin reconstruir la ventana después.
    served_at_ms: int
    correct_index: int
    choice: int | None
    correct: bool
    elapsed_ms: int
    points: int
    rejected: RejectReason | None


@dataclass(frozen=True)
class Resolved[RunT: SoloRun]:
    record: RoundRecord
    run: RunT


@dataclass(frozen=True)
class SoloEngine:
    rules: SoloRules

    def start(self) -> SoloRun:
        return SoloRun(rules=self.rules, lives=self.rules.lives)

    def next_question(
        self, run: SoloRun, *, question_id: str, now_ms: int
    ) -> ServedQuestion:
        if run.finished:
            raise InvalidTransition("la corrida terminó: no hay pregunta siguiente")

        return ServedQuestion(
            round_index=run.round_index,
            question_id=question_id,
            difficulty=self.rules.difficulty_for(run.correct_count),
            seconds=self.rules.seconds_for(run.correct_count),
            served_at_ms=now_ms,
        )

    def resolve[RunT: SoloRun](
        self,
        run: RunT,
        served: ServedQuestion,
        *,
        correct_index: int,
        answer: Answer | None,
    ) -> Resolved[RunT]:
        if run.finished:
            raise InvalidTransition("la corrida terminó: no hay ronda que resolver")
        if served.round_index != run.round_index:
            raise InvalidTransition(
                f"se resolvió la ronda {served.round_index} "
                f"estando en la {run.round_index}"
            )
        if correct_index not in CHOICES:
            raise ValueError(f"correct_index fuera de rango: {correct_index}")

        settled = settle(served, answer, correct_index=correct_index)
        points = 0
        if settled.correct:
            points = round_points(
                correct=True,
                elapsed_ms=settled.elapsed_ms,
                total_seconds=served.seconds,
            ) + self.rules.streak_bonus(run.streak)

        if settled.correct:
            streak = run.streak + 1
            lives = run.lives
            score = run.score + points
            correct_count = run.correct_count + 1
        else:
            streak = 0
            lives = run.lives - 1
            score = run.score
            correct_count = run.correct_count

        next_run = replace(
            run,
            round_index=run.round_index + 1,
            score=score,
            lives=lives,
            streak=streak,
            correct_count=correct_count,
            longest_streak=max(run.longest_streak, streak),
            max_difficulty=max(run.max_difficulty, served.difficulty),
            status=RunStatus.FINISHED if lives == 0 else RunStatus.PLAYING,
        )

        record = RoundRecord(
            round_index=served.round_index,
            question_id=served.question_id,
            difficulty=served.difficulty,
            seconds=served.seconds,
            served_at_ms=served.served_at_ms,
            correct_index=correct_index,
            choice=settled.answer.choice if settled.answer is not None else None,
            correct=settled.correct,
            elapsed_ms=settled.elapsed_ms,
            points=points,
            rejected=settled.rejected,
        )
        return Resolved(record=record, run=next_run)
