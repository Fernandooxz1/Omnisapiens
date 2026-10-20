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

    La máquina pura no consulta el ranking: deja `None` y el borde lo completa
    con la fila ya cerrada. Si el ranking falla, estos campos salen en `None`.
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
class SessionStart(Message):
    """Arranque del protocolo canónico de una sesión solo.

    `session_id` es el de `game_sessions`: la sesión la crea `POST /sessions` y
    el socket solo se engancha. `lives` es un dato del formato lineal; un modo
    sin vidas puede mandarlo igual.
    """

    type: ClassVar[str] = "session_start"
    session_id: str
    mode: str
    config: dict[str, object]
    lives: int


@dataclass(frozen=True)
class ItemStart(Message):
    """Un ítem servido. `payload` ya pasó por el `public_schema` del modo."""

    type: ClassVar[str] = "item_start"
    item_key: str
    position: int
    ends_at: int
    total_seconds: int
    payload: dict[str, object]


@dataclass(frozen=True)
class ItemResult(Message):
    """El ítem cerrado. Recién acá viaja la solución.

    `scores` es el estado del corredor después de la ronda: puntaje, vidas,
    racha y aciertos. El cliente lo dibuja; no lo recalcula.
    """

    type: ClassVar[str] = "item_result"
    item_key: str
    correct: bool
    submission: dict[str, object] | None
    solution: dict[str, object] | None
    points: int
    scores: dict[str, int]


@dataclass(frozen=True)
class SessionEnd(Message):
    """Fin de la sesión. `ranking` es nulo en un modo que no publica tabla."""

    type: ClassVar[str] = "session_end"
    session_id: str
    score: int
    correct_count: int
    max_difficulty: int
    longest_streak: int
    ranking: dict[str, object] | None


@dataclass(frozen=True)
class SessionState(Message):
    """Foto de la sesión para el cliente que pide `state`."""

    type: ClassVar[str] = "session_state"
    session_id: str
    mode: str
    config: dict[str, object]
    position: int
    ends_at: int | None
    total_seconds: int | None
    payload: dict[str, object] | None
    scores: dict[str, int]
    finished: bool


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
