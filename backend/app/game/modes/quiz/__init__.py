"""El contenido de quiz y el catálogo de kinds disponibles hoy.

Cuando haya un segundo `ContentKind`, este catálogo se muda al registro de
contenido; por ahora vive acá para que la CLI y el admin resuelvan `--kind` y
`/admin/content/{kind}` contra la misma lista.
"""

from app.game.modes.quiz.content import QUIZ, QuizContent
from app.game.modes.quiz.models import (
    QUIZ_PROMPT_MAX_LENGTH,
    QUIZ_SCHEMA_VERSION,
    QuizCandidatesConfig,
    QuizPayload,
    QuizSolution,
)
from app.game.modes.quiz.rules import QuizRules

CONTENT_KINDS: dict[str, QuizContent] = {QUIZ.code: QUIZ}

# Las reglas las comparten los dos modos de quiz: `trivia_arcade` y
# `trivia_versus` solo cambian el formato y la progresión.
QUIZ_RULES = QuizRules()


def get_content_kind(code: str) -> QuizContent:
    try:
        return CONTENT_KINDS[code]
    except KeyError:
        raise ValueError(f"kind de contenido desconocido: {code!r}") from None


__all__ = [
    "CONTENT_KINDS",
    "QUIZ",
    "QUIZ_PROMPT_MAX_LENGTH",
    "QUIZ_RULES",
    "QUIZ_SCHEMA_VERSION",
    "QuizCandidatesConfig",
    "QuizContent",
    "QuizPayload",
    "QuizRules",
    "QuizSolution",
    "get_content_kind",
]
