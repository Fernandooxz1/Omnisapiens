"""Las cuatro tablas de una sesión: resumen, sillas, ítems e intentos.

Un solo esquema cubre lineal y tablero, solo y versus. `item_key` distingue
rondas numeradas de posiciones de tablero, y `attempt_seq` permite más de un
intento sobre el mismo ítem. `solution_snapshot` deja la fila auditable aunque
el contenido se archive.
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
    Text,
    UniqueConstraint,
    desc,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.game.constants import DIFFICULTY_MAX, DIFFICULTY_MIN
from app.models.base import Base
from app.models.checks import quoted_list

SESSION_STATUSES = ("playing", "finished", "abandoned", "void", "invalid")
PARTICIPANT_OUTCOMES = ("win", "lose", "draw", "abandoned", "void")

# `invalid` es el estado que usa la base (barrendero, auditoría) para sacar de
# circulación una sesión; el ranking solo mira las `finished` con dueño.
_RANKED = text("status = 'finished' AND owner_user_id IS NOT NULL")


class GameSession(Base):
    """El resumen de una partida de cualquier formato.

    Los contadores son proyección: los escribe el motor al cerrar la sesión.
    `owner_user_id` es nulo en versus (no hay dueño) y `room_id` puede quedar
    nulo si la sala se purga sin llevarse el historial.
    """

    __tablename__ = "game_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    mode: Mapped[str] = mapped_column(Text)
    content_kind: Mapped[str] = mapped_column(Text)
    play_format: Mapped[str] = mapped_column(Text)
    ruleset_version: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[str] = mapped_column(String(16), server_default="playing")
    config: Mapped[dict[str, object]] = mapped_column(JSONB)

    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("rooms.id", ondelete="SET NULL")
    )

    score: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    correct_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    longest_streak: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    max_difficulty: Mapped[int] = mapped_column(SmallInteger, server_default=text("1"))

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            f"status IN ({quoted_list(SESSION_STATUSES)})", name="status_known"
        ),
        # Una sesión en curso no tiene final, y una cerrada lo tiene: evita el
        # estado ambiguo que después no se sabe si el barrendero debe tocar.
        CheckConstraint(
            "(status = 'playing') = (ended_at IS NULL)", name="ending_matches_status"
        ),
        CheckConstraint(
            "score >= 0 AND correct_count >= 0", name="counters_not_negative"
        ),
        CheckConstraint(
            "longest_streak BETWEEN 0 AND correct_count", name="streak_within_corrects"
        ),
        CheckConstraint(
            f"max_difficulty BETWEEN {DIFFICULTY_MIN} AND {DIFFICULTY_MAX}",
            name="difficulty_range",
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at", name="ends_after_start"
        ),
        CheckConstraint("jsonb_typeof(config) = 'object'", name="config_object"),
        # Índices de FK, que Postgres no crea solo.
        Index(None, "owner_user_id"),
        Index(None, "room_id"),
        # Lo que barre el reaper: sesiones vivas abiertas hace rato.
        Index(None, "status", "started_at"),
        # Ranking y "mi mejor marca": parciales, así una sesión en curso o
        # abandonada no ocupa lugar ni obliga a filtrar por estado.
        Index(
            "ix_sessions_ranking",
            "mode",
            desc("score"),
            "ended_at",
            postgresql_where=_RANKED,
        ),
        Index(
            "ix_sessions_best_by_user",
            "mode",
            "owner_user_id",
            desc("score"),
            postgresql_where=_RANKED,
        ),
    )


class GameParticipant(Base):
    """Una silla ocupada: quién jugó, en qué asiento y cómo terminó."""

    __tablename__ = "game_participants"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("game_sessions.id", ondelete="CASCADE"), primary_key=True
    )
    seat: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    score: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    # Nulo mientras la sesión está en curso; se escribe al cerrar.
    outcome: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("session_id", "user_id"),
        CheckConstraint("score >= 0", name="score_not_negative"),
        CheckConstraint(
            f"outcome IS NULL OR outcome IN ({quoted_list(PARTICIPANT_OUTCOMES)})",
            name="outcome_known",
        ),
        Index(None, "user_id"),
    )


class SessionItem(Base):
    """Un ítem servido, con la solución congelada al momento de servirlo."""

    __tablename__ = "session_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("game_sessions.id", ondelete="CASCADE")
    )
    # "0", "1" en lineal; "A", "B" en tablero.
    item_key: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(SmallInteger)

    # SET NULL para poder archivar o purgar el contenido sin perder la sesión.
    content_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("content_items.id", ondelete="SET NULL")
    )
    difficulty: Mapped[int] = mapped_column(SmallInteger)
    seconds: Mapped[int] = mapped_column(Integer)

    served_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    solution_snapshot: Mapped[dict[str, object]] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("session_id", "item_key"),
        CheckConstraint("position >= 0", name="position_not_negative"),
        CheckConstraint(
            f"difficulty BETWEEN {DIFFICULTY_MIN} AND {DIFFICULTY_MAX}",
            name="difficulty_range",
        ),
        CheckConstraint("seconds > 0", name="seconds_positive"),
        Index(None, "content_id"),
    )


class SessionAttempt(Base):
    """Una respuesta enviada sobre un ítem, con su veredicto ya decidido."""

    __tablename__ = "session_attempts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("session_items.id", ondelete="CASCADE")
    )
    attempt_seq: Mapped[int] = mapped_column(SmallInteger)
    seat: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))

    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    submission: Mapped[dict[str, object]] = mapped_column(JSONB)
    correct: Mapped[bool] = mapped_column(Boolean)
    elapsed_ms: Mapped[int] = mapped_column(Integer)
    points: Mapped[int] = mapped_column(Integer)
    # Motivo de rechazo del modo (fuera de ventana, inválida, etc.): el
    # catálogo es del `RoundRules`, no de la base.
    rejected: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("item_id", "seat", "attempt_seq"),
        CheckConstraint("attempt_seq >= 0", name="attempt_seq_not_negative"),
        CheckConstraint("elapsed_ms >= 0", name="elapsed_ms_not_negative"),
        CheckConstraint("points >= 0", name="points_not_negative"),
    )
