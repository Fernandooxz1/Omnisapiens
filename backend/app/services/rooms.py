"""Creación y búsqueda de salas."""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.game.constants import ROOM_CODE_ALPHABET, ROOM_CODE_LENGTH
from app.models import Room, User
from app.runtime.room import RoomStatus

ROOM_CODE_ATTEMPTS = 5


class RoomCodeCollision(Exception):
    """Reintentos agotados por colisión de código: con 32^6 combinaciones, no ocurre."""


def generate_room_code() -> str:
    # `secrets` y no `random`: el código es la llave de la sala.
    return "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(ROOM_CODE_LENGTH))


def normalize_room_code(code: str) -> str:
    """El código tal como lo tipeó el usuario: sin espacios y en mayúsculas."""
    return code.strip().upper()


async def get_by_code(session: AsyncSession, code: str) -> Room | None:
    """La sala del código, o `None`. Un solo lugar normaliza (H-17).

    Lo usan el HTTP y el WebSocket: los dos tienen que aceptar el mismo `k7m2qp`
    que el usuario ve en pantalla.
    """
    return await session.scalar(
        select(Room).where(Room.code == normalize_room_code(code))
    )


def room_is_available(sala: Room, *, now: datetime | None = None) -> bool:
    """Si todavía se puede entrar.

    Una sala `expired` no vuelve, y una `waiting` con `expires_at` vencido tampoco
    (H-10): si no, abrir el WS la resucitaba en memoria y el código vencido seguía
    sirviendo. `playing` y `finished` siguen abiertas para reconectar/revancha.
    """
    if sala.status == RoomStatus.EXPIRED.value:
        return False
    ahora = now or datetime.now(UTC)
    return not (sala.status == RoomStatus.WAITING.value and sala.expires_at <= ahora)


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
