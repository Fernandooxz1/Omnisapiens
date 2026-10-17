"""Selección de preguntas como función pura sobre un pool de candidatas.

Quien llama decide de dónde salen las candidatas (Postgres o memoria), qué ids
están prohibidos, y pasa un Random con semilla si necesita reproducibilidad.
"""

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from enum import StrEnum
from random import Random

from app.game.constants import CATEGORIES, DIFFICULTY_MAX, DIFFICULTY_MIN


class NoQuestionsAvailable(Exception):
    """El pool llegó vacío: no hay banco de preguntas cargado."""


class SelectionStrategy(StrEnum):
    TARGET = "target"
    NEARBY_DIFFICULTY = "nearby_difficulty"
    ANY_CATEGORY = "any_category"
    FALLBACK = "fallback"
    REPEAT = "repeat"


@dataclass(frozen=True)
class Candidate:
    question_id: str
    category: str
    difficulty: int

    def __post_init__(self) -> None:
        if not self.question_id:
            raise ValueError("question_id vacío")
        if self.category not in CATEGORIES:
            raise ValueError(f"categoría desconocida: {self.category}")
        if not DIFFICULTY_MIN <= self.difficulty <= DIFFICULTY_MAX:
            raise ValueError(f"dificultad fuera de rango: {self.difficulty}")


@dataclass(frozen=True)
class Selection:
    question_id: str
    strategy: SelectionStrategy


def _pick(
    pool: Sequence[Candidate], strategy: SelectionStrategy, rng: Random
) -> Selection:
    # Ordenar por id hace que el resultado no dependa del orden en que llegó el pool.
    winner = rng.choice(sorted(pool, key=lambda candidate: candidate.question_id))
    return Selection(question_id=winner.question_id, strategy=strategy)


def select(
    candidates: Sequence[Candidate],
    *,
    category: str,
    difficulty: int,
    rng: Random,
    excluded: Collection[str] = (),
) -> Selection:
    if category not in CATEGORIES:
        raise ValueError(f"categoría desconocida: {category}")
    if not DIFFICULTY_MIN <= difficulty <= DIFFICULTY_MAX:
        raise ValueError(f"dificultad fuera de rango: {difficulty}")
    if not candidates:
        raise NoQuestionsAvailable("no hay preguntas cargadas")

    blocked = set(excluded)
    unused = [c for c in candidates if c.question_id not in blocked]

    target = [
        c for c in unused if c.category == category and c.difficulty == difficulty
    ]
    if target:
        return _pick(target, SelectionStrategy.TARGET, rng)

    nearby = [
        c
        for c in unused
        if c.category == category and abs(c.difficulty - difficulty) <= 1
    ]
    if nearby:
        return _pick(nearby, SelectionStrategy.NEARBY_DIFFICULTY, rng)

    any_category = [c for c in unused if abs(c.difficulty - difficulty) <= 1]
    if any_category:
        return _pick(any_category, SelectionStrategy.ANY_CATEGORY, rng)

    if unused:
        return _pick(unused, SelectionStrategy.FALLBACK, rng)

    return _pick(candidates, SelectionStrategy.REPEAT, rng)
