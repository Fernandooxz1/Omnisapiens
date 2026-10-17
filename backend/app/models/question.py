import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
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

from app.game.constants import CATEGORIES, CHOICES, DIFFICULTY_MAX, DIFFICULTY_MIN
from app.models.base import Base

PROMPT_MAX_LENGTH = 300
STATUSES = ("draft", "published", "archived")
MEDIA_TYPES = ("none", "image", "audio")

_categories = ", ".join(f"'{category}'" for category in CATEGORIES)
_choices = ", ".join(str(choice) for choice in CHOICES)
_statuses = ", ".join(f"'{status}'" for status in STATUSES)
_media_types = ", ".join(f"'{media}'" for media in MEDIA_TYPES)


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    category: Mapped[str] = mapped_column(String(24))
    difficulty: Mapped[int] = mapped_column(SmallInteger)
    language: Mapped[str] = mapped_column(String(8), server_default="es")

    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[list[str]] = mapped_column(JSONB)
    correct_index: Mapped[int] = mapped_column(SmallInteger)

    explanation: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(16), server_default="draft")
    content_hash: Mapped[str] = mapped_column(String(64))

    media_type: Mapped[str] = mapped_column(String(16), server_default="none")
    media_url: Mapped[str | None] = mapped_column(Text)

    # Lista vacía, nunca NULL: si no, cada consulta futura por tag arrastra un COALESCE.
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=text("'{}'"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # onupdate es del lado de SQLAlchemy: mueve la fecha un UPDATE hecho por la app,
    # no uno a mano por psql (no hay trigger).
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(f"category IN ({_categories})", name="category_known"),
        CheckConstraint(
            f"difficulty BETWEEN {DIFFICULTY_MIN} AND {DIFFICULTY_MAX}",
            name="difficulty_range",
        ),
        CheckConstraint("language IN ('es')", name="language_known"),
        CheckConstraint(
            f"prompt = btrim(prompt) AND char_length(prompt) BETWEEN 1 AND {PROMPT_MAX_LENGTH}",
            name="prompt_clean",
        ),
        CheckConstraint(
            "jsonb_typeof(options) = 'array' AND jsonb_array_length(options) = 4",
            name="options_shape",
        ),
        # Cubre el tipo de cada elemento; que no estén vacías ni repetidas es de Python.
        CheckConstraint(
            """NOT jsonb_path_exists(options, '$[*] ? (@.type() != "string")')""",
            name="options_strings",
        ),
        CheckConstraint(f"correct_index IN ({_choices})", name="correct_index_choice"),
        CheckConstraint(f"status IN ({_statuses})", name="status_known"),
        CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="content_hash_hex"),
        CheckConstraint(f"media_type IN ({_media_types})", name="media_type_known"),
        CheckConstraint(
            "(media_type = 'none') = (media_url IS NULL)", name="media_consistent"
        ),
        UniqueConstraint("content_hash"),
        Index(None, "status", "category", "difficulty"),
    )
