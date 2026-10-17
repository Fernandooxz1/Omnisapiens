"""Entorno de Alembic: motor async (asyncpg) y metadatos de app.models.

La URL sale de `.env` (app.config.settings.database_url), la misma que usa la
API: si Alembic tuviera su propia copia, migrar y arrancar podrían apuntar a
bases distintas. `import app.models` es lo que llena `Base.metadata`; sin él
autogenerate vería una base vacía y propondría borrar todo.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Sin esto `alembic check` no nota un tipo o un server_default cambiado
        # y una migración incompleta pasa el control.
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # NullPool: Alembic es un proceso corto, no tiene sentido dejar conexiones
    # vivas después de migrar.
    engine = create_async_engine(settings.database_url, poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    raise SystemExit(
        "Modo offline (--sql) no configurado: las migraciones se aplican "
        "conectándose a la base. Pedilo si hace falta el SQL suelto."
    )

asyncio.run(run_async_migrations())
