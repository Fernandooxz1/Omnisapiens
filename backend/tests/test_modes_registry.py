"""El registro y las validaciones de los contratos de modo."""

from collections.abc import Mapping
from random import Random

import pytest
from pydantic import BaseModel

from app.game.core import ServedItem, Submission, Verdict
from app.game.modes import (
    ConnectionPolicy,
    ContentDraft,
    GameMode,
    ItemRef,
    LoadedItem,
    ModeRegistry,
    Players,
    PublicItem,
    Schedule,
    Solution,
    Step,
)


class _Content:
    code = "quiz"
    schema_version = 1

    def parse_row(self, raw: Mapping[str, str]) -> ContentDraft:
        raise NotImplementedError

    def fingerprint(self, draft: ContentDraft) -> str:
        raise NotImplementedError

    async def candidates(self, session: object, *, config: BaseModel) -> list[ItemRef]:
        raise NotImplementedError

    async def load(self, session: object, ref: ItemRef) -> LoadedItem:
        raise NotImplementedError


class _Rules:
    def serve(
        self,
        item: LoadedItem,
        *,
        difficulty: int,
        seconds: int,
        now_ms: int,
        rng: Random,
    ) -> ServedItem:
        raise NotImplementedError

    def grade(
        self, served: ServedItem, submission: Submission, *, now_ms: int
    ) -> Verdict[object]:
        raise NotImplementedError


class _Progression:
    def next(self, state: object, format: str) -> Step:
        raise NotImplementedError


class _Scoring:
    def points(
        self,
        verdict: Verdict[object],
        elapsed_ms: int,
        seconds: int,
        state: object,
    ) -> int:
        raise NotImplementedError


class _Config(BaseModel):
    pass


class _Public(BaseModel):
    pass


def make_mode(**overrides: object) -> GameMode:
    base: dict[str, object] = {
        "code": "trivia_test",
        "content_kind": "quiz",
        "play_format": "arcade",
        "ruleset_version": 1,
        "content": _Content(),
        "rules": _Rules(),
        "progression": _Progression(),
        "scoring": _Scoring(),
        "config_schema": _Config,
        "public_schema": _Public,
        "ranking": None,
        "players": Players.SOLO,
        "connection": ConnectionPolicy.EPHEMERAL,
        "schedule": Schedule.LINEAR,
    }
    return GameMode(**(base | overrides))  # type: ignore[arg-type]


def test_a_mode_can_be_registered_and_read_back() -> None:
    registry = ModeRegistry()
    mode = make_mode()

    assert registry.register(mode) is mode
    assert registry.get("trivia_test") is mode
    assert registry.all() == (mode,)


def test_a_duplicate_code_is_rejected() -> None:
    registry = ModeRegistry()
    registry.register(make_mode())

    with pytest.raises(ValueError, match="duplicado"):
        registry.register(make_mode())


def test_an_unknown_mode_raises_key_error() -> None:
    with pytest.raises(KeyError, match="desconocido"):
        ModeRegistry().get("no_existe")


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"code": ""}, "code"),
        ({"content_kind": ""}, "content_kind"),
        ({"play_format": ""}, "play_format"),
        ({"ruleset_version": 0}, "ruleset_version"),
        ({"content_kind": "rosco"}, "no coincide"),
    ],
)
def test_an_invalid_mode_is_rejected(
    overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        make_mode(**overrides)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"difficulty": 0, "seconds": 10}, "dificultad"),
        ({"difficulty": 6, "seconds": 10}, "dificultad"),
        ({"difficulty": 1, "seconds": 0}, "seconds"),
    ],
)
def test_a_step_must_have_a_valid_round(
    overrides: dict[str, int], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        Step(**overrides)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"content_id": "", "difficulty": 1}, "content_id"),
        ({"content_id": "q", "difficulty": 0}, "dificultad"),
        ({"content_id": "q", "difficulty": 6}, "dificultad"),
    ],
)
def test_an_item_ref_must_point_to_a_valid_item(
    overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        ItemRef(**overrides)  # type: ignore[arg-type]


def test_a_draft_validates_its_version_and_difficulty() -> None:
    public = PublicItem(payload={"prompt": "¿?"})
    solution = Solution(payload={"correct_index": 1})

    draft = ContentDraft(
        schema_version=1,
        public=public,
        solution=solution,
        difficulty=3,
        categories=("geography",),
    )
    assert draft.public is public
    assert draft.language == "es"

    with pytest.raises(ValueError, match="schema_version"):
        ContentDraft(
            schema_version=0,
            public=public,
            solution=solution,
            difficulty=1,
        )
    with pytest.raises(ValueError, match="dificultad"):
        ContentDraft(
            schema_version=1,
            public=public,
            solution=solution,
            difficulty=9,
        )


def test_a_loaded_item_keeps_the_solution_apart() -> None:
    loaded = LoadedItem(
        content_id="q-1",
        public=PublicItem(payload={"prompt": "¿?"}),
        solution=Solution(payload={"correct_index": 1}),
    )

    assert "correct_index" not in loaded.public.payload
    assert loaded.solution.payload["correct_index"] == 1

    with pytest.raises(ValueError, match="content_id"):
        LoadedItem(
            content_id="",
            public=loaded.public,
            solution=loaded.solution,
        )
