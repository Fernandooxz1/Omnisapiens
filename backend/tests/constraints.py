"""Los dos desenlaces posibles de un INSERT: pasa, o lo rechaza la base.

`rechaza` exige el **motivo** concreto (nombre del constraint, de la columna o
del tipo). Sin eso, un test que rompe dos cosas a la vez también pasaría y
dejaría de probar la regla que dice probar.

Se espera `DBAPIError` y no `IntegrityError` porque no todo lo que rechaza la
base es una violación de constraint: un texto más largo que el `varchar` llega
como `DataError`. En los dos casos el error viene de Postgres, que es lo que se
quiere demostrar.
"""

import re
from typing import Any

import pytest
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Base


async def acepta(session: AsyncSession, *filas: Any) -> None:
    """Inserta en orden de dependencia entre tablas.

    Sin `relationship()` en los modelos, el unit of work no deduce que `matches`
    va después de `users`: en un solo flush el INSERT de la partida sale primero
    y la FK lo rechaza. Un flush por tabla lo ordena sin depender del ORM.
    """
    for tabla in Base.metadata.sorted_tables:
        grupo = [fila for fila in filas if fila.__table__ is tabla]
        if grupo:
            session.add_all(grupo)
            await session.flush()
    await session.commit()


async def rechaza_al_confirmar(session: AsyncSession, motivo: str) -> None:
    """Para cambios ya aplicados en memoria: el rechazo aparece al confirmar."""
    with pytest.raises(DBAPIError, match=re.escape(motivo)):
        await session.commit()
    await session.rollback()


async def rechaza(session: AsyncSession, *filas: Any, motivo: str) -> None:
    session.add_all(filas)
    await rechaza_al_confirmar(session, motivo)
