import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, func, text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    # El default vive en Python (no en la base) para que el objeto tenga id antes
    # del flush y se pueda usar como FK de otros inserts en la misma transacción.
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nick: Mapped[str] = mapped_column(String(16))
    is_guest: Mapped[bool] = mapped_column(server_default=true())

    # Nulos en MVP: la cuenta real (Google, email) queda para después.
    email: Mapped[str | None] = mapped_column(String(255))
    provider: Mapped[str | None] = mapped_column(String(32))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        # El btrim acá no es cosmético: sin él un nick termina almacenado con
        # espacios y el único por nick deja pasar "juan" y "juan " como distintos.
        CheckConstraint(
            "nick = btrim(nick) AND char_length(nick) >= 1", name="nick_normalized"
        ),
        # Único entre vivos: un usuario borrado lógico libera su nick.
        Index(
            "uq_users_nick",
            "nick",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
