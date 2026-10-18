"""La config: el secreto corto sólo se acepta en local (H-21)."""

import pytest
from pydantic import ValidationError

from app.config import Settings


def _campos(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "database_url": "postgresql+asyncpg://x:y@localhost:5432/z",
        "redis_url": "redis://localhost:6379/0",
        "jwt_secret": "corto",
        "admin_token": "token-de-admin",
        "cors_origins": "http://localhost:5173",
    }
    return base | overrides


def test_local_accepts_a_short_secret() -> None:
    assert Settings(env="local", **_campos()).jwt_secret == "corto"


def test_production_rejects_a_short_secret() -> None:
    with pytest.raises(ValidationError, match="al menos 32 bytes"):
        Settings(env="prod", **_campos())


def test_production_rejects_a_short_admin_token() -> None:
    with pytest.raises(ValidationError, match=r"ADMIN_TOKEN.*32 bytes"):
        Settings(env="prod", **_campos(jwt_secret="x" * 32))


def test_an_empty_admin_token_is_rejected_even_in_local() -> None:
    with pytest.raises(ValidationError, match="ADMIN_TOKEN no puede estar vacío"):
        Settings(env="local", **_campos(admin_token=""))


def test_production_accepts_a_long_secret() -> None:
    ajustes = Settings(env="prod", **_campos(jwt_secret="x" * 32, admin_token="y" * 32))

    assert ajustes.env == "prod"
