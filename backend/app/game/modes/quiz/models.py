"""Los payloads versionados del quiz.

`QuizPayload` es lo que puede viajar al cliente; `QuizSolution` es lo que solo
ve `grade`. Los dos llevan `v` y ese número tiene que coincidir con el
`schema_version` de `content_items` (lo exige el `CHECK` de la tabla): un
payload sin versión se rechaza en vez de pasar por un `NULL`.

El tipo público no tiene `correct_index` ni `explanation`, y no es un descuido:
no hay dónde guardarlos, así que no se pueden filtrar.
"""

from typing import Final, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.game.constants import DIFFICULTY_MAX, DIFFICULTY_MIN

QUIZ_SCHEMA_VERSION: Final = 1
QUIZ_OPTION_COUNT: Final = 4
QUIZ_PROMPT_MAX_LENGTH: Final = 300


class QuizMedia(BaseModel):
    """El medio del ítem, con la misma coherencia que las columnas de la tabla."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["none", "image", "audio"] = "none"
    url: str | None = None

    @model_validator(mode="after")
    def _media_is_consistent(self) -> Self:
        # `none` sin URL o un medio con URL; lo mezclado es un error de carga.
        if (self.type == "none") != (self.url is None):
            raise ValueError("el medio y su URL no son coherentes")
        return self


class QuizPayload(BaseModel):
    """Lo público: enunciado, opciones y medio. Sin la respuesta."""

    model_config = ConfigDict(extra="forbid")

    v: Literal[1] = QUIZ_SCHEMA_VERSION
    prompt: str = Field(min_length=1, max_length=QUIZ_PROMPT_MAX_LENGTH)
    options: list[str] = Field(
        min_length=QUIZ_OPTION_COUNT, max_length=QUIZ_OPTION_COUNT
    )
    media: QuizMedia = Field(default_factory=QuizMedia)

    @field_validator("prompt")
    @classmethod
    def _prompt_is_clean(cls, value: str) -> str:
        limpio = value.strip()
        if not limpio:
            raise ValueError("el enunciado está vacío")
        return limpio

    @field_validator("options")
    @classmethod
    def _options_are_clean(cls, value: list[str]) -> list[str]:
        limpias = [opcion.strip() for opcion in value]
        if any(not opcion for opcion in limpias):
            raise ValueError("hay una opción vacía")
        # casefold: "París" y "parís" son la misma opción para quien juega.
        if len({opcion.casefold() for opcion in limpias}) < len(limpias):
            raise ValueError("hay opciones repetidas")
        return limpias


class QuizSolution(BaseModel):
    """Lo que solo ve `grade`: el índice correcto y la explicación."""

    model_config = ConfigDict(extra="forbid")

    v: Literal[1] = QUIZ_SCHEMA_VERSION
    correct_index: int = Field(ge=0, lt=QUIZ_OPTION_COUNT)
    explanation: str | None = None


class QuizCandidatesConfig(BaseModel):
    """El tramo de dificultad que puede pedir una sesión de quiz."""

    model_config = ConfigDict(extra="forbid")

    low: int | None = Field(default=None, ge=DIFFICULTY_MIN, le=DIFFICULTY_MAX)
    high: int | None = Field(default=None, ge=DIFFICULTY_MIN, le=DIFFICULTY_MAX)

    @model_validator(mode="after")
    def _range_is_ordered(self) -> Self:
        if self.low is not None and self.high is not None and self.low > self.high:
            raise ValueError(f"rango de dificultad invertido: {self.low}-{self.high}")
        return self


__all__ = [
    "QUIZ_OPTION_COUNT",
    "QUIZ_PROMPT_MAX_LENGTH",
    "QUIZ_SCHEMA_VERSION",
    "QuizCandidatesConfig",
    "QuizMedia",
    "QuizPayload",
    "QuizSolution",
]
