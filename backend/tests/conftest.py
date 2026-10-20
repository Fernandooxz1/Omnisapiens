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
from collections.abc import AsyncIterator, Callable, Iterator
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import httpx
import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.api import rate_limit
from app.api.deps import get_session
from app.config import settings
from app.main import app

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DATABASE_NAME = "trivia_test"
TEST_REDIS_DB = 1

# La base de test es la de desarrollo con otro nombre: una sola URL que
# mantener (.env). Si cambia el host o el usuario, cambia para las dos.
TEST_URL = sa.make_url(settings.database_url).set(database=TEST_DATABASE_NAME)
TEST_URL_STR = TEST_URL.render_as_string(hide_password=False)

# Con Redis, lo mismo: el de desarrollo en otra base. Así un FLUSHDB de los tests
# no se lleva puesto el estado de una partida que esté corriendo en :6379/0.
TEST_REDIS_URL = urlunsplit(
    urlsplit(settings.redis_url)._replace(path=f"/{TEST_REDIS_DB}")
)


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
    return


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


@pytest.fixture(scope="session")
async def redis_test() -> AsyncIterator[Redis]:
    """Redis real, en una base aparte de la de desarrollo."""
    cliente = Redis.from_url(TEST_REDIS_URL, decode_responses=True)
    await cliente.flushdb()
    yield cliente
    await cliente.aclose()


@pytest.fixture
async def redis(redis_test: Redis) -> AsyncIterator[Redis]:
    """Redis no tiene rollback: lo que un test escribió, lo limpia el mismo test.

    Se limpia después y no antes para que un test que falle deje ver qué dejó.
    """
    yield redis_test
    await redis_test.flushdb()


@pytest.fixture(autouse=True)
async def _rate_limit_aislado(redis: Redis, monkeypatch: pytest.MonkeyPatch) -> None:
    """Los tests no comparten el contador de rate limit del Redis de desarrollo.

    Usan la base de test (que se vacía al final) y un límite alto: los tests que
    prueban el corte lo bajan a mano.
    """
    monkeypatch.setattr(rate_limit, "redis_client", redis)
    monkeypatch.setattr(rate_limit.settings, "rate_limit_guest_per_minute", 10_000)
    monkeypatch.setattr(rate_limit.settings, "rate_limit_room_per_minute", 10_000)
    monkeypatch.setattr(rate_limit.settings, "rate_limit_arcade_per_minute", 10_000)
    monkeypatch.setattr(rate_limit.settings, "rate_limit_session_per_minute", 10_000)


def _sesion_del_test(
    session: AsyncSession,
) -> Callable[[], AsyncIterator[AsyncSession]]:
    """La dependencia de reemplazo: devuelve la sesión del test y no la cierra."""

    async def _sesion() -> AsyncIterator[AsyncSession]:
        yield session

    return _sesion


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[httpx.AsyncClient]:
    """La API real con una sola cosa cambiada: la sesión de base.

    Se reemplaza `get_session` por la sesión del test, así el pedido entra en la
    misma transacción y el rollback del final deshace lo que escribió el endpoint.
    Sin esto, los tests de API ensuciarían la base y dependerían del orden.
    """
    app.dependency_overrides[get_session] = _sesion_del_test(session)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as cliente:
            yield cliente
    finally:
        app.dependency_overrides.clear()
