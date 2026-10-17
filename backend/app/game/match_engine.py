"""Motor puro de la partida 1v1.

El estado es el historial completo de rondas: marcador, ronda actual y desempate
se derivan de él. Con 7 rondas como máximo el costo es nulo, y así los
contadores no pueden desincronizarse del historial.
"""

from dataclasses import dataclass, replace
from enum import StrEnum

from app.game.answers import Answer, RejectReason, ServedQuestion, settle
from app.game.constants import CHOICES, ONLINE_ROUNDS_OPTIONS, ONLINE_SECONDS_OPTIONS
from app.game.errors import InvalidTransition
from app.game.scoring import round_points

# (última ronda del tramo, dificultad mínima, dificultad máxima)
_DIFFICULTY_BY_ROUND = ((1, 1, 2), (3, 2, 3), (5, 3, 4))
_TIEBREAK_DIFFICULTY = (4, 5)


class Player(StrEnum):
    A = "a"
    B = "b"


class MatchStatus(StrEnum):
    PLAYING = "playing"
    FINISHED = "finished"
    ABANDONED = "abandoned"
    VOID = "void"


@dataclass(frozen=True)
class MatchConfig:
    rounds: int
    seconds: int

    def __post_init__(self) -> None:
        if self.rounds not in ONLINE_ROUNDS_OPTIONS:
            raise ValueError(f"rounds no permitido: {self.rounds}")
        if self.seconds not in ONLINE_SECONDS_OPTIONS:
            raise ValueError(f"seconds no permitido: {self.seconds}")


@dataclass(frozen=True)
class RoundRecord:
    round_index: int
    question_id: str
    difficulty: int
    seconds: int
    correct_index: int
    a_choice: int | None
    b_choice: int | None
    a_ms: int | None
    b_ms: int | None
    a_correct: bool
    b_correct: bool
    a_points: int
    b_points: int
    a_rejected: RejectReason | None
    b_rejected: RejectReason | None


@dataclass(frozen=True)
class MatchState:
    """El historial de rondas es la única fuente de verdad: marcador y contadores
    se derivan de él, así que no pueden desincronizarse."""

    config: MatchConfig
    rounds: tuple[RoundRecord, ...] = ()
    status: MatchStatus = MatchStatus.PLAYING
    winner: Player | None = None

    def __post_init__(self) -> None:
        if tuple(record.round_index for record in self.rounds) != tuple(
            range(len(self.rounds))
        ):
            raise ValueError("las rondas deben ser consecutivas desde 0")

        if self.status is MatchStatus.PLAYING:
            if self.winner is not None:
                raise ValueError("una partida en curso no tiene ganador")
            if self.in_tiebreak and self.score_a != self.score_b:
                raise ValueError(
                    "con las rondas agotadas y marcador distinto, debe estar terminada"
                )
        elif self.status is MatchStatus.VOID:
            if self.winner is not None:
                raise ValueError("una partida anulada no tiene ganador")
        else:
            if self.winner is None:
                raise ValueError(f"una partida {self.status} necesita ganador")
            if self.in_tiebreak and self.score_a == self.score_b:
                raise ValueError("una partida terminada no puede quedar empatada")

    @property
    def score_a(self) -> int:
        return sum(record.a_points for record in self.rounds)

    @property
    def score_b(self) -> int:
        return sum(record.b_points for record in self.rounds)

    @property
    def round_index(self) -> int:
        return len(self.rounds)

    @property
    def in_tiebreak(self) -> bool:
        return self.round_index >= self.config.rounds

    @property
    def seconds_per_round(self) -> int:
        return self.config.seconds // 2 if self.in_tiebreak else self.config.seconds


@dataclass(frozen=True)
class Resolved:
    record: RoundRecord
    state: MatchState


def difficulty_range(state: MatchState) -> tuple[int, int]:
    if state.in_tiebreak:
        return _TIEBREAK_DIFFICULTY

    for last_round, low, high in _DIFFICULTY_BY_ROUND:
        if state.round_index <= last_round:
            return low, high
    return _TIEBREAK_DIFFICULTY


def next_round(
    state: MatchState, *, question_id: str, difficulty: int, now_ms: int
) -> ServedQuestion:
    if state.status is not MatchStatus.PLAYING:
        raise InvalidTransition("la partida no está en curso: no hay ronda siguiente")

    low, high = difficulty_range(state)
    if not low <= difficulty <= high:
        raise ValueError(f"dificultad {difficulty} fuera del tramo {low}-{high}")

    return ServedQuestion(
        round_index=state.round_index,
        question_id=question_id,
        difficulty=difficulty,
        seconds=state.seconds_per_round,
        served_at_ms=now_ms,
    )


def resolve_round(
    state: MatchState,
    served: ServedQuestion,
    *,
    correct_index: int,
    a: Answer | None,
    b: Answer | None,
) -> Resolved:
    if state.status is not MatchStatus.PLAYING:
        raise InvalidTransition(
            "la partida no está en curso: no hay ronda que resolver"
        )
    if served.round_index != state.round_index:
        raise InvalidTransition(
            f"se resolvió la ronda {served.round_index} estando en la {state.round_index}"
        )
    if correct_index not in CHOICES:
        raise ValueError(f"correct_index fuera de rango: {correct_index}")

    a_settled = settle(served, a, correct_index=correct_index)
    b_settled = settle(served, b, correct_index=correct_index)

    a_points = round_points(
        correct=a_settled.correct,
        elapsed_ms=a_settled.elapsed_ms,
        total_seconds=served.seconds,
    )
    b_points = round_points(
        correct=b_settled.correct,
        elapsed_ms=b_settled.elapsed_ms,
        total_seconds=served.seconds,
    )

    record = RoundRecord(
        round_index=served.round_index,
        question_id=served.question_id,
        difficulty=served.difficulty,
        seconds=served.seconds,
        correct_index=correct_index,
        a_choice=a_settled.answer.choice if a_settled.answer is not None else None,
        b_choice=b_settled.answer.choice if b_settled.answer is not None else None,
        a_ms=a_settled.elapsed_ms if a_settled.answer is not None else None,
        b_ms=b_settled.elapsed_ms if b_settled.answer is not None else None,
        a_correct=a_settled.correct,
        b_correct=b_settled.correct,
        a_points=a_points,
        b_points=b_points,
        a_rejected=a_settled.rejected,
        b_rejected=b_settled.rejected,
    )

    rounds = (*state.rounds, record)
    score_a = state.score_a + a_points
    score_b = state.score_b + b_points

    decided = len(rounds) >= state.config.rounds and score_a != score_b
    winner = None
    if decided:
        winner = Player.A if score_a > score_b else Player.B

    next_state = replace(
        state,
        rounds=rounds,
        status=MatchStatus.FINISHED if decided else MatchStatus.PLAYING,
        winner=winner,
    )
    return Resolved(record=record, state=next_state)


def abandon(state: MatchState, *, gone: Player) -> MatchState:
    if state.status is not MatchStatus.PLAYING:
        raise InvalidTransition("solo se puede abandonar una partida en curso")

    winner = Player.B if gone is Player.A else Player.A
    return replace(state, status=MatchStatus.ABANDONED, winner=winner)


def void(state: MatchState) -> MatchState:
    if state.status is not MatchStatus.PLAYING:
        raise InvalidTransition("solo se puede anular una partida en curso")

    return replace(state, status=MatchStatus.VOID, winner=None)
