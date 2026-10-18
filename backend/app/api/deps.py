"""Lo que un endpoint necesita antes de empezar: la sesión y quién manda el pedido.

Son el interceptor que además inyecta el objeto: el endpoint declara `SessionDep`
o `OptionalUserDep` y FastAPI resuelve el resto.
"""

from collections.abc import AsyncIterator
from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ApiError
from app.config import settings
from app.db import session_factory
from app.models import User
from app.security.tokens import InvalidToken, read_guest_token


async def get_session() -> AsyncIterator[AsyncSession]:
    """Una sesión por pedido. Rollback si el pedido revienta; commit al final.

    Ojo con el orden: FastAPI cierra el `yield` **después** de emitir la respuesta
    (comprobado con 0.143), así que este commit no protege al cliente. Los
    endpoints que escriben commitean ellos, antes de responder; esto queda como
    red de seguridad para lo que se escriba sin commit explícito.
    """
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def authenticate(session: AsyncSession, token: str) -> User:
    """Un token → el usuario vivo, o `ApiError` 401.

    La única puerta de auth: la usan el header `Authorization` (HTTP) y el
    `?token=` del WebSocket. Dos transportes, una sola regla de identidad.
    """
    try:
        identidad = read_guest_token(token)
    except InvalidToken:
        raise ApiError(
            401, "AUTH_REQUIRED", "El token venció o no es válido."
        ) from None

    usuario = await session.get(User, identidad.user_id)
    # El borrado es lógico: la fila sigue ahí, pero el token ya no es de nadie.
    if usuario is None or usuario.deleted_at is not None:
        raise ApiError(401, "AUTH_REQUIRED", "El token venció o no es válido.")
    return usuario


async def get_optional_user(
    session: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
) -> User | None:
    """El usuario del header `Authorization: Bearer ...`, o `None` si no vino.

    Un token presente pero roto **no** se ignora: 401. Ignorarlo le entregaría al
    cliente un usuario nuevo sin avisarle de que perdió el suyo, y eso se descubre
    tarde, cuando ya jugó una partida como otro.
    """
    if authorization is None:
        return None
    return await authenticate(session, _bearer(authorization))


def _bearer(authorization: str) -> str:
    esquema, _, token = authorization.partition(" ")
    if esquema.lower() != "bearer" or not token:
        raise ApiError(
            401, "AUTH_REQUIRED", "Se espera `Authorization: Bearer <token>`."
        )
    return token


OptionalUserDep = Annotated[User | None, Depends(get_optional_user)]


async def get_current_user(usuario: OptionalUserDep) -> User:
    """La variante obligatoria: sin token válido el pedido no llega al endpoint."""
    if usuario is None:
        raise ApiError(401, "AUTH_REQUIRED", "Se necesita un token válido.")
    return usuario


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def require_admin(
    x_admin_token: Annotated[str | None, Header()] = None,
) -> None:
    """El pase del panel: `X-Admin-Token` igual al de la configuración.

    `compare_digest` compara en tiempo constante; un `!=` filtra cuántos bytes
    acertaste en el tiempo de respuesta. Se comparan bytes porque la versión de
    `str` explota con caracteres no ASCII, y el header es texto libre.

    Un token ausente y uno inválido dan el mismo 401: distinguirlos no le sirve
    a quien tiene el pase y le cuenta a quien lo busca.
    """
    if x_admin_token is not None and compare_digest(
        x_admin_token.encode("utf-8"), settings.admin_token.encode("utf-8")
    ):
        return
    raise ApiError(401, "ADMIN_REQUIRED", "Se necesita el token de administración.")
