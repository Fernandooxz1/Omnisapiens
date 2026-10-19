"""Contenido genérico: el ítem que se sirve y su solución, en tablas separadas.

La solución vive aparte a propósito: el camino público lee `content_items` y no
puede filtrarla con un `SELECT *`. `kind` no se limita a una lista porque los
modos se registran en código (`GameMode`), no en la base.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.game.constants import DIFFICULTY_MAX, DIFFICULTY_MIN
from app.models.base import Base
from app.models.checks import quoted_list

STATUSES = ("draft", "published", "archived")
MEDIA_TYPES = ("none", "image", "audio")


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(Text)
    schema_version: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[str] = mapped_column(String(16), server_default="draft")
    language: Mapped[str] = mapped_column(String(8), server_default="es")
    difficulty: Mapped[int] = mapped_column(SmallInteger)
    # Lista vacía, nunca NULL: el filtro por tag no arrastra un COALESCE.
    categories: Mapped[list[str]] = mapped_column(
        ARRAY(Text), server_default=text("'{}'")
    )

    payload: Mapped[dict[str, object]] = mapped_column(JSONB)
    media_type: Mapped[str] = mapped_column(String(16), server_default="none")
    media_url: Mapped[str | None] = mapped_column(Text)

    content_hash: Mapped[str] = mapped_column(String(64))
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("content_items.id")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("kind = btrim(kind) AND kind <> ''", name="kind_clean"),
        CheckConstraint(f"status IN ({quoted_list(STATUSES)})", name="status_known"),
        CheckConstraint(
            f"difficulty BETWEEN {DIFFICULTY_MIN} AND {DIFFICULTY_MAX}",
            name="difficulty_range",
        ),
        CheckConstraint("jsonb_typeof(payload) = 'object'", name="payload_object"),
        # `CASE` protege el cast: un payload sin `v` o con `v` de otro tipo tiene
        # que rechazarse por este constraint, no reventar con un error de parseo.
        CheckConstraint(
            "CASE WHEN jsonb_typeof(payload->'v') = 'number'"
            " THEN (payload->>'v')::numeric = schema_version"
            " ELSE false END",
            name="payload_version_matches_schema",
        ),
        CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="content_hash_hex"),
        CheckConstraint(
            f"media_type IN ({quoted_list(MEDIA_TYPES)})", name="media_type_known"
        ),
        CheckConstraint(
            "(media_type = 'none') = (media_url IS NULL)", name="media_consistent"
        ),
        UniqueConstraint("content_hash"),
        Index(None, "kind", "status", "difficulty"),
        Index(None, "categories", postgresql_using="gin"),
    )


class ContentSolution(Base):
    """La solución del ítem. `content_id` es PK: una solución por ítem."""

    __tablename__ = "content_solutions"

    content_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content_items.id", ondelete="CASCADE"), primary_key=True
    )
    payload: Mapped[dict[str, object]] = mapped_column(JSONB)
