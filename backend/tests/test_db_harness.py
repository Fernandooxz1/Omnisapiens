"""El andamiaje de base real: que migre y que aísle.

Es el test de las dos cosas que, si se rompen, hacen que los otros cien tests
midan cualquier cosa: la migración aplicada y el rollback por test.
"""

from sqlalchemy import func, inspect, select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from app.models import User

from .constraints import acepta
from .factories import user

TABLAS = {
    "alembic_version",
    "content_items",
    "content_solutions",
    "game_participants",
    "game_sessions",
    "rooms",
    "session_attempts",
    "session_items",
    "users",
}


async def test_migration_creates_every_table(connection: AsyncConnection) -> None:
    tablas = await connection.run_sync(lambda c: inspect(c).get_table_names())

    assert set(tablas) == TABLAS


async def test_a_row_written_in_a_test_is_readable(session: AsyncSession) -> None:
    await acepta(session, user(nick="fernando"))

    vivos = await session.scalar(select(func.count()).select_from(User))
    assert vivos == 1


async def test_a_row_from_another_test_does_not_survive(session: AsyncSession) -> None:
    # Depende a propósito del test de arriba: si el rollback del fixture no
    # funcionara, esta fila seguiría estando. Dentro de un archivo, pytest corre
    # los tests en el orden en que están definidos.
    vivos = await session.scalar(select(func.count()).select_from(User))

    assert vivos == 0
