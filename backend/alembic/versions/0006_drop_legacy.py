"""drop the legacy tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-20 12:00:00.000000

El historial vive en `game_sessions` desde la fase 3 y las dos superficies
(`arcade_runs` y `matches`) quedaron de solo lectura en las fases 4.2 y 5.3. Acá
se retiran: a partir de esta revisión hay una sola fuente de verdad.

El `downgrade` recrea las tablas vacías con las FKs que tenían en 0004b (a
`content_items`), suficiente para volver a la revisión anterior. Los datos no se
recuperan: el backfill a `game_sessions` ya había copiado el historial.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Primero las hijas: el orden inverso al de creación evita depender de
    # `CASCADE` al dropear tablas con FK entre sí.
    op.drop_table("arcade_answers")
    op.drop_table("match_rounds")
    op.drop_table("arcade_runs")
    op.drop_table("matches")
    op.drop_table("questions")


def downgrade() -> None:
    """Downgrade schema.

    Recrea el esquema tal como estaba en 0004b, sin filas.
    """
    op.create_table(
        "questions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(length=24), nullable=False),
        sa.Column("difficulty", sa.SmallInteger(), nullable=False),
        sa.Column("language", sa.String(length=8), server_default="es", nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("correct_index", sa.SmallInteger(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(length=16), server_default="draft", nullable=False
        ),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "media_type", sa.String(length=16), server_default="none", nullable=False
        ),
        sa.Column("media_url", sa.Text(), nullable=True),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(media_type = 'none') = (media_url IS NULL)",
            name=op.f("ck_questions_media_consistent"),
        ),
        sa.CheckConstraint(
            "category IN ('geography', 'history', 'science', 'art', 'entertainment', 'sports')",
            name=op.f("ck_questions_category_known"),
        ),
        sa.CheckConstraint(
            "content_hash ~ '^[0-9a-f]{64}$'",
            name=op.f("ck_questions_content_hash_hex"),
        ),
        sa.CheckConstraint(
            "jsonb_typeof(options) = 'array' AND jsonb_array_length(options) = 4",
            name=op.f("ck_questions_options_shape"),
        ),
        sa.CheckConstraint(
            "language IN ('es')", name=op.f("ck_questions_language_known")
        ),
        sa.CheckConstraint(
            "media_type IN ('none', 'image', 'audio')",
            name=op.f("ck_questions_media_type_known"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name=op.f("ck_questions_status_known"),
        ),
        sa.CheckConstraint(
            "NOT jsonb_path_exists(options, '$[*] ? (@.type() != \"string\")')",
            name=op.f("ck_questions_options_strings"),
        ),
        sa.CheckConstraint(
            "correct_index IN (0, 1, 2, 3)",
            name=op.f("ck_questions_correct_index_choice"),
        ),
        sa.CheckConstraint(
            "difficulty BETWEEN 1 AND 5", name=op.f("ck_questions_difficulty_range")
        ),
        sa.CheckConstraint(
            "prompt = btrim(prompt) AND char_length(prompt) BETWEEN 1 AND 300",
            name=op.f("ck_questions_prompt_clean"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_questions")),
        sa.UniqueConstraint("content_hash", name=op.f("uq_questions_content_hash")),
    )
    op.create_index(
        op.f("ix_questions_status_category_difficulty"),
        "questions",
        ["status", "category", "difficulty"],
        unique=False,
    )
    op.create_table(
        "arcade_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
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
            "status", sa.String(length=16), server_default="playing", nullable=False
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
            name=op.f("ck_arcade_runs_ending_matches_status"),
        ),
        sa.CheckConstraint(
            "status IN ('playing', 'finished', 'invalid')",
            name=op.f("ck_arcade_runs_status_known"),
        ),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name=op.f("ck_arcade_runs_ends_after_start"),
        ),
        sa.CheckConstraint(
            "longest_streak BETWEEN 0 AND correct_count",
            name=op.f("ck_arcade_runs_streak_within_corrects"),
        ),
        sa.CheckConstraint(
            "max_difficulty BETWEEN 1 AND 5",
            name=op.f("ck_arcade_runs_difficulty_range"),
        ),
        sa.CheckConstraint(
            "score >= 0 AND correct_count >= 0",
            name=op.f("ck_arcade_runs_counters_not_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_arcade_runs_user_id")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_arcade_runs")),
    )
    op.create_index(
        "ix_arcade_runs_best_by_user",
        "arcade_runs",
        ["user_id", sa.literal_column("score DESC")],
        unique=False,
        postgresql_where=sa.text("status = 'finished'"),
    )
    op.create_index(
        "ix_arcade_runs_ranking",
        "arcade_runs",
        [sa.literal_column("score DESC")],
        unique=False,
        postgresql_where=sa.text("status = 'finished'"),
    )
    op.create_index(
        op.f("ix_arcade_runs_status_started_at"),
        "arcade_runs",
        ["status", "started_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_arcade_runs_user_id"), "arcade_runs", ["user_id"], unique=False
    )
    op.create_index(
        "ix_arcade_runs_weekly",
        "arcade_runs",
        ["ended_at"],
        unique=False,
        postgresql_where=sa.text("status = 'finished'"),
    )
    op.create_table(
        "matches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=True),
        sa.Column("player_a_id", sa.Uuid(), nullable=False),
        sa.Column("player_b_id", sa.Uuid(), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default="playing", nullable=False
        ),
        sa.Column("score_a", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("score_b", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("winner_id", sa.Uuid(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "jsonb_typeof(config) = 'object' AND jsonb_typeof(config->'rounds') IS NOT DISTINCT FROM 'number' AND jsonb_typeof(config->'seconds') IS NOT DISTINCT FROM 'number' AND (config->>'rounds') IN ('3', '5', '7') AND (config->>'seconds') IN ('10', '20', '30')",
            name=op.f("ck_matches_config_valid"),
        ),
        sa.CheckConstraint(
            "status IN ('playing', 'finished', 'abandoned', 'void')",
            name=op.f("ck_matches_status_known"),
        ),
        sa.CheckConstraint(
            "player_a_id <> player_b_id", name=op.f("ck_matches_players_differ")
        ),
        sa.CheckConstraint(
            "score_a >= 0 AND score_b >= 0", name=op.f("ck_matches_scores_not_negative")
        ),
        sa.CheckConstraint(
            "winner_id IS NULL OR winner_id IN (player_a_id, player_b_id)",
            name=op.f("ck_matches_winner_plays"),
        ),
        sa.ForeignKeyConstraint(
            ["player_a_id"], ["users.id"], name=op.f("fk_matches_player_a_id")
        ),
        sa.ForeignKeyConstraint(
            ["player_b_id"], ["users.id"], name=op.f("fk_matches_player_b_id")
        ),
        sa.ForeignKeyConstraint(
            ["room_id"],
            ["rooms.id"],
            name=op.f("fk_matches_room_id"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["winner_id"], ["users.id"], name=op.f("fk_matches_winner_id")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_matches")),
    )
    op.create_index(
        op.f("ix_matches_player_a_id"), "matches", ["player_a_id"], unique=False
    )
    op.create_index(
        op.f("ix_matches_player_b_id"), "matches", ["player_b_id"], unique=False
    )
    op.create_index(op.f("ix_matches_room_id"), "matches", ["room_id"], unique=False)
    op.create_index(
        op.f("ix_matches_status_started_at"),
        "matches",
        ["status", "started_at"],
        unique=False,
    )
    op.create_table(
        "arcade_answers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("round_index", sa.SmallInteger(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=True),
        sa.Column("difficulty", sa.SmallInteger(), nullable=False),
        sa.Column("seconds", sa.SmallInteger(), nullable=False),
        sa.Column("correct_index", sa.SmallInteger(), nullable=False),
        sa.Column("chosen_index", sa.SmallInteger(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("ms", sa.Integer(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("rejected", sa.String(length=24), nullable=True),
        sa.CheckConstraint(
            "rejected IS NULL OR rejected IN ('outside_window')",
            name=op.f("ck_arcade_answers_rejection_known"),
        ),
        sa.CheckConstraint(
            "chosen_index IS NULL OR chosen_index IN (0, 1, 2, 3)",
            name=op.f("ck_arcade_answers_chosen_in_range"),
        ),
        sa.CheckConstraint(
            "correct_index IN (0, 1, 2, 3)",
            name=op.f("ck_arcade_answers_correct_index_choice"),
        ),
        sa.CheckConstraint(
            "difficulty BETWEEN 1 AND 5",
            name=op.f("ck_arcade_answers_difficulty_range"),
        ),
        sa.CheckConstraint(
            "is_correct = (chosen_index IS NOT NULL AND chosen_index = correct_index)",
            name=op.f("ck_arcade_answers_correctness_from_choice"),
        ),
        sa.CheckConstraint(
            "ms BETWEEN 0 AND seconds * 1000",
            name=op.f("ck_arcade_answers_ms_within_window"),
        ),
        sa.CheckConstraint(
            "points >= 0", name=op.f("ck_arcade_answers_points_not_negative")
        ),
        sa.CheckConstraint(
            "rejected IS NULL OR chosen_index IS NULL",
            name=op.f("ck_arcade_answers_rejected_without_choice"),
        ),
        sa.CheckConstraint(
            "round_index >= 0", name=op.f("ck_arcade_answers_round_index_not_negative")
        ),
        sa.CheckConstraint(
            "seconds > 0", name=op.f("ck_arcade_answers_seconds_positive")
        ),
        # En 0004b la FK se repuntó a `content_items`.
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["content_items.id"],
            name=op.f("fk_arcade_answers_question_id"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["arcade_runs.id"],
            name=op.f("fk_arcade_answers_run_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_arcade_answers")),
        sa.UniqueConstraint(
            "run_id", "round_index", name=op.f("uq_arcade_answers_run_id_round_index")
        ),
    )
    op.create_table(
        "match_rounds",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("match_id", sa.Uuid(), nullable=False),
        sa.Column("round_index", sa.SmallInteger(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=True),
        sa.Column("difficulty", sa.SmallInteger(), nullable=False),
        sa.Column("seconds", sa.SmallInteger(), nullable=False),
        sa.Column("correct_index", sa.SmallInteger(), nullable=False),
        sa.Column("a_choice", sa.SmallInteger(), nullable=True),
        sa.Column("b_choice", sa.SmallInteger(), nullable=True),
        sa.Column("a_ms", sa.Integer(), nullable=True),
        sa.Column("b_ms", sa.Integer(), nullable=True),
        sa.Column("a_correct", sa.Boolean(), nullable=False),
        sa.Column("b_correct", sa.Boolean(), nullable=False),
        sa.Column("a_points", sa.Integer(), nullable=False),
        sa.Column("b_points", sa.Integer(), nullable=False),
        sa.Column("a_rejected", sa.String(length=24), nullable=True),
        sa.Column("b_rejected", sa.String(length=24), nullable=True),
        sa.CheckConstraint(
            "(a_rejected IS NULL OR a_rejected IN ('outside_window')) AND (b_rejected IS NULL OR b_rejected IN ('outside_window')) AND (a_rejected IS NULL OR a_choice IS NULL) AND (b_rejected IS NULL OR b_choice IS NULL)",
            name=op.f("ck_match_rounds_rejections_consistent"),
        ),
        sa.CheckConstraint(
            "(a_choice IS NULL OR a_choice IN (0, 1, 2, 3)) AND (b_choice IS NULL OR b_choice IN (0, 1, 2, 3))",
            name=op.f("ck_match_rounds_choices_in_range"),
        ),
        sa.CheckConstraint(
            "(a_choice IS NULL) = (a_ms IS NULL) AND (b_choice IS NULL) = (b_ms IS NULL) AND (a_ms IS NULL OR (a_ms >= 0 AND a_ms <= seconds * 1000)) AND (b_ms IS NULL OR (b_ms >= 0 AND b_ms <= seconds * 1000))",
            name=op.f("ck_match_rounds_times_consistent"),
        ),
        sa.CheckConstraint(
            "a_correct = (a_choice IS NOT NULL AND a_choice = correct_index) AND b_correct = (b_choice IS NOT NULL AND b_choice = correct_index)",
            name=op.f("ck_match_rounds_correctness_from_choice"),
        ),
        sa.CheckConstraint(
            "a_points >= 0 AND b_points >= 0",
            name=op.f("ck_match_rounds_points_not_negative"),
        ),
        sa.CheckConstraint(
            "correct_index IN (0, 1, 2, 3)",
            name=op.f("ck_match_rounds_correct_index_choice"),
        ),
        sa.CheckConstraint(
            "difficulty BETWEEN 1 AND 5", name=op.f("ck_match_rounds_difficulty_range")
        ),
        sa.CheckConstraint(
            "round_index >= 0", name=op.f("ck_match_rounds_round_index_not_negative")
        ),
        sa.CheckConstraint(
            "seconds > 0", name=op.f("ck_match_rounds_seconds_positive")
        ),
        sa.ForeignKeyConstraint(
            ["match_id"],
            ["matches.id"],
            name=op.f("fk_match_rounds_match_id"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["content_items.id"],
            name=op.f("fk_match_rounds_question_id"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_match_rounds")),
        sa.UniqueConstraint(
            "match_id", "round_index", name=op.f("uq_match_rounds_match_id_round_index")
        ),
    )
