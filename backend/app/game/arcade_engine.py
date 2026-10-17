"""Motor puro de la corrida arcade.

A diferencia del 1v1, una corrida no tiene techo de rondas: el historial no vive
en el estado. Cada `resolve` devuelve el registro de la ronda para que la capa
de arriba lo persista y el estado quede chico.
"""

from dataclasses import dataclass, replace
from enum import StrEnum

from app.game.answers import Answer, RejectReason, ServedQuestion, settle
from app.game.constants import (
    ARCADE_DIFFICULTY_TIERS,
    ARCADE_LIVES,
    ARCADE_SECONDS_FLOOR,
    ARCADE_SECONDS_START,
    ARCADE_SECONDS_STEP_EVERY,
    CHOICES,
    DIFFICULTY_MAX,
    DIFFICULTY_MIN,
)
from app.game.errors import InvalidTransition
from app.game.scoring import arcade_points


class RunStatus(StrEnum):
    PLAYING = "playing"
    FINISHED = "finished"


@dataclass(frozen=True)
class RoundRecord:
    round_index: int
    question_id: str
    difficulty: int
    seconds: int
    correct_index: int
    choice: int | None
    correct: bool
    elapsed_ms: int
    points: int
    rejected: RejectReason | None


@dataclass(frozen=True)
class ArcadeRun:
    round_index: int = 0
    score: int = 0
    lives: int = ARCADE_LIVES
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
        if not 0 <= self.lives <= ARCADE_LIVES:
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
class Resolved:
    record: RoundRecord
    run: ArcadeRun


def difficulty_for(correct_count: int) -> int:
    if correct_count < 0:
        raise ValueError(f"correct_count negativo: {correct_count}")

    level = DIFFICULTY_MIN
    for index, threshold in enumerate(ARCADE_DIFFICULTY_TIERS):
        if correct_count >= threshold:
            level = index + DIFFICULTY_MIN
    return level


def seconds_for(correct_count: int) -> int:
    if correct_count < 0:
        raise ValueError(f"correct_count negativo: {correct_count}")

    return max(
        ARCADE_SECONDS_FLOOR,
        ARCADE_SECONDS_START - correct_count // ARCADE_SECONDS_STEP_EVERY,
    )


def next_question(run: ArcadeRun, *, question_id: str, now_ms: int) -> ServedQuestion:
    if run.finished:
        raise InvalidTransition("la corrida terminó: no hay pregunta siguiente")

    return ServedQuestion(
        round_index=run.round_index,
        question_id=question_id,
        difficulty=difficulty_for(run.correct_count),
        seconds=seconds_for(run.correct_count),
        served_at_ms=now_ms,
    )


def resolve(
    run: ArcadeRun,
    served: ServedQuestion,
    *,
    correct_index: int,
    answer: Answer | None,
) -> Resolved:
    if run.finished:
        raise InvalidTransition("la corrida terminó: no hay ronda que resolver")
    if served.round_index != run.round_index:
        raise InvalidTransition(
            f"se resolvió la ronda {served.round_index} estando en la {run.round_index}"
        )
    if correct_index not in CHOICES:
        raise ValueError(f"correct_index fuera de rango: {correct_index}")

    settled = settle(served, answer, correct_index=correct_index)
    points = arcade_points(
        correct=settled.correct,
        elapsed_ms=settled.elapsed_ms,
        total_seconds=served.seconds,
        streak=run.streak,
    )

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
        correct_index=correct_index,
        choice=settled.answer.choice if settled.answer is not None else None,
        correct=settled.correct,
        elapsed_ms=settled.elapsed_ms,
        points=points,
        rejected=settled.rejected,
    )
    return Resolved(record=record, run=next_run)
