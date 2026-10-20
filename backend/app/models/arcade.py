"""Las dos tablas del arcade: la partida y sus rondas."""

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
    desc,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.game.answers import RejectReason
from app.game.constants import CHOICES, DIFFICULTY_MAX, DIFFICULTY_MIN
from app.game.solo_engine import RunStatus
from app.models.base import Base
from app.models.checks import number_list, quoted_list

# `invalid` no existe en el motor: es el estado que usa la base para sacar de
# circulación una partida sospechosa. El ranking solo mira las `finished`.
INVALID_STATUS = "invalid"
RUN_STATUSES = (*RunStatus, INVALID_STATUS)

_FINISHED_ONLY = text("status = 'finished'")


class ArcadeRun(Base):
    __tablename__ = "arcade_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    score: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    correct_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    longest_streak: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    max_difficulty: Mapped[int] = mapped_column(SmallInteger, server_default=text("1"))

    status: Mapped[str] = mapped_column(String(16), server_default="playing")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            f"status IN ({quoted_list(RUN_STATUSES)})", name="status_known"
        ),
        CheckConstraint(
            "score >= 0 AND correct_count >= 0", name="counters_not_negative"
        ),
        # Misma invariante que el motor: la racha más larga nunca supera los aciertos.
        CheckConstraint(
            "longest_streak BETWEEN 0 AND correct_count", name="streak_within_corrects"
        ),
        CheckConstraint(
            f"max_difficulty BETWEEN {DIFFICULTY_MIN} AND {DIFFICULTY_MAX}",
            name="difficulty_range",
        ),
        CheckConstraint(
            "(status = 'playing') = (ended_at IS NULL)", name="ending_matches_status"
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at", name="ends_after_start"
        ),
        Index(None, "user_id"),
        # Los tres índices del ranking, parciales: una partida en curso o dudosa no
        # ocupa lugar, y el que ordena por puntaje no escanea historial inútil.
        Index(
            "ix_arcade_runs_best_by_user",
            "user_id",
            desc("score"),
            postgresql_where=_FINISHED_ONLY,
        ),
        Index("ix_arcade_runs_ranking", desc("score"), postgresql_where=_FINISHED_ONLY),
        Index("ix_arcade_runs_weekly", "ended_at", postgresql_where=_FINISHED_ONLY),
        Index(None, "status", "started_at"),
    )


class ArcadeAnswer(Base):
    """Una ronda del arcade.

    Sin rival no hay dos elecciones, y `ms` nunca es nulo: `settle` mide el tiempo
    agotado cuando no hubo respuesta válida.
    """

    __tablename__ = "arcade_answers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("arcade_runs.id", ondelete="CASCADE")
    )
    round_index: Mapped[int] = mapped_column(SmallInteger)

    question_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("content_items.id", ondelete="SET NULL")
    )
    difficulty: Mapped[int] = mapped_column(SmallInteger)
    seconds: Mapped[int] = mapped_column(SmallInteger)
    correct_index: Mapped[int] = mapped_column(SmallInteger)

    chosen_index: Mapped[int | None] = mapped_column(SmallInteger)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    ms: Mapped[int] = mapped_column(Integer)
    points: Mapped[int] = mapped_column(Integer)
    rejected: Mapped[str | None] = mapped_column(String(24))

    __table_args__ = (
        UniqueConstraint("run_id", "round_index"),
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
            f"chosen_index IS NULL OR chosen_index IN ({number_list(CHOICES)})",
            name="chosen_in_range",
        ),
        CheckConstraint(
            "is_correct = (chosen_index IS NOT NULL AND chosen_index = correct_index)",
            name="correctness_from_choice",
        ),
        CheckConstraint(
            f"rejected IS NULL OR rejected IN ({quoted_list(RejectReason)})",
            name="rejection_known",
        ),
        CheckConstraint(
            "rejected IS NULL OR chosen_index IS NULL", name="rejected_without_choice"
        ),
        CheckConstraint("ms BETWEEN 0 AND seconds * 1000", name="ms_within_window"),
        CheckConstraint("points >= 0", name="points_not_negative"),
    )
