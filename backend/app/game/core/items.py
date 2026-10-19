"""Los tipos que comparten todos los modos del juego.

`ServedItem` es lo que el servidor ya envió: el ítem, su dificultad, el tiempo
asignado y el instante límite. `Submission` es lo que llegó del cliente, en la
forma que el modo espere. `Verdict` es el resultado de juzgarlo.

La solución nunca vive acá: la ve el `grade` del modo. El borde solo manipula
estos tipos y no puede filtrar lo que no tiene.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

from app.game.constants import DIFFICULTY_MAX, DIFFICULTY_MIN


class RejectReason(StrEnum):
    OUTSIDE_WINDOW = "outside_window"


@dataclass(frozen=True)
class ServedItem:
    """Un ítem en vuelo y la ventana en la que su respuesta existe.

    `deadline` es absoluto y `seconds` es el tiempo mostrado al jugador: en los
    formatos lineales coinciden (`deadline = served_at_ms + seconds * 1000`),
    pero un tablero puede compartir un límite distinto sin romper el tipo.
    """

    item_key: str
    difficulty: int
    seconds: int
    served_at_ms: int
    deadline: int

    def __post_init__(self) -> None:
        if not self.item_key:
            raise ValueError("item_key vacío")
        if not DIFFICULTY_MIN <= self.difficulty <= DIFFICULTY_MAX:
            raise ValueError(f"dificultad fuera de rango: {self.difficulty}")
        if self.seconds <= 0:
            raise ValueError(f"seconds debe ser positivo: {self.seconds}")
        if self.served_at_ms < 0:
            raise ValueError(f"served_at_ms negativo: {self.served_at_ms}")
        if self.deadline <= self.served_at_ms:
            raise ValueError("deadline debe ser posterior a served_at_ms")

    @property
    def window_ms(self) -> int:
        return self.deadline - self.served_at_ms


@dataclass(frozen=True)
class ChoiceSubmission:
    index: int
    kind: Literal["choice"] = field(default="choice", init=False)

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError(f"index negativo: {self.index}")


@dataclass(frozen=True)
class TextSubmission:
    text: str
    kind: Literal["text"] = field(default="text", init=False)


@dataclass(frozen=True)
class LetterSubmission:
    letter: str
    word: str
    kind: Literal["letter"] = field(default="letter", init=False)


@dataclass(frozen=True)
class OrderSubmission:
    order: tuple[int, ...]
    kind: Literal["order"] = field(default="order", init=False)


Submission = ChoiceSubmission | TextSubmission | LetterSubmission | OrderSubmission


@dataclass(frozen=True)
class Verdict[DetailT]:
    """Lo que comparten todos los modos después de juzgar una submission.

    `detail` queda tipado por el modo: el quiz puede devolver la explicación y
    el rosco, la letra esperada. `settle` rellena lo común.
    """

    correct: bool
    elapsed_ms: int
    rejected: RejectReason | None = None
    detail: DetailT | None = None
