"""Los contratos que declara un modo del juego.

Un `GameMode` combina un contenido (`ContentKind`), las reglas de una ronda
(`RoundRules`), la progresión entre rondas (`Progression`) y el puntaje
(`ScoringPolicy`). El borde solo conoce estos protocolos y el registro: no hay
una clase de mensaje ni una rama por modo.

Los tipos de contenido son deliberadamente chicos: el payload público y la
solución viajan en estructuras separadas, y `LoadedItem` es lo único que las
junta. El borde nunca recibe un `LoadedItem` entero, solo su parte pública.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from random import Random
from typing import Protocol

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.game.constants import DIFFICULTY_MAX, DIFFICULTY_MIN
from app.game.core import ServedItem, Submission, Verdict


class Players(StrEnum):
    SOLO = "solo"
    VERSUS = "versus"


class ConnectionPolicy(StrEnum):
    """Qué pasa con la sesión cuando la conexión se cae."""

    EPHEMERAL = "ephemeral"
    RESILIENT = "resilient"


class Schedule(StrEnum):
    """Cómo avanza la sesión: ronda tras ronda o un tablero con posiciones."""

    LINEAR = "linear"
    BOARD = "board"


@dataclass(frozen=True)
class ItemRef:
    """Lo mínimo para elegir un ítem antes de cargarlo.

    Los ids son texto, como en el selector de preguntas: la conversión a `uuid`
    pasa una sola vez, en el borde de la base.
    """

    content_id: str
    difficulty: int
    categories: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.content_id:
            raise ValueError("content_id vacío")
        if not DIFFICULTY_MIN <= self.difficulty <= DIFFICULTY_MAX:
            raise ValueError(f"dificultad fuera de rango: {self.difficulty}")


@dataclass(frozen=True)
class PublicItem:
    """Lo que puede viajar al cliente. Nunca contiene la solución."""

    payload: Mapping[str, object]
    media_type: str = "none"
    media_url: str | None = None


@dataclass(frozen=True)
class Solution:
    """Lo que solo ve `RoundRules.grade`."""

    payload: Mapping[str, object]


@dataclass(frozen=True)
class LoadedItem:
    """El ítem cargado con sus dos mitades: pública y solución."""

    content_id: str
    public: PublicItem
    solution: Solution

    def __post_init__(self) -> None:
        if not self.content_id:
            raise ValueError("content_id vacío")


@dataclass(frozen=True)
class ContentDraft:
    """Una fila ya parseada, antes de asignarle id y `content_hash`."""

    schema_version: int
    public: PublicItem
    solution: Solution
    difficulty: int
    categories: tuple[str, ...] = ()
    language: str = "es"

    def __post_init__(self) -> None:
        if self.schema_version < 1:
            raise ValueError(f"schema_version inválida: {self.schema_version}")
        if not DIFFICULTY_MIN <= self.difficulty <= DIFFICULTY_MAX:
            raise ValueError(f"dificultad fuera de rango: {self.difficulty}")
        if not self.language:
            raise ValueError("language vacío")


class ContentKind(Protocol):
    """Cómo se guarda, valida, importa y sirve un tipo de contenido."""

    code: str
    schema_version: int

    def parse_row(self, raw: Mapping[str, str]) -> ContentDraft: ...

    def fingerprint(self, draft: ContentDraft) -> str: ...

    async def candidates(
        self, session: AsyncSession, *, config: BaseModel
    ) -> list[ItemRef]: ...

    async def load(self, session: AsyncSession, ref: ItemRef) -> LoadedItem: ...


class RoundRules(Protocol):
    """Qué significa servir y juzgar una ronda de este modo."""

    def serve(
        self,
        item: LoadedItem,
        *,
        difficulty: int,
        seconds: int,
        now_ms: int,
        rng: Random,
    ) -> ServedItem: ...

    def grade(
        self, served: ServedItem, submission: Submission, *, now_ms: int
    ) -> Verdict[object]: ...


class SessionState(Protocol):
    """Los contadores comunes que puede mirar una progresión o un puntaje."""

    round_index: int
    score: int
    streak: int
    correct_count: int
    longest_streak: int
    max_difficulty: int

    @property
    def finished(self) -> bool: ...


@dataclass(frozen=True)
class Step:
    """La próxima ronda que decide la progresión.

    `finished` es la respuesta a "¿la sesión sigue?": en un tablero puede ser
    verdadero sin que se hayan agotado los ítems (se cerró el rosco, por ejemplo).
    """

    difficulty: int
    seconds: int
    finished: bool = False

    def __post_init__(self) -> None:
        if not DIFFICULTY_MIN <= self.difficulty <= DIFFICULTY_MAX:
            raise ValueError(f"dificultad fuera de rango: {self.difficulty}")
        if self.seconds <= 0:
            raise ValueError(f"seconds debe ser positivo: {self.seconds}")


class Progression(Protocol):
    """Cómo se pasa de una ronda a la siguiente."""

    def next(self, state: SessionState, format: str) -> Step: ...


class ScoringPolicy(Protocol):
    """Cuánto vale una ronda. No decide si fue correcta: eso es `Verdict`."""

    def points(
        self,
        verdict: Verdict[object],
        elapsed_ms: int,
        seconds: int,
        state: SessionState,
    ) -> int: ...


@dataclass(frozen=True)
class RankingPolicy:
    """Marca que el modo publica ranking.

    En la v1 la única política es el puntaje de la sesión; el tipo existe para
    que un modo lo declare (`ranking is not None`) sin una lista aparte.
    """


@dataclass(frozen=True)
class GameMode:
    """La combinación registrada que el jugador elige."""

    code: str
    name: str
    content_kind: str
    play_format: str
    ruleset_version: int
    content: ContentKind
    rules: RoundRules
    progression: Progression
    scoring: ScoringPolicy
    config_schema: type[BaseModel]
    public_schema: type[BaseModel]
    input: str
    media: tuple[str, ...]
    ranking: RankingPolicy | None
    players: Players
    connection: ConnectionPolicy
    schedule: Schedule

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("code vacío")
        if not self.name:
            raise ValueError("name vacío")
        if not self.content_kind:
            raise ValueError("content_kind vacío")
        if not self.play_format:
            raise ValueError("play_format vacío")
        if self.ruleset_version < 1:
            raise ValueError(f"ruleset_version inválida: {self.ruleset_version}")
        if self.content.code != self.content_kind:
            raise ValueError(
                f"content_kind {self.content_kind!r} no coincide con "
                f"ContentKind.code {self.content.code!r}"
            )
        if not self.input:
            raise ValueError("input vacío")
        if not self.media or any(not item for item in self.media):
            raise ValueError("media vacío")


__all__ = [
    "ConnectionPolicy",
    "ContentDraft",
    "ContentKind",
    "GameMode",
    "ItemRef",
    "LoadedItem",
    "Players",
    "Progression",
    "PublicItem",
    "RankingPolicy",
    "RoundRules",
    "Schedule",
    "ScoringPolicy",
    "SessionState",
    "Solution",
    "Step",
]
