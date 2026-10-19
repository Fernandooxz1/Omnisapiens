"""Guardia contra el drift de schema: la base migrada == los modelos.

`alembic check` compara modelos contra base, pero **no mira los `CHECK`** (ni
agregados, ni cambiados, ni renombrados, ni borrados): se verificó a mano y es
ciego en las cuatro formas. Como las reglas de negocio de este proyecto viven
en `CHECK`, esa ceguera es justo donde no se puede fallar.

Este test tapa el agujero: crea un schema descartable con el DDL que compilan
los modelos y compara el inventario de constraints e índices contra la base
migrada. Compara el *cuerpo* de cada constraint, no solo el nombre, así que un
`CHECK` escrito distinto se ve.

Lo que cubre `alembic check` (tablas, columnas, tipos, defaults, FK) no se
duplica acá: si eso cambia, falla el check y este test sigue verde.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.schema import CreateIndex, CreateTable

from app.models import Base

ESQUEMA_MODELOS = "ddl_de_los_modelos"

# Se compila una vez, al importar: es el DDL que SQLAlchemy deduce de los
# modelos, el mismo que se fue comparando a mano contra cada migración.
DDL_DE_LOS_MODELOS = [
    str(CreateTable(tabla).compile(dialect=postgresql.dialect())).strip()
    for tabla in Base.metadata.sorted_tables
] + [
    str(CreateIndex(indice).compile(dialect=postgresql.dialect())).strip()
    for tabla in Base.metadata.sorted_tables
    for indice in tabla.indexes
]

_INVENTARIO = sa.text(
    """
    SELECT c.relname || '|' || con.conname || '|' || pg_get_constraintdef(con.oid)
    FROM pg_constraint con
    JOIN pg_class c ON c.oid = con.conrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = :esquema AND c.relname <> 'alembic_version'
    UNION ALL
    SELECT indexname || '|' || indexdef
    FROM pg_indexes
    WHERE schemaname = :esquema AND tablename <> 'alembic_version'
    ORDER BY 1
    """
)


def _sin_esquema(definicion: str, esquema: str) -> str:
    # Postgres califica el nombre cuando la referencia no está en el
    # search_path: el mismo constraint sale "REFERENCES s.questions" adentro
    # de un schema propio y "REFERENCES questions" en public. Se compara el
    # contenido, no el nombre del schema.
    return definicion.replace(f"{esquema}.", "")


async def _inventario(connection: AsyncConnection, esquema: str) -> set[str]:
    filas = await connection.execute(_INVENTARIO, {"esquema": esquema})
    return {_sin_esquema(fila[0], esquema) for fila in filas}


async def test_migrated_schema_matches_the_models(
    connection: AsyncConnection,
) -> None:
    await connection.execute(
        sa.text(f"DROP SCHEMA IF EXISTS {ESQUEMA_MODELOS} CASCADE")
    )
    await connection.execute(sa.text(f"CREATE SCHEMA {ESQUEMA_MODELOS}"))
    # Los CREATE TABLE van sin calificar: el search_path decide dónde caen, y
    # las FK se resuelven entre tablas del mismo schema. SET LOCAL es de la
    # transacción, así que el rollback del fixture se lleva todo el schema.
    await connection.execute(sa.text(f"SET LOCAL search_path = {ESQUEMA_MODELOS}"))
    for sentencia in DDL_DE_LOS_MODELOS:
        await connection.execute(sa.text(sentencia))
    await connection.execute(sa.text("SET LOCAL search_path = public"))

    de_los_modelos = await _inventario(connection, ESQUEMA_MODELOS)
    de_la_base = await _inventario(connection, "public")

    assert de_la_base == de_los_modelos, (
        f"constraints e índices que están en los modelos y faltan en la base"
        f" (migración sin escribir): {sorted(de_los_modelos - de_la_base)}\n"
        f"constraints e índices que están en la base y ya no en los modelos"
        f": {sorted(de_la_base - de_los_modelos)}"
    )
