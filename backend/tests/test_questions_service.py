from random import Random

import pytest

from app.services.questions import (
    Candidate,
    NoQuestionsAvailable,
    SelectionStrategy,
    select,
)


def candidate(
    question_id: str, *, category: str = "science", difficulty: int = 3
) -> Candidate:
    return Candidate(question_id=question_id, category=category, difficulty=difficulty)


def pool() -> list[Candidate]:
    return [
        candidate("target-1", difficulty=3),
        candidate("target-2", difficulty=3),
        candidate("nearby", difficulty=4),
        candidate("other-category", category="history", difficulty=3),
        candidate("far-away", category="art", difficulty=1),
    ]


def test_prefers_exact_category_and_difficulty() -> None:
    selection = select(pool(), category="science", difficulty=3, rng=Random(1))

    assert selection.strategy is SelectionStrategy.TARGET
    assert selection.question_id in {"target-1", "target-2"}


def test_widens_difficulty_before_changing_category() -> None:
    candidates = [candidate("nearby", difficulty=4), candidate("other", category="art")]

    selection = select(candidates, category="science", difficulty=3, rng=Random(1))

    assert selection.strategy is SelectionStrategy.NEARBY_DIFFICULTY
    assert selection.question_id == "nearby"


def test_changes_category_when_the_category_is_exhausted() -> None:
    candidates = [candidate("other", category="history", difficulty=3)]

    selection = select(candidates, category="science", difficulty=3, rng=Random(1))

    assert selection.strategy is SelectionStrategy.ANY_CATEGORY
    assert selection.question_id == "other"


def test_falls_back_to_any_difficulty_before_repeating() -> None:
    candidates = [candidate("far-away", category="art", difficulty=1)]

    selection = select(candidates, category="science", difficulty=5, rng=Random(1))

    assert selection.strategy is SelectionStrategy.FALLBACK
    assert selection.question_id == "far-away"


def test_repeats_only_when_everything_was_used() -> None:
    candidates = [candidate("only")]

    selection = select(
        candidates, category="science", difficulty=3, rng=Random(1), excluded={"only"}
    )

    assert selection.strategy is SelectionStrategy.REPEAT
    assert selection.question_id == "only"


def test_excluded_questions_are_never_picked() -> None:
    candidates = pool()
    excluded = {"target-1", "target-2"}

    for _ in range(50):
        selection = select(
            candidates,
            category="science",
            difficulty=3,
            rng=Random(),
            excluded=excluded,
        )
        assert selection.question_id not in excluded


def test_empty_pool_raises() -> None:
    with pytest.raises(NoQuestionsAvailable):
        select([], category="science", difficulty=3, rng=Random(1))


def test_same_seed_gives_the_same_result() -> None:
    first = select(pool(), category="science", difficulty=3, rng=Random(7))
    second = select(pool(), category="science", difficulty=3, rng=Random(7))

    assert first == second


def test_result_does_not_depend_on_pool_order() -> None:
    candidates = pool()

    first = select(candidates, category="science", difficulty=3, rng=Random(11))
    second = select(
        list(reversed(candidates)), category="science", difficulty=3, rng=Random(11)
    )

    assert first == second


def test_candidates_spread_the_choice() -> None:
    candidates = [candidate(f"q-{index}") for index in range(5)]
    rng = Random(3)

    picked = {
        select(candidates, category="science", difficulty=3, rng=rng).question_id
        for _ in range(50)
    }

    assert picked == {f"q-{index}" for index in range(5)}


@pytest.mark.parametrize(
    ("category", "difficulty"),
    [("nonsense", 3), ("science", 0), ("science", 6)],
)
def test_invalid_request_raises(category: str, difficulty: int) -> None:
    with pytest.raises(ValueError):
        select(pool(), category=category, difficulty=difficulty, rng=Random(1))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"question_id": ""},
        {"category": "nonsense"},
        {"difficulty": 0},
        {"difficulty": 9},
    ],
)
def test_candidate_validation(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        Candidate(
            **{"question_id": "q", "category": "science", "difficulty": 3, **kwargs}
        )  # type: ignore[arg-type]
