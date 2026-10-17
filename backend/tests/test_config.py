"""La config: el secreto corto sólo se acepta en local (H-21)."""

import pytest
from pydantic import ValidationError

from app.config import Settings


def _campos(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "database_url": "postgresql+asyncpg://x:y@localhost:5432/z",
        "redis_url": "redis://localhost:6379/0",
        "jwt_secret": "corto",
        "cors_origins": "http://localhost:5173",
    }
    return base | overrides


def test_local_accepts_a_short_secret() -> None:
    assert Settings(env="local", **_campos()).jwt_secret == "corto"


def test_production_rejects_a_short_secret() -> None:
    with pytest.raises(ValidationError, match="al menos 32 bytes"):
        Settings(env="prod", **_campos())


def test_production_accepts_a_long_secret() -> None:
    ajustes = Settings(env="prod", **_campos(jwt_secret="x" * 32))

    assert ajustes.env == "prod"
