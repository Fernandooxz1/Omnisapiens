"""Altas de usuario. Hoy, la única que existe es la del invitado."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.security.nicks import clean_nick, random_nick

# 9000 nicks generados posibles: un choque es raro pero no imposible. Se reintenta
# en vez de confiar en la suerte.
NICK_ATTEMPTS = 5


class NickTaken(Exception):
    """El nick pedido ya lo tiene un usuario vivo."""


async def create_guest(session: AsyncSession, nick: str | None) -> User:
    """Da de alta un invitado y lo devuelve con su id ya puesto.

    Sin nick se genera uno: ahí un choque se reintenta, porque el nick no lo eligió
    nadie. Con nick, el choque es del usuario y sale como `NickTaken` para que la
    API conteste 409: cambiarle el nick por atrás sería mentirle.

    El único constraint único de `users` es el índice parcial del nick, así que un
    `IntegrityError` en este INSERT es un nick repetido y nada más.
    """
    pedido = None if nick is None else clean_nick(nick)
    for _ in range(1 if pedido is not None else NICK_ATTEMPTS):
        usuario = User(nick=pedido if pedido is not None else random_nick())
        session.add(usuario)
        try:
            await session.flush()
        except IntegrityError:
            # La sesión queda inservible después de un error de la base: sin el
            # rollback, el próximo flush arrastra la transacción abortada.
            await session.rollback()
        else:
            return usuario

    raise NickTaken
