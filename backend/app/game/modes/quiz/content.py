"""El `ContentKind` del quiz: fila → payload público, y la base → `LoadedItem`.

La validación de una fila vive acá y no en el importador: el tipo de contenido es
el que sabe qué es una pregunta válida (categoría conocida, dificultad 1-5,
cuatro opciones no vacías y distintas). El importador solo aporta el archivo y el
estado con el que se guarda.

El barajado de opciones vive en `question_bank`, junto con el resto de lo que ve
el jugador; lo que este módulo garantiza es que el tipo público (`QuizPayload`)
no tiene `correct_index`.
"""

import hashlib
import unicodedata
import uuid
from collections.abc import Mapping
from typing import Any, cast

from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.game.constants import CATEGORIES, DIFFICULTY_MAX, DIFFICULTY_MIN
from app.game.modes.base import (
    ContentDraft,
    ItemRef,
    LoadedItem,
    PublicItem,
    Solution,
)
from app.game.modes.quiz.models import (
    QUIZ_PROMPT_MAX_LENGTH,
    QUIZ_SCHEMA_VERSION,
    QuizCandidatesConfig,
    QuizPayload,
    QuizSolution,
)
from app.models import ContentItem, ContentSolution

# El formato del archivo (§13.1 del plan). Va acá porque las columnas son del
# quiz: `option_a..d` y `correct` en letras no significan nada para otro kind.
COLUMNS = (
    "category",
    "difficulty",
    "prompt",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct",
    "explanation",
    "source",
    "tags",
)
OPTION_KEYS = ("option_a", "option_b", "option_c", "option_d")
REQUIRED = ("category", "difficulty", "prompt", *OPTION_KEYS, "correct")
CORRECT_LETTERS = {"A": 0, "B": 1, "C": 2, "D": 3}


class RowError(Exception):
    """Una fila no pasa la validación; el mensaje es el motivo que se informa."""


def normalize_prompt(prompt: str) -> str:
    """El enunciado en una forma comparable: sin tildes, sin signos, en
    minúsculas y con los espacios de adentro colapsados.

    Se pliegan los acentos (NFKD y se tiran los diacríticos) para que "¿Cuál es
    el río?" y "Cual es el rio?" sean la misma pregunta. Es solo para comparar:
    lo que se guarda es el enunciado tal como lo escribió el autor.
    """
    descompuesto = unicodedata.normalize("NFKD", prompt)
    sin_tildes = "".join(
        c for c in descompuesto if not unicodedata.combining(c)
    ).lower()
    sin_signos = "".join(c if c.isalnum() else " " for c in sin_tildes)
    return " ".join(sin_signos.split())


def content_hash(prompt: str) -> str:
    """SHA-256 del enunciado normalizado: es la clave del `UNIQUE` de la tabla."""
    return hashlib.sha256(normalize_prompt(prompt).encode("utf-8")).hexdigest()


def _text(raw: Any) -> str:
    return "" if raw is None else str(raw).strip()


def _is_number(raw: str) -> bool:
    return raw.lstrip("+-").isdigit()


