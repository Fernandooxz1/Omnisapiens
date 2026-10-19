"""content

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-19 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "content_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("schema_version", sa.SmallInteger(), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default="draft", nullable=False
        ),
        sa.Column("language", sa.String(length=8), server_default="es", nullable=False),
        sa.Column("difficulty", sa.SmallInteger(), nullable=False),
        sa.Column(
            "categories",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "media_type", sa.String(length=16), server_default="none", nullable=False
        ),
        sa.Column("media_url", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("supersedes_id", sa.Uuid(), nullable=True),
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
            "kind = btrim(kind) AND kind <> ''",
            name=op.f("ck_content_items_kind_clean"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name=op.f("ck_content_items_status_known"),
        ),
        sa.CheckConstraint(
            "difficulty BETWEEN 1 AND 5",
            name=op.f("ck_content_items_difficulty_range"),
        ),
        sa.CheckConstraint(
            "jsonb_typeof(payload) = 'object'",
            name=op.f("ck_content_items_payload_object"),
        ),
        sa.CheckConstraint(
            "CASE WHEN jsonb_typeof(payload->'v') = 'number' THEN (payload->>'v')::numeric = schema_version ELSE false END",
            name=op.f("ck_content_items_payload_version_matches_schema"),
        ),
        sa.CheckConstraint(
            "content_hash ~ '^[0-9a-f]{64}$'",
            name=op.f("ck_content_items_content_hash_hex"),
        ),
        sa.CheckConstraint(
            "media_type IN ('none', 'image', 'audio')",
            name=op.f("ck_content_items_media_type_known"),
        ),
        sa.CheckConstraint(
            "(media_type = 'none') = (media_url IS NULL)",
            name=op.f("ck_content_items_media_consistent"),
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_id"],
            ["content_items.id"],
            name=op.f("fk_content_items_supersedes_id"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_content_items")),
        sa.UniqueConstraint("content_hash", name=op.f("uq_content_items_content_hash")),
    )
    op.create_index(
        op.f("ix_content_items_kind_status_difficulty"),
        "content_items",
        ["kind", "status", "difficulty"],
        unique=False,
    )
    op.create_index(
        op.f("ix_content_items_categories"),
        "content_items",
        ["categories"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_table(
        "content_solutions",
        sa.Column("content_id", sa.Uuid(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["content_id"],
            ["content_items.id"],
            name=op.f("fk_content_solutions_content_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("content_id", name=op.f("pk_content_solutions")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("content_solutions")
    op.drop_index(op.f("ix_content_items_categories"), table_name="content_items")
    op.drop_index(
        op.f("ix_content_items_kind_status_difficulty"), table_name="content_items"
    )
    op.drop_table("content_items")
