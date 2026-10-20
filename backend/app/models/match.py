"""La sala: el lobby de una partida online.

Desde la fase 10 la tabla es la única que queda de la unidad "partida": el
historial vive en `game_sessions` desde la fase 3. `rooms` sigue siendo la tabla
del lobby y el borde mantiene su estado y el techo de vencimiento.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.game.constants import ROOM_CODE_ALPHABET, ROOM_CODE_LENGTH
from app.models.base import Base
from app.models.checks import quoted_list

ROOM_STATUSES = ("waiting", "playing", "finished", "expired")


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # El host es quien crea la sala, y no "el primero que entra": la fila vive más
    # que las conexiones, así que una reconexión no cambia de dueño la sala.
    host_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    # varchar y no char: char(n) rellena con espacios y compara raro.
    code: Mapped[str] = mapped_column(String(ROOM_CODE_LENGTH))
    mode: Mapped[str] = mapped_column(Text, server_default="trivia_versus")
    # El modo valida el contenido del config con su `config_schema`; la base
    # solo exige que sea un objeto para no atarse a un formato por modo.
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
        # Desde la fase 3 el config depende del modo de la sala; los valores
        # se validan con el esquema del modo en Python (pérdida deliberada de
        # rigidez, compensada por los tests de contrato de la API).
        CheckConstraint("jsonb_typeof(config) = 'object'", name="config_valid"),
        UniqueConstraint("code"),
        # Índice de FK (Postgres no lo crea solo): "las salas que creé" y el
        # chequeo de la FK no barren la tabla.
        Index(None, "host_user_id"),
        # Lo que busca el barrendero: salas vivas con la fecha vencida.
        Index(None, "status", "expires_at"),
    )