class QuizContent:
    """El contenido de trivia de cuatro opciones."""

    code = "quiz"
    schema_version = QUIZ_SCHEMA_VERSION

    def parse_row(self, raw: Mapping[str, Any]) -> ContentDraft:
        """Valida una fila cruda y la convierte en `ContentDraft`.

        Levanta `RowError` con un motivo legible; el importador lo informa con la
        línea exacta en vez de dejar reventar un `IntegrityError`.
        """
        category = _text(raw.get("category"))
        if not category:
            raise RowError("falta la categoría")
        if category not in CATEGORIES:
            raise RowError(f"categoría desconocida: {category!r}")

        dificultad_texto = _text(raw.get("difficulty"))
        if not dificultad_texto:
            raise RowError("falta la dificultad")
        if not _is_number(dificultad_texto):
            raise RowError(f"la dificultad {dificultad_texto!r} no es un número")
        difficulty = int(dificultad_texto)
        if not DIFFICULTY_MIN <= difficulty <= DIFFICULTY_MAX:
            raise RowError(
                f"la dificultad {difficulty} está fuera de "
                f"{DIFFICULTY_MIN}-{DIFFICULTY_MAX}"
            )

        prompt = _text(raw.get("prompt"))
        if not prompt:
            raise RowError("el enunciado está vacío")
        if len(prompt) > QUIZ_PROMPT_MAX_LENGTH:
            raise RowError(
                f"el enunciado tiene {len(prompt)} caracteres "
                f"(máximo {QUIZ_PROMPT_MAX_LENGTH})"
            )

        options = []
        for clave in OPTION_KEYS:
            opcion = _text(raw.get(clave))
            if not opcion:
                raise RowError(f"la opción {clave[-1].upper()} está vacía")
            options.append(opcion)
        if len({opcion.casefold() for opcion in options}) < len(options):
            raise RowError("hay opciones repetidas")

        correct = _text(raw.get("correct")).upper()
        if correct not in CORRECT_LETTERS:
            raise RowError("la respuesta correcta debe ser A, B, C o D")

        try:
            public = QuizPayload(prompt=prompt, options=options)
            solution = QuizSolution(
                correct_index=CORRECT_LETTERS[correct],
                explanation=_text(raw.get("explanation")) or None,
            )
        except ValidationError as exc:
            # Los chequeos de arriba ya cubren el contrato; si algo se escapa, el
            # motivo tiene que ser legible igual.
            raise RowError(exc.errors()[0]["msg"]) from None

        return ContentDraft(
            schema_version=self.schema_version,
            public=PublicItem(
                payload=public.model_dump(),
                media_type=public.media.type,
                media_url=public.media.url,
            ),
            solution=Solution(payload=solution.model_dump()),
            difficulty=difficulty,
            categories=(category,),
        )

    def fingerprint(self, draft: ContentDraft) -> str:
        """El hash congelado del quiz: el enunciado normalizado.

        Es el mismo `content_hash` que usaba `questions`, así el backfill y una
        importación nueva no pueden duplicar la misma pregunta.
        """
        return content_hash(_prompt_of(draft))

    async def candidates(
        self, session: AsyncSession, *, config: BaseModel
    ) -> list[ItemRef]:
        """Los ítems publicados del tramo pedido, sin cargar payloads."""
        ajustes = QuizCandidatesConfig.model_validate(config.model_dump())
        consulta = select(
            ContentItem.id, ContentItem.difficulty, ContentItem.categories
        ).where(
            ContentItem.kind == self.code,
            ContentItem.status == "published",
        )
        if ajustes.low is not None:
            consulta = consulta.where(ContentItem.difficulty >= ajustes.low)
        if ajustes.high is not None:
            consulta = consulta.where(ContentItem.difficulty <= ajustes.high)

        filas = await session.execute(consulta)
        return [
            ItemRef(
                content_id=str(content_id),
                difficulty=difficulty,
                categories=tuple(categories or ()),
            )
            for content_id, difficulty, categories in filas
        ]

    async def load(self, session: AsyncSession, ref: ItemRef) -> LoadedItem:
        """Carga el ítem y su solución. La solución no sale de este módulo."""
        try:
            content_id = uuid.UUID(ref.content_id)
        except ValueError:
            raise KeyError(f"id de contenido inválido: {ref.content_id!r}") from None

        item = await session.get(ContentItem, content_id)
        if item is None or item.kind != self.code:
            raise KeyError(f"contenido inexistente para {self.code}: {ref.content_id}")

        solution = await session.get(ContentSolution, content_id)
        if solution is None:
            raise KeyError(f"el contenido {ref.content_id} no tiene solución")

        public = QuizPayload.model_validate(item.payload)
        answer = QuizSolution.model_validate(solution.payload)
        return LoadedItem(
            content_id=str(item.id),
            public=PublicItem(
                payload=public.model_dump(),
                media_type=item.media_type,
                media_url=item.media_url,
            ),
            solution=Solution(payload=answer.model_dump()),
        )


def _prompt_of(draft: ContentDraft) -> str:
    payload = cast("dict[str, Any]", draft.public.payload)
    prompt = payload.get("prompt")
    if not isinstance(prompt, str):
        raise ValueError("el payload público del quiz no tiene `prompt`")
    return prompt


QUIZ = QuizContent()


__all__ = [
    "COLUMNS",
    "CORRECT_LETTERS",
    "OPTION_KEYS",
    "QUIZ",
    "REQUIRED",
    "QuizContent",
    "RowError",
    "content_hash",
    "normalize_prompt",
]
