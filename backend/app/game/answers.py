from dataclasses import dataclass
from enum import StrEnum

from app.game.constants import CHOICES, DIFFICULTY_MAX, DIFFICULTY_MIN


class RejectReason(StrEnum):
    OUTSIDE_WINDOW = "outside_window"


@dataclass(frozen=True)
class ServedQuestion:
    """Lo que ya se envió al cliente: fija dificultad, tiempo y momento de arranque.

    Guardar estos valores evita recalcularlos después: el puntaje se calcula
    siempre con el tiempo que el jugador realmente vio.
    """

    round_index: int
    question_id: str
    difficulty: int
    seconds: int
    served_at_ms: int

    def __post_init__(self) -> None:
        if self.round_index < 0:
            raise ValueError(f"round_index negativo: {self.round_index}")
        if not DIFFICULTY_MIN <= self.difficulty <= DIFFICULTY_MAX:
            raise ValueError(f"dificultad fuera de rango: {self.difficulty}")
        if self.seconds <= 0:
            raise ValueError(f"seconds debe ser positivo: {self.seconds}")
        if self.served_at_ms < 0:
            raise ValueError(f"served_at_ms negativo: {self.served_at_ms}")

    @property
    def limit_ms(self) -> int:
        return self.seconds * 1000

    @property
    def ends_at_ms(self) -> int:
        return self.served_at_ms + self.limit_ms


@dataclass(frozen=True)
class Answer:
    """Respuesta bien formada: si no cabe en el dominio, no se puede construir."""

    round_index: int
    choice: int
    answered_at_ms: int

    def __post_init__(self) -> None:
        if self.round_index < 0:
            raise ValueError(f"round_index negativo: {self.round_index}")
        if self.choice not in CHOICES:
            raise ValueError(f"choice fuera de rango: {self.choice}")
        if self.answered_at_ms < 0:
            raise ValueError(f"answered_at_ms negativo: {self.answered_at_ms}")


@dataclass(frozen=True)
class Settled:
    """Respuesta ya juzgada. `answer` es None si no hubo respuesta válida."""

    answer: Answer | None
    rejected: RejectReason | None
    correct: bool
    elapsed_ms: int


def settle(
    served: ServedQuestion, answer: Answer | None, *, correct_index: int
) -> Settled:
    """Única definición de qué cuenta como respuesta: fuera de la ventana no existe."""
    if answer is None:
        return Settled(
            answer=None, rejected=None, correct=False, elapsed_ms=served.limit_ms
        )

    if not served.served_at_ms <= answer.answered_at_ms <= served.ends_at_ms:
        return Settled(
            answer=None,
            rejected=RejectReason.OUTSIDE_WINDOW,
            correct=False,
            elapsed_ms=served.limit_ms,
        )

    return Settled(
        answer=answer,
        rejected=None,
        correct=answer.choice == correct_index,
        elapsed_ms=answer.answered_at_ms - served.served_at_ms,
    )
