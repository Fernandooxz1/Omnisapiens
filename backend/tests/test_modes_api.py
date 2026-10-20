"""El catálogo HTTP de modos y sus esquemas de configuración."""

import httpx
import pytest
from pydantic import ValidationError

from app.game.modes import get
from app.game.modes.arcade import TRIVIA_ARCADE, ArcadeConfig
from app.game.modes.versus import TRIVIA_VERSUS, VersusModeConfig


async def test_the_catalog_lists_the_registered_modes(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/modes")

    assert response.status_code == 200
    catalog = {mode["code"]: mode for mode in response.json()}
    assert set(catalog) == {"trivia_arcade", "trivia_versus"}


async def test_the_arcade_is_solo_and_ranked(client: httpx.AsyncClient) -> None:
    response = await client.get("/modes")
    arcade = next(m for m in response.json() if m["code"] == "trivia_arcade")

    assert arcade["name"] == "Arcade"
    assert arcade["content_kind"] == "quiz"
    assert arcade["play_format"] == "arcade"
    assert arcade["players"] == "solo"
    assert arcade["input"] == "choice"
    assert arcade["media"] == ["none", "image", "audio"]
    assert arcade["ranking"] is True
    assert arcade["config_schema"]["additionalProperties"] is False


async def test_the_versus_has_no_ranking(client: httpx.AsyncClient) -> None:
    response = await client.get("/modes")
    versus = next(m for m in response.json() if m["code"] == "trivia_versus")

    assert versus["name"] == "1v1"
    assert versus["play_format"] == "versus"
    assert versus["players"] == "versus"
    assert versus["ranking"] is False
    assert set(versus["config_schema"]["properties"]) == {"rounds", "seconds"}


def test_the_registry_is_the_only_catalog() -> None:
    assert get("trivia_arcade") is TRIVIA_ARCADE
    assert get("trivia_versus") is TRIVIA_VERSUS


def test_the_arcade_config_accepts_empty_and_rejects_extra_values() -> None:
    assert ArcadeConfig.model_validate({}) == ArcadeConfig()

    with pytest.raises(ValidationError):
        ArcadeConfig.model_validate({"lives": 9})


@pytest.mark.parametrize(
    "payload",
    [
        {"rounds": 4},
        {"rounds": 0},
        {"seconds": 15},
        {"seconds": 0},
        {"rounds": 3, "extra": 1},
    ],
)
def test_the_versus_config_rejects_invalid_values(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        VersusModeConfig.model_validate(payload)


def test_the_versus_config_keeps_the_defaults() -> None:
    config = VersusModeConfig.model_validate({})

    assert config.rounds == 5
    assert config.seconds == 20
