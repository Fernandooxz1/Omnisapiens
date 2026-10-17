"""`users`: la forma del nick y el único parcial que permite reusarlo."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from .constraints import acepta, rechaza
from .factories import user


async def test_a_nick_is_accepted(session: AsyncSession) -> None:
    await acepta(session, user(nick="juan"))


async def test_a_nick_of_16_characters_is_accepted(session: AsyncSession) -> None:
    await acepta(session, user(nick="a" * 16))


async def test_two_different_nicks_are_accepted(session: AsyncSession) -> None:
    await acepta(session, user(nick="juan"), user(nick="ana"))


async def test_a_repeated_nick_is_rejected(session: AsyncSession) -> None:
    await acepta(session, user(nick="juan"))

    await rechaza(session, user(nick="juan"), motivo="uq_users_nick")


async def test_a_nick_of_17_characters_is_rejected(session: AsyncSession) -> None:
    # No es un CHECK: lo corta el tipo. El mensaje nombra la columna, no un constraint.
    await rechaza(session, user(nick="a" * 17), motivo="character varying(16)")


async def test_a_nick_with_a_trailing_space_is_rejected(session: AsyncSession) -> None:
    await rechaza(session, user(nick="pedro "), motivo="ck_users_nick_normalized")


async def test_an_empty_nick_is_rejected(session: AsyncSession) -> None:
    await rechaza(session, user(nick=""), motivo="ck_users_nick_normalized")


async def test_a_nick_of_only_spaces_is_rejected(session: AsyncSession) -> None:
    await rechaza(session, user(nick="   "), motivo="ck_users_nick_normalized")


async def test_a_soft_deleted_user_frees_its_nick(session: AsyncSession) -> None:
    ana = user(nick="ana")
    await acepta(session, ana)

    ana.deleted_at = datetime.now(UTC)
    await session.commit()

    await acepta(session, user(nick="ana"))


async def test_a_deleted_user_does_not_free_a_live_nick(session: AsyncSession) -> None:
    # El único es parcial (solo entre vivos): tener una fila borrada no habilita
    # repetir el nick de una que sigue viva.
    borrada = user(nick="ana")
    borrada.deleted_at = datetime.now(UTC)
    await acepta(session, user(nick="juan"), borrada)

    await rechaza(session, user(nick="juan"), motivo="uq_users_nick")


async def test_defaults_of_a_new_user(session: AsyncSession) -> None:
    juan = user(nick="juan")

    await acepta(session, juan)

    assert juan.is_guest is True
    assert juan.created_at is not None
    assert juan.last_seen_at is not None
    assert juan.deleted_at is None
