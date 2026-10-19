"""sessions

Revision ID: 0005
Revises: 0004b
Create Date: 2026-10-19 17:08:17.607854

Crea el modelo genérico de sesión (resumen, sillas, ítems e intentos) y le da a
la sala un `mode`. El `CHECK` de `rooms.config` se relaja a "es un objeto":
cada modo valida su configuración con su `config_schema` en Python.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RANKED = sa.text("status = 'finished' AND owner_user_id IS NOT NULL")
_OLD_ROOM_CONFIG = (
    "jsonb_typeof(config) = 'object'"
    " AND jsonb_typeof(config->'rounds') IS NOT DISTINCT FROM 'number'"
    " AND jsonb_typeof(config->'seconds') IS NOT DISTINCT FROM 'number'"
    " AND (config->>'rounds') IN ('3', '5', '7')"
    " AND (config->>'seconds') IN ('10', '20', '30')"
)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "game_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("content_kind", sa.Text(), nullable=False),
        sa.Column("play_format", sa.Text(), nullable=False),
        sa.Column("ruleset_version", sa.SmallInteger(), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default="playing", nullable=False
        ),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=True),
        sa.Column("room_id", sa.Uuid(), nullable=True),
        sa.Column("score", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "correct_count", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "longest_streak", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "max_difficulty",
            sa.SmallInteger(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(status = 'playing') = (ended_at IS NULL)",
            name=op.f("ck_game_sessions_ending_matches_status"),
        ),
        sa.CheckConstraint(
            "jsonb_typeof(config) = 'object'",
            name=op.f("ck_game_sessions_config_object"),
        ),
        sa.CheckConstraint(
            "status IN ('playing', 'finished', 'abandoned', 'void', 'invalid')",
            name=op.f("ck_game_sessions_status_known"),
        ),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name=op.f("ck_game_sessions_ends_after_start"),
        ),
        sa.CheckConstraint(
            "longest_streak BETWEEN 0 AND correct_count",
            name=op.f("ck_game_sessions_streak_within_corrects"),
        ),
        sa.CheckConstraint(
            "max_difficulty BETWEEN 1 AND 5",
            name=op.f("ck_game_sessions_difficulty_range"),
        ),
        sa.CheckConstraint(
            "score >= 0 AND correct_count >= 0",
            name=op.f("ck_game_sessions_counters_not_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            ["users.id"],
            name=op.f("fk_game_sessions_owner_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["room_id"],
            ["rooms.id"],
            name=op.f("fk_game_sessions_room_id"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_game_sessions")),
    )
    op.create_index(
        op.f("ix_game_sessions_owner_user_id"),
        "game_sessions",
        ["owner_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_game_sessions_room_id"),
        "game_sessions",
        ["room_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_game_sessions_status_started_at"),
        "game_sessions",
        ["status", "started_at"],
        unique=False,
    )
    op.create_index(
        "ix_sessions_best_by_user",
        "game_sessions",
        ["mode", "owner_user_id", sa.literal_column("score DESC")],
        unique=False,
        postgresql_where=_RANKED,
    )
    op.create_index(
        "ix_sessions_ranking",
        "game_sessions",
        ["mode", sa.literal_column("score DESC"), "ended_at"],
        unique=False,
        postgresql_where=_RANKED,
    )

    op.create_table(
        "game_participants",
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("seat", sa.SmallInteger(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "outcome IS NULL OR outcome IN"
            " ('win', 'lose', 'draw', 'abandoned', 'void')",
            name=op.f("ck_game_participants_outcome_known"),
        ),
        sa.CheckConstraint(
            "score >= 0", name=op.f("ck_game_participants_score_not_negative")
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["game_sessions.id"],
            name=op.f("fk_game_participants_session_id"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_game_participants_user_id"),
        ),
        sa.PrimaryKeyConstraint(
            "session_id", "seat", name=op.f("pk_game_participants")
        ),
        sa.UniqueConstraint(
            "session_id",
            "user_id",
            name=op.f("uq_game_participants_session_id_user_id"),
        ),
    )
    op.create_index(
        op.f("ix_game_participants_user_id"),
        "game_participants",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "session_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("item_key", sa.Text(), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.Column("content_id", sa.Uuid(), nullable=True),
        sa.Column("difficulty", sa.SmallInteger(), nullable=False),
        sa.Column("seconds", sa.Integer(), nullable=False),
        sa.Column("served_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "solution_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.CheckConstraint(
            "difficulty BETWEEN 1 AND 5",
            name=op.f("ck_session_items_difficulty_range"),
        ),
        sa.CheckConstraint(
            "position >= 0", name=op.f("ck_session_items_position_not_negative")
        ),
        sa.CheckConstraint(
            "seconds > 0", name=op.f("ck_session_items_seconds_positive")
        ),
        sa.ForeignKeyConstraint(
            ["content_id"],
            ["content_items.id"],
            name=op.f("fk_session_items_content_id"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["game_sessions.id"],
            name=op.f("fk_session_items_session_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_session_items")),
        sa.UniqueConstraint(
            "session_id", "item_key", name=op.f("uq_session_items_session_id_item_key")
        ),
    )
    op.create_index(
        op.f("ix_session_items_content_id"),
        "session_items",
        ["content_id"],
        unique=False,
    )

    op.create_table(
        "session_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("item_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_seq", sa.SmallInteger(), nullable=False),
        sa.Column(
            "seat", sa.SmallInteger(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "submission", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("elapsed_ms", sa.Integer(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("rejected", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "attempt_seq >= 0",
            name=op.f("ck_session_attempts_attempt_seq_not_negative"),
        ),
        sa.CheckConstraint(
            "elapsed_ms >= 0",
            name=op.f("ck_session_attempts_elapsed_ms_not_negative"),
        ),
        sa.CheckConstraint(
            "points >= 0", name=op.f("ck_session_attempts_points_not_negative")
        ),
        sa.ForeignKeyConstraint(
            ["item_id"],
            ["session_items.id"],
            name=op.f("fk_session_attempts_item_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_session_attempts")),
        sa.UniqueConstraint(
            "item_id",
            "seat",
            "attempt_seq",
            name=op.f("uq_session_attempts_item_id_seat_attempt_seq"),
        ),
    )

    op.add_column(
        "rooms",
        sa.Column("mode", sa.Text(), server_default="trivia_versus", nullable=False),
    )
    # El formato del config ya depende del modo: la base no puede validar un
    # esquema que no conoce. Los tests de contrato de la API cubren los valores.
    op.drop_constraint(op.f("ck_rooms_config_valid"), "rooms", type_="check")
    op.create_check_constraint(
        op.f("ck_rooms_config_valid"), "rooms", "jsonb_typeof(config) = 'object'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f("ck_rooms_config_valid"), "rooms", type_="check")
    op.create_check_constraint(op.f("ck_rooms_config_valid"), "rooms", _OLD_ROOM_CONFIG)
    op.drop_column("rooms", "mode")

    op.drop_table("session_attempts")
    op.drop_index(op.f("ix_session_items_content_id"), table_name="session_items")
    op.drop_table("session_items")
    op.drop_index(op.f("ix_game_participants_user_id"), table_name="game_participants")
    op.drop_table("game_participants")
    op.drop_index("ix_sessions_ranking", table_name="game_sessions")
    op.drop_index("ix_sessions_best_by_user", table_name="game_sessions")
    op.drop_index(
        op.f("ix_game_sessions_status_started_at"), table_name="game_sessions"
    )
    op.drop_index(op.f("ix_game_sessions_room_id"), table_name="game_sessions")
    op.drop_index(op.f("ix_game_sessions_owner_user_id"), table_name="game_sessions")
    op.drop_table("game_sessions")
