"""El listado del banco para el panel: filtros, búsqueda y paginación.

Es el otro extremo de `question_bank`: aquel sirve preguntas a una partida y
esconde la respuesta; este las muestra todas —incluidas `draft` y `archived`—
para curarlas. La consulta y el conteo comparten los mismos filtros: si se
separan, el total deja de coincidir con lo que se ve en la página.
"""

from dataclasses import dataclass

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Question


@dataclass(frozen=True)
class QuestionPage:
    items: list[Question]
    total: int


def _search_pattern(texto: str) -> str:
    """`ILIKE` con los comodines del usuario escapados.

    Sin esto, buscar `%` devuelve el banco entero y `_` hace de comodín. El
    escape es el backslash, que también hay que escapar para que un `\\` escrito
    en el buscador se busque literal.
    """
    escapado = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"


async def list_questions(
    session: AsyncSession,
    *,
    status: str | None = None,
    category: str | None = None,
    difficulty: int | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> QuestionPage:
    filtros: list[ColumnElement[bool]] = []
    if status is not None:
        filtros.append(Question.status == status)
    if category is not None:
        filtros.append(Question.category == category)
    if difficulty is not None:
        filtros.append(Question.difficulty == difficulty)
    if q:
        filtros.append(Question.prompt.ilike(_search_pattern(q), escape="\\"))

    total = await session.scalar(
        select(func.count()).select_from(Question).where(*filtros)
    )
    filas = await session.execute(
        select(Question)
        # `id` desempata: dos preguntas importadas en el mismo INSERT comparten
        # `created_at` al microsegundo, y sin desempate la página 2 puede repetir
        # una fila de la 1.
        .where(*filtros)
        .order_by(Question.created_at.desc(), Question.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return QuestionPage(items=list(filas.scalars()), total=total or 0)
