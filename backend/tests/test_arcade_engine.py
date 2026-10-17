import pytest

from app.game.answers import Answer, RejectReason, ServedQuestion
from app.game.arcade_engine import (
    ArcadeRun,
    RunStatus,
    difficulty_for,
    next_question,
    resolve,
    seconds_for,
)
from app.game.errors import InvalidTransition


def start_run() -> ArcadeRun:
    return ArcadeRun()


def served_for(run: ArcadeRun, *, now_ms: int = 1_000) -> ServedQuestion:
    return next_question(run, question_id=f"q-{run.round_index}", now_ms=now_ms)


def answer(served: ServedQuestion, *, choice: int, at_ms: int) -> Answer:
    return Answer(round_index=served.round_index, choice=choice, answered_at_ms=at_ms)


@pytest.mark.parametrize(
    ("correct_count", "expected"),
    [
        (0, 1),
        (3, 1),
        (4, 2),
        (9, 2),
        (10, 3),
        (17, 3),
        (18, 4),
        (27, 4),
        (28, 5),
        (100, 5),
    ],
)
def test_difficulty_progression(correct_count: int, expected: int) -> None:
    assert difficulty_for(correct_count) == expected


@pytest.mark.parametrize(
    ("correct_count", "expected"),
    [(0, 20), (2, 20), (3, 19), (6, 18), (42, 6), (45, 5), (90, 5)],
)
def test_seconds_progression(correct_count: int, expected: int) -> None:
    assert seconds_for(correct_count) == expected


def test_negative_correct_count_raises() -> None:
    with pytest.raises(ValueError, match="correct_count negativo"):
        difficulty_for(-1)
    with pytest.raises(ValueError, match="correct_count negativo"):
        seconds_for(-1)


def test_first_question_starts_easy_and_long() -> None:
    served = served_for(start_run())

    assert served.difficulty == 1
    assert served.seconds == 20
    assert served.served_at_ms == 1_000
    assert served.ends_at_ms == 21_000


def test_question_difficulty_follows_progress() -> None:
    run = ArcadeRun(correct_count=4, streak=4, longest_streak=4, score=600)
    assert served_for(run).difficulty == 2


def test_correct_answer_scores_and_keeps_lives() -> None:
    run = start_run()
    served = served_for(run)

    resolved = resolve(
        run, served, correct_index=2, answer=answer(served, choice=2, at_ms=2_000)
    )

    assert resolved.record.correct is True
    assert resolved.record.points == 148
    assert resolved.record.elapsed_ms == 1_000
    assert resolved.record.choice == 2
    assert resolved.record.rejected is None
    assert resolved.run.score == 148
    assert resolved.run.lives == 3
    assert resolved.run.streak == 1
    assert resolved.run.correct_count == 1
    assert resolved.run.longest_streak == 1
    assert resolved.run.round_index == 1


def test_wrong_answer_loses_a_life_and_resets_streak() -> None:
    run = ArcadeRun(score=600, streak=4, longest_streak=4, correct_count=4)
    served = served_for(run, now_ms=10_000)

    resolved = resolve(
        run, served, correct_index=0, answer=answer(served, choice=3, at_ms=11_000)
    )

    assert resolved.record.points == 0
    assert resolved.run.score == 600
    assert resolved.run.lives == 2
    assert resolved.run.streak == 0
    assert resolved.run.longest_streak == 4
    assert resolved.run.status is RunStatus.PLAYING


def test_late_answer_counts_as_missing() -> None:
    run = start_run()
    served = served_for(run, now_ms=1_000)

    resolved = resolve(
        run, served, correct_index=0, answer=answer(served, choice=0, at_ms=21_001)
    )

    assert resolved.record.rejected is RejectReason.OUTSIDE_WINDOW
    assert resolved.record.correct is False
    assert resolved.record.choice is None
    assert resolved.record.elapsed_ms == 20_000
    assert resolved.record.points == 0
    assert resolved.run.lives == 2


def test_missing_answer_counts_as_wrong() -> None:
    run = start_run()
    served = served_for(run)

    resolved = resolve(run, served, correct_index=0, answer=None)

    assert resolved.record.choice is None
    assert resolved.record.correct is False
    assert resolved.run.lives == 2
    assert resolved.run.score == 0


def test_third_wrong_answer_finishes_the_run() -> None:
    run = start_run()
    for _ in range(3):
        served = served_for(run)
        run = resolve(run, served, correct_index=0, answer=None).run

    assert run.status is RunStatus.FINISHED
    assert run.finished is True
    assert run.lives == 0


def test_streak_bonus_grows_with_consecutive_hits() -> None:
    run = start_run()
    points = []

    for _ in range(3):
        served = served_for(run)
        resolved = resolve(
            run,
            served,
            correct_index=0,
            answer=answer(served, choice=0, at_ms=served.served_at_ms),
        )
        points.append(resolved.record.points)
        run = resolved.run

    assert run.streak == 3
    assert points[0] < points[1] < points[2]


def test_record_keeps_what_was_served() -> None:
    run = start_run()
    served = served_for(run)

    record = resolve(run, served, correct_index=0, answer=None).record

    assert record.question_id == "q-0"
    assert record.difficulty == served.difficulty
    assert record.seconds == served.seconds
    assert record.round_index == served.round_index


def test_max_difficulty_tracks_played_questions() -> None:
    run = start_run()
    for _ in range(5):
        served = served_for(run)
        run = resolve(
            run,
            served,
            correct_index=0,
            answer=answer(served, choice=0, at_ms=served.served_at_ms),
        ).run

    assert run.max_difficulty == 2


def test_no_question_after_finishing() -> None:
    run = ArcadeRun(lives=0, status=RunStatus.FINISHED)

    with pytest.raises(InvalidTransition):
        next_question(run, question_id="q", now_ms=0)


def test_cannot_resolve_after_finishing() -> None:
    served = ServedQuestion(
        round_index=3, question_id="q", difficulty=1, seconds=20, served_at_ms=0
    )
    run = ArcadeRun(round_index=3, lives=0, status=RunStatus.FINISHED)

    with pytest.raises(InvalidTransition):
        resolve(run, served, correct_index=0, answer=None)


def test_cannot_resolve_a_different_round() -> None:
    served = ServedQuestion(
        round_index=1, question_id="q", difficulty=1, seconds=20, served_at_ms=0
    )

    with pytest.raises(InvalidTransition):
        resolve(ArcadeRun(), served, correct_index=0, answer=None)


def test_correct_index_must_be_a_valid_choice() -> None:
    served = ServedQuestion(
        round_index=0, question_id="q", difficulty=1, seconds=20, served_at_ms=0
    )

    with pytest.raises(ValueError, match="correct_index fuera de rango"):
        resolve(ArcadeRun(), served, correct_index=7, answer=None)


@pytest.mark.parametrize(
    "overrides",
    [
        {"lives": 4},
        {"lives": -1},
        {"score": -1},
        {"streak": 2, "correct_count": 1},
        {"longest_streak": 5, "correct_count": 1, "streak": 0},
        {"status": RunStatus.FINISHED},
        {"lives": 0},
        {"max_difficulty": 6},
    ],
)
def test_impossible_states_are_rejected(overrides: dict[str, object]) -> None:
    with pytest.raises(
        ValueError, match=r"fuera de rango|negativo|streak|se contradicen"
    ):
        ArcadeRun(**overrides)  # type: ignore[arg-type]
