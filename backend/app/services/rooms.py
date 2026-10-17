"""Creación de salas. La consulta es tan chica que vive en el router."""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.game.constants import ROOM_CODE_ALPHABET, ROOM_CODE_LENGTH
from app.models import Room, User

ROOM_CODE_ATTEMPTS = 5


class RoomCodeCollision(Exception):
    """Reintentos agotados por colisión de código: con 32^6 combinaciones, no ocurre."""


def generate_room_code() -> str:
    # `secrets` y no `random`: el código es la llave de la sala.
    return "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(ROOM_CODE_LENGTH))


async def create_room(
    session: AsyncSession, host: User, *, rounds: int, seconds: int
) -> Room:
    config = {"rounds": rounds, "seconds": seconds}
    for _ in range(ROOM_CODE_ATTEMPTS):
        sala = Room(
            host_user_id=host.id,
            code=generate_room_code(),
            config=config,
            expires_at=datetime.now(UTC)
            + timedelta(seconds=settings.room_idle_timeout_seconds),
        )
        session.add(sala)
        try:
            await session.flush()
        except IntegrityError:
            # El único de `code` es el árbitro de la colisión, igual que el nick.
            await session.rollback()
            continue
        else:
            return sala
    raise RoomCodeCollision
