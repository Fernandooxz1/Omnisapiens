"""Las formas de los mensajes del WebSocket de salas (§10.1).

Un solo sobre para todo: `{"t": tipo, "id": opcional, "d": {...}}`. Acá viven las
dataclasses del lado del servidor y el que las serializa. El tipo, no el handler,
decide qué campos viajan: una pregunta que se manda al cliente **no tiene**
`correct_index`, porque el dataclass no tiene dónde guardarlo.
"""

from dataclasses import asdict, dataclass
from typing import Any, ClassVar


@dataclass(frozen=True)
class Message:
    type: ClassVar[str] = ""


@dataclass(frozen=True)
class PlayerView:
    id: str
    nick: str


@dataclass(frozen=True)
class RoundChoice:
    choice: int | None
    ms: int | None
    points: int
    correct: bool


@dataclass(frozen=True)
class Scores:
    you: int
    opponent: int


@dataclass(frozen=True)
class RoomState(Message):
    type: ClassVar[str] = "room_state"
    code: str
    status: str
    config: dict[str, int]
    you: PlayerView
    players: list[PlayerView]
    match_id: str | None


@dataclass(frozen=True)
class MatchStart(Message):
    type: ClassVar[str] = "match_start"
    match_id: str
    config: dict[str, int]
    rounds_total: int


@dataclass(frozen=True)
class RoundStart(Message):
    type: ClassVar[str] = "round_start"
    round: int
    question_id: str
    prompt: str
    options: list[str]
    category: str
    difficulty: int
    ends_at: int
    total_seconds: int


@dataclass(frozen=True)
class OpponentAnswered(Message):
    type: ClassVar[str] = "opponent_answered"
    round: int


@dataclass(frozen=True)
class RoundResult(Message):
    type: ClassVar[str] = "round_result"
    round: int
    correct_index: int
    explanation: str | None
    you: RoundChoice
    opponent: RoundChoice
    scores: Scores


@dataclass(frozen=True)
class ReconnectPending(Message):
    type: ClassVar[str] = "reconnect_pending"
    seconds_left: int


@dataclass(frozen=True)
class OpponentReturned(Message):
    type: ClassVar[str] = "opponent_returned"


@dataclass(frozen=True)
class MatchEnd(Message):
    type: ClassVar[str] = "match_end"
    winner: str
    scores: Scores
    rounds: list[RoundResult]
    reason: str


@dataclass(frozen=True)
class RematchWaiting(Message):
    type: ClassVar[str] = "rematch_waiting"


@dataclass(frozen=True)
class ArcadeStart(Message):
    type: ClassVar[str] = "arcade_start"
    run_id: str
    lives: int
    seconds: int


@dataclass(frozen=True)
class ArcadeQuestion(Message):
    """La pregunta del arcade. Sin `correct_index`: vive en `LoadedQuestion`."""

    type: ClassVar[str] = "arcade_question"
    round: int
    prompt: str
    options: list[str]
    category: str
    difficulty: int
    seconds: int
    ends_at: int
    score: int
    lives: int
    streak: int
    correct_count: int


@dataclass(frozen=True)
class ArcadeResult(Message):
    type: ClassVar[str] = "arcade_result"
    round: int
    correct_index: int
    explanation: str | None
    you: RoundChoice
    score: int
    lives: int
    streak: int
    correct_count: int


@dataclass(frozen=True)
class ArcadeEnd(Message):
    """Fin de corrida.

    Las posiciones y la mejor marca las completa el ranking (corte 4). La
    máquina pura no toca Redis: deja `None` y el borde las reemplaza.
    """

    type: ClassVar[str] = "arcade_end"
    run_id: str
    score: int
    correct_count: int
    max_difficulty: int
    longest_streak: int
    rank_global: int | None
    rank_weekly: int | None
    personal_best: int | None
    is_new_best: bool


@dataclass(frozen=True)
class Error(Message):
    type: ClassVar[str] = "error"
    code: str
    message: str


@dataclass(frozen=True)
class Pong(Message):
    type: ClassVar[str] = "pong"


def encode(message: Message, *, id: str | None = None) -> dict[str, Any]:
    """Arma el sobre. `id` solo cuando el pedido lo trajo y hay que correlacionar."""
    sobre: dict[str, Any] = {"t": message.type, "d": asdict(message)}
    if id is not None:
        sobre["id"] = id
    return sobre
