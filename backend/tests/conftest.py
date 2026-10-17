"""Base de datos real para los tests: Postgres, nunca SQLite.

SQLite no tiene `jsonb`, ni índices únicos parciales, ni `CHECK` con regex:
daría confianza falsa justo en las reglas que este proyecto hace cumplir en la
base. La base de test se llama `trivia_test` y se recrea en cada sesión.

Aislamiento: cada test corre dentro de una transacción que se revierte al
final. El `commit()` del código bajo prueba no la cierra: con
`join_transaction_mode="create_savepoint"` se convierte en un SAVEPOINT, así
que el rollback del fixture deshace todo sin limpieza entre tests. Lo que este
esquema no aísla es DDL y `TRUNCATE` dentro de un test: eso se commitea de
verdad (ningún test lo hace).
"""

import asyncio
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import settings

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DATABASE_NAME = "trivia_test"

# La base de test es la de desarrollo con otro nombre: una sola URL que
# mantener (.env). Si cambia el host o el usuario, cambia para las dos.
TEST_URL = sa.make_url(settings.database_url).set(database=TEST_DATABASE_NAME)
TEST_URL_STR = TEST_URL.render_as_string(hide_password=False)


async def _recreate_database() -> None:
    # Se entra por la base de mantenimiento porque no se puede DROPear la base
    # a la que estás conectado. AUTOCOMMIT porque DROP/CREATE DATABASE no
    # corren dentro de una transacción.
    admin = create_async_engine(
        TEST_URL.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    async with admin.connect() as connection:
        # FORCE desengancha lo que haya quedado colgado de una corrida anterior.
        await connection.execute(
            sa.text(f"DROP DATABASE IF EXISTS {TEST_DATABASE_NAME} WITH (FORCE)")
        )
        await connection.execute(sa.text(f"CREATE DATABASE {TEST_DATABASE_NAME}"))
    await admin.dispose()


@pytest.fixture(scope="session")
def database() -> Iterator[None]:
    """Base recién creada y migrada una vez por sesión.

    Síncrona a propósito: `alembic.command` corre su propio event loop, así que
    llamarla desde una fixture async rompería con "event loop is already running".
    """
    asyncio.run(_recreate_database())
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", TEST_URL_STR)
    command.upgrade(config, "head")
    yield


@pytest.fixture(scope="session")
async def engine(database: None) -> AsyncIterator[AsyncEngine]:
    # NullPool: cada test abre su propia conexión y la cierra, así ninguna
    # queda atada a un event loop ya terminado.
    engine = create_async_engine(TEST_URL_STR, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest.fixture
async def connection(engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            yield connection
        finally:
            await transaction.rollback()


@pytest.fixture
async def session(connection: AsyncConnection) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    ) as session:
        yield session
