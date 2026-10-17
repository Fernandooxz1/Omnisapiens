"""El andamiaje de base real: que migre, que aísle y que los `CHECK` estén vivos.

Es el test de las tres cosas que, si se rompen, hacen que los otros 100 tests
mientan: la migración aplicada, el rollback por test y los constraints
realmente creados en la base.
"""

from typing import Any

import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from app.models import Question, User

TABLAS = {
    "alembic_version",
    "arcade_answers",
    "arcade_runs",
    "match_rounds",
    "matches",
    "questions",
    "rooms",
    "users",
}


def _question(**overrides: Any) -> Question:
    return Question(
        **{
            "category": "science",
            "difficulty": 3,
            "prompt": "¿Cuántos planetas tiene el sistema solar?",
            "options": ["7", "8", "9", "10"],
            "correct_index": 1,
            "content_hash": "a" * 64,
        }
        | overrides
    )


async def test_la_migracion_dejo_todas_las_tablas(connection: AsyncConnection) -> None:
    tablas = await connection.run_sync(lambda c: inspect(c).get_table_names())
    assert set(tablas) == TABLAS


async def test_una_fila_escrita_se_lee_en_el_mismo_test(session: AsyncSession) -> None:
    session.add(User(nick="fernando"))
    await session.commit()

    vivos = await session.scalar(select(func.count()).select_from(User))
    assert vivos == 1


async def test_lo_escrito_por_otro_test_no_sobrevive(session: AsyncSession) -> None:
    # Depende a propósito del test de arriba: si el rollback del fixture no
    # funcionara, esta fila seguiría estando. Dentro de un archivo, pytest
    # corre los tests en el orden en que están definidos.
    vivos = await session.scalar(select(func.count()).select_from(User))
    assert vivos == 0


async def test_un_check_rechaza_la_fila_invalida(session: AsyncSession) -> None:
    session.add(_question(difficulty=9))

    with pytest.raises(IntegrityError, match="ck_questions_difficulty_range"):
        await session.commit()
    await session.rollback()
