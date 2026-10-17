"""Rate limiting mínimo por IP, en Redis (H-09).

Ventana fija de un minuto: `INCR` y `EXPIRE` en la primera. No pretende ser justo
ni distribuido, sólo evitar que `/auth/guest` cree invitados sin tope y que se
puedan probar códigos de sala a fuerza bruta. Si Redis no contesta, se deja pasar
(mismo criterio que el historial del arcade: degradar, no romper) y queda el aviso
en el log.
"""

import logging

from fastapi import Request
from redis.exceptions import RedisError

from app.api.errors import ApiError
from app.config import settings
from app.redis import redis_client

logger = logging.getLogger(__name__)

WINDOW_SECONDS = 60


async def enforce(
    ip: str | None, *, bucket: str, limit: int, window_s: int = WINDOW_SECONDS
) -> None:
    cliente = ip or "desconocida"
    clave = f"rate:{bucket}:{cliente}"
    try:
        cuenta = await redis_client.incr(clave)
        if cuenta == 1:
            await redis_client.expire(clave, window_s)
    except RedisError:
        logger.warning("sin Redis no hay rate limit para %s", clave)
        return
    if cuenta > limit:
        raise ApiError(
            429, "RATE_LIMITED", "Demasiados pedidos seguidos. Esperá un momento."
        )


async def guest_limit(ip: str | None) -> None:
    await enforce(ip, bucket="guest", limit=settings.rate_limit_guest_per_minute)


async def room_limit(ip: str | None) -> None:
    await enforce(ip, bucket="room", limit=settings.rate_limit_room_per_minute)


async def arcade_limit(ip: str | None) -> None:
    await enforce(ip, bucket="arcade", limit=settings.rate_limit_arcade_per_minute)


async def guest_rate_limit(request: Request) -> None:
    await guest_limit(request.client.host if request.client else None)


async def room_rate_limit(request: Request) -> None:
    await room_limit(request.client.host if request.client else None)
