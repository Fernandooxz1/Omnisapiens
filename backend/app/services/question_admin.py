"""El listado del contenido para el panel: filtros, búsqueda y paginación.

Es el otro extremo de `question_bank`: aquel sirve contenido a una partida y
esconde la solución; este lo muestra todo —incluidos `draft` y `archived`— para
curarlo. La consulta y el conteo comparten los mismos filtros: si se separan, el
total deja de coincidir con lo que se ve en la página.

Desde 2.3 lee `content_items`/`content_solutions`, no la tabla vieja. El filtro
`q` busca en `payload->>'prompt'` porque el único `ContentKind` implementado es
quiz; cuando haya otro, el kind tendrá que decir dónde buscar.
"""

from dataclasses import dataclass

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ContentItem, ContentSolution


@dataclass(frozen=True)
class ContentRow:
    """El ítem y su solución: el panel es la única vista que ve la respuesta."""

    item: ContentItem
    solution: ContentSolution


@dataclass(frozen=True)
class ContentPage:
    items: list[ContentRow]
    total: int


def _search_pattern(texto: str) -> str:
    """`ILIKE` con los comodines del usuario escapados.

    Sin esto, buscar `%` devuelve el banco entero y `_` hace de comodín. El
    escape es el backslash, que también hay que escapar para que un `\\` escrito
    en el buscador se busque literal.
    """
    escapado = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"


async def list_content(
    session: AsyncSession,
    *,
    kind: str,
    status: str | None = None,
    category: str | None = None,
    difficulty: int | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ContentPage:
    filtros: list[ColumnElement[bool]] = [ContentItem.kind == kind]
    if status is not None:
        filtros.append(ContentItem.status == status)
    if category is not None:
        filtros.append(ContentItem.categories.contains([category]))
    if difficulty is not None:
        filtros.append(ContentItem.difficulty == difficulty)
    if q:
        filtros.append(
            ContentItem.payload["prompt"].astext.ilike(_search_pattern(q), escape="\\")
        )

    total = await session.scalar(
        select(func.count()).select_from(ContentItem).where(*filtros)
    )
    filas = await session.execute(
        select(ContentItem, ContentSolution)
        .join(ContentSolution, ContentSolution.content_id == ContentItem.id)
        # `id` desempata: dos ítems importados en el mismo INSERT comparten
        # `created_at` al microsegundo, y sin desempate la página 2 puede repetir
        # una fila de la 1.
        .where(*filtros)
        .order_by(ContentItem.created_at.desc(), ContentItem.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return ContentPage(
        items=[
            ContentRow(item=item, solution=solution) for item, solution in filas.all()
        ],
        total=total or 0,
    )
