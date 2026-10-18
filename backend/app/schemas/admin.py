"""El panel de preguntas: la única vista que ve la respuesta correcta.

A diferencia de `RoundQuestion`, acá sí viaja `correct_index`: quien lista el
banco está curándolo, no jugando.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


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


class AdminQuestionPage(BaseModel):
    items: list[AdminQuestionOut]
    page: int
    # `page_size` y no `limit`: es el tamaño de la página, no un tope suelto.
    page_size: int
    total: int
    # `pages` viene calculado para que el cliente no repita la división (ni se
    # equivoque con el redondeo).
    pages: int
