import pytest

from app.game.constants import ONLINE_SECONDS_OPTIONS
from app.game.scoring import arcade_points, round_points, streak_bonus


@pytest.mark.parametrize(
    ("elapsed_ms", "expected"),
    [
        (0, 150),
        (1_000, 148),
        (10_000, 125),
        (19_000, 103),
        (20_000, 100),
    ],
)
def test_online_points_20_seconds(elapsed_ms: int, expected: int) -> None:
    assert (
        round_points(correct=True, elapsed_ms=elapsed_ms, total_seconds=20) == expected
    )


@pytest.mark.parametrize(
    ("elapsed_ms", "expected"),
    [(1_000, 145), (5_000, 125), (10_000, 100)],
)
def test_online_points_10_seconds(elapsed_ms: int, expected: int) -> None:
    assert (
        round_points(correct=True, elapsed_ms=elapsed_ms, total_seconds=10) == expected
    )


def test_wrong_answer_scores_nothing() -> None:
    assert round_points(correct=False, elapsed_ms=0, total_seconds=20) == 0


@pytest.mark.parametrize("seconds", ONLINE_SECONDS_OPTIONS)
def test_points_stay_in_range_and_decrease_with_time(seconds: int) -> None:
    limit_ms = seconds * 1000
    previous = 151

    for elapsed in range(0, limit_ms + 1, 50):
        points = round_points(correct=True, elapsed_ms=elapsed, total_seconds=seconds)
        assert 100 <= points <= 150
        assert points <= previous
        previous = points

    assert previous == 100


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"total_seconds": 0, "elapsed_ms": 0}, "total_seconds"),
        ({"total_seconds": 20, "elapsed_ms": -1}, "negativo"),
        ({"total_seconds": 20, "elapsed_ms": 20_001}, "ventana"),
    ],
)
def test_invalid_inputs_raise(kwargs: dict[str, int], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        round_points(correct=True, **kwargs)


@pytest.mark.parametrize(
    ("streak", "expected"),
    [(0, 0), (1, 10), (3, 30), (5, 50), (9, 50)],
)
def test_streak_bonus(streak: int, expected: int) -> None:
    assert streak_bonus(streak) == expected


def test_negative_streak_raises() -> None:
    with pytest.raises(ValueError, match="negativo"):
        streak_bonus(-1)


def test_arcade_points_add_streak_bonus() -> None:
    assert (
        arcade_points(correct=True, elapsed_ms=1_000, total_seconds=20, streak=0) == 148
    )
    assert (
        arcade_points(correct=True, elapsed_ms=1_000, total_seconds=20, streak=3) == 178
    )


def test_arcade_wrong_answer_scores_nothing_even_with_streak() -> None:
    assert arcade_points(correct=False, elapsed_ms=0, total_seconds=20, streak=5) == 0
