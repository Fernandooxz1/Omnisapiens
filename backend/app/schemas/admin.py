"""El panel de contenido: la única vista que ve la respuesta correcta.

A diferencia de `RoundQuestion`, acá sí viaja `correct_index`: quien lista el
banco está curándolo, no jugando.

La respuesta conserva la forma de siempre (`AdminQuestionOut`) para no romper el
panel mientras el banco se muda a `content_items`. `source` y `tags` eran de la
tabla vieja y el contenido genérico no los guarda: salen `null` y `[]`.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.game.modes.quiz.models import QuizPayload, QuizSolution
from app.models import ContentItem, ContentSolution


class QuestionStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AdminQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: str
    difficulty: int
    prompt: str
    options: list[str]
    correct_index: int
    explanation: str | None
    source: str | None
    status: QuestionStatus
    media_type: str
    media_url: str | None
    tags: list[str]
    created_at: datetime
    updated_at: datetime


def admin_question(item: ContentItem, solution: ContentSolution) -> AdminQuestionOut:
    """Traduce el contenido genérico a la vista del panel.

    Es específico del quiz porque es el único kind implementado; cuando haya
    otro, cada `ContentKind` tendrá que aportar su propia vista.
    """
    public = QuizPayload.model_validate(item.payload)
    answer = QuizSolution.model_validate(solution.payload)
    return AdminQuestionOut(
        id=item.id,
        category=item.categories[0] if item.categories else "",
        difficulty=item.difficulty,
        prompt=public.prompt,
        options=list(public.options),
        correct_index=answer.correct_index,
        explanation=answer.explanation,
        source=None,
        status=QuestionStatus(item.status),
        media_type=item.media_type,
        media_url=item.media_url,
        tags=[],
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


class AdminQuestionPage(BaseModel):
    items: list[AdminQuestionOut]
    page: int
    # `page_size` y no `limit`: es el tamaño de la página, no un tope suelto.
    page_size: int
    total: int
    # `pages` viene calculado para que el cliente no repita la división (ni se
    # equivoque con el redondeo).
    pages: int


class RejectedRowOut(BaseModel):
    row: int
    reason: str


class ImportReportOut(BaseModel):
    """El mismo informe que imprime la CLI, para que la pantalla lo muestre igual."""

    total: int
    imported: int
    duplicated: int
    rejected: list[RejectedRowOut]
