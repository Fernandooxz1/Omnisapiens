"""La unidad "partida": la sala, la partida y sus rondas.

Las tres tablas van juntas porque el `config` es el mismo objeto (`MatchConfig`)
en las dos primeras y su validación tiene que ser idéntica.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.game.answers import RejectReason
from app.game.constants import (
    CHOICES,
    DIFFICULTY_MAX,
    DIFFICULTY_MIN,
    ONLINE_ROUNDS_OPTIONS,
    ONLINE_SECONDS_OPTIONS,
    ROOM_CODE_ALPHABET,
    ROOM_CODE_LENGTH,
)
from app.game.match_engine import MatchStatus
from app.models.base import Base
from app.models.checks import number_list, quoted_list

ROOM_STATUSES = ("waiting", "playing", "finished", "expired")


def _config_constraint(name: str) -> CheckConstraint:
    """Valida forma y valores del config sin castear nada: un cast sobre una clave
    que no es número tira un error de sintaxis en vez de una violación legible.

    `IS NOT DISTINCT FROM` en vez de `=`: un CHECK se cumple cuando da NULL, así que
    una clave ausente (NULL) pasaría como si fuera válida.
    """
    return CheckConstraint(
        "jsonb_typeof(config) = 'object'"
        " AND jsonb_typeof(config->'rounds') IS NOT DISTINCT FROM 'number'"
        " AND jsonb_typeof(config->'seconds') IS NOT DISTINCT FROM 'number'"
        f" AND (config->>'rounds') IN ({quoted_list(ONLINE_ROUNDS_OPTIONS)})"
        f" AND (config->>'seconds') IN ({quoted_list(ONLINE_SECONDS_OPTIONS)})",
        name=name,
    )


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # El host es quien crea la sala, y no "el primero que entra": la fila vive más
    # que las conexiones, así que una reconexión no cambia de dueño la sala.
    host_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    # varchar y no char: char(n) rellena con espacios y compara raro.
    code: Mapped[str] = mapped_column(String(ROOM_CODE_LENGTH))
    config: Mapped[dict[str, int]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(16), server_default="waiting")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            f"code ~ '^[{ROOM_CODE_ALPHABET}]{{{ROOM_CODE_LENGTH}}}$'",
            name="code_alphabet",
        ),
        CheckConstraint(
            f"status IN ({quoted_list(ROOM_STATUSES)})", name="status_known"
        ),
        _config_constraint("config_valid"),
        UniqueConstraint("code"),
        # Índice de FK (Postgres no lo crea solo): "las salas que creé" y el
        # chequeo de la FK no barren la tabla.
        Index(None, "host_user_id"),
        # Lo que busca el barrendero: salas vivas con la fecha vencida.
        Index(None, "status", "expires_at"),
    )


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Nullable y SET NULL: el día que se purguen salas viejas, el historial sobrevive.
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("rooms.id", ondelete="SET NULL")
    )
    player_a_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    player_b_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    config: Mapped[dict[str, int]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(16), server_default="playing")

    # Copia derivada del historial de rondas: la escribe el motor al cerrar la partida.
    score_a: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    score_b: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    winner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(f"status IN ({quoted_list(MatchStatus)})", name="status_known"),
        _config_constraint("config_valid"),
        CheckConstraint("player_a_id <> player_b_id", name="players_differ"),
        CheckConstraint(
            "winner_id IS NULL OR winner_id IN (player_a_id, player_b_id)",
            name="winner_plays",
        ),
        CheckConstraint("score_a >= 0 AND score_b >= 0", name="scores_not_negative"),
        # Índice de FK, que Postgres no crea solo: sin esto el chequeo de la FK
        # y el "mis últimas partidas" barren la tabla entera.
        Index(None, "player_a_id"),
        Index(None, "player_b_id"),
        Index(None, "room_id"),
        Index(None, "status", "started_at"),
    )


class MatchRound(Base):
    """Una ronda resuelta, con todo lo necesario para recalcularla años después.

    Las columnas espejan `RoundRecord` del motor: mismo nombre, mismo significado.
    """

    __tablename__ = "match_rounds"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE")
    )
    round_index: Mapped[int] = mapped_column(SmallInteger)

    # SET NULL para poder purgar una pregunta sin perder la ronda que la usó.
    question_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("questions.id", ondelete="SET NULL")
    )
    difficulty: Mapped[int] = mapped_column(SmallInteger)
    seconds: Mapped[int] = mapped_column(SmallInteger)
    correct_index: Mapped[int] = mapped_column(SmallInteger)

    a_choice: Mapped[int | None] = mapped_column(SmallInteger)
    b_choice: Mapped[int | None] = mapped_column(SmallInteger)
    a_ms: Mapped[int | None] = mapped_column(Integer)
    b_ms: Mapped[int | None] = mapped_column(Integer)
    # No se derivan de (choice, correct_index): una respuesta fuera de la ventana
    # puede tener la opción correcta y aun así contar mal.
    a_correct: Mapped[bool] = mapped_column(Boolean)
    b_correct: Mapped[bool] = mapped_column(Boolean)
    a_points: Mapped[int] = mapped_column(Integer)
    b_points: Mapped[int] = mapped_column(Integer)
    a_rejected: Mapped[str | None] = mapped_column(String(24))
    b_rejected: Mapped[str | None] = mapped_column(String(24))

    __table_args__ = (
        UniqueConstraint("match_id", "round_index"),
        CheckConstraint("round_index >= 0", name="round_index_not_negative"),
        CheckConstraint(
            f"difficulty BETWEEN {DIFFICULTY_MIN} AND {DIFFICULTY_MAX}",
            name="difficulty_range",
        ),
        CheckConstraint("seconds > 0", name="seconds_positive"),
        CheckConstraint(
            f"correct_index IN ({number_list(CHOICES)})", name="correct_index_choice"
        ),
        CheckConstraint(
            f"(a_choice IS NULL OR a_choice IN ({number_list(CHOICES)}))"
            f" AND (b_choice IS NULL OR b_choice IN ({number_list(CHOICES)}))",
            name="choices_in_range",
        ),
        # Sin respuesta no hay tiempo que medir, y al revés. El tope es la ventana:
        # `settle` no deja medir más que el tiempo que se mostró la pregunta.
        CheckConstraint(
            "(a_choice IS NULL) = (a_ms IS NULL)"
            " AND (b_choice IS NULL) = (b_ms IS NULL)"
            " AND (a_ms IS NULL OR (a_ms >= 0 AND a_ms <= seconds * 1000))"
            " AND (b_ms IS NULL OR (b_ms >= 0 AND b_ms <= seconds * 1000))",
            name="times_consistent",
        ),
        # Las mismas invariantes que ya garantiza `settle`, escritas en piedra.
        CheckConstraint(
            "a_correct = (a_choice IS NOT NULL AND a_choice = correct_index)"
            " AND b_correct = (b_choice IS NOT NULL AND b_choice = correct_index)",
            name="correctness_from_choice",
        ),
        CheckConstraint(
            f"(a_rejected IS NULL OR a_rejected IN ({quoted_list(RejectReason)}))"
            f" AND (b_rejected IS NULL OR b_rejected IN ({quoted_list(RejectReason)}))"
            " AND (a_rejected IS NULL OR a_choice IS NULL)"
            " AND (b_rejected IS NULL OR b_choice IS NULL)",
            name="rejections_consistent",
        ),
        # Solo el piso: cuánto suma un acierto es economía del motor, y eso cambia.
        CheckConstraint("a_points >= 0 AND b_points >= 0", name="points_not_negative"),
    )
