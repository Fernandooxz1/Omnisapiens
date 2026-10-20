"""Los contratos de modo y el registro del proceso."""

from app.game.modes.arcade import TRIVIA_ARCADE
from app.game.modes.base import (
    ConnectionPolicy,
    ContentDraft,
    ContentKind,
    GameMode,
    ItemRef,
    LoadedItem,
    Players,
    Progression,
    PublicItem,
    RankingPolicy,
    RoundRules,
    Schedule,
    ScoringPolicy,
    SessionState,
    Solution,
    Step,
)
from app.game.modes.registry import (
    ModeRegistry,
    all,
    get,
    register,
    registry,
)
from app.game.modes.versus import TRIVIA_VERSUS

# El catálogo del proceso. `GET /modes`, la creación de sesiones y el ranking
# leen de acá; no hay una segunda lista de modos.
register(TRIVIA_ARCADE)
register(TRIVIA_VERSUS)

__all__ = [
    "TRIVIA_ARCADE",
    "TRIVIA_VERSUS",
    "ConnectionPolicy",
    "ContentDraft",
    "ContentKind",
    "GameMode",
    "ItemRef",
    "LoadedItem",
    "ModeRegistry",
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
    "all",
    "get",
    "register",
    "registry",
]
