"""Lo que un endpoint necesita antes de empezar: la sesión y quién manda el pedido.

Son el interceptor que además inyecta el objeto: el endpoint declara `SessionDep`
o `OptionalUserDep` y FastAPI resuelve el resto.
"""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ApiError
from app.db import session_factory
from app.models import User
from app.security.tokens import InvalidToken, read_guest_token


async def get_session() -> AsyncIterator[AsyncSession]:
    """Una sesión por pedido, y el commit acá: el borde del pedido es el borde de
    la transacción. Un endpoint que escribe y se olvida del commit no pierde nada;
    uno que revienta a mitad no deja la mitad escrita."""
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


SessionDep = Annotated[AsyncSession, Depends(get_session)]


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

    try:
        identidad = read_guest_token(_bearer(authorization))
    except InvalidToken:
        raise ApiError(
            401, "AUTH_REQUIRED", "El token venció o no es válido."
        ) from None

    usuario = await session.get(User, identidad.user_id)
    # El borrado es lógico: la fila sigue ahí, pero el token ya no es de nadie.
    if usuario is None or usuario.deleted_at is not None:
        raise ApiError(401, "AUTH_REQUIRED", "El token venció o no es válido.")
    return usuario


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
