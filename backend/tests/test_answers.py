import pytest

from app.game.answers import Answer, RejectReason, ServedQuestion, settle


def served() -> ServedQuestion:
    return ServedQuestion(
        round_index=2, question_id="q-2", difficulty=3, seconds=20, served_at_ms=1_000
    )


def answer(choice: int, answered_at_ms: int) -> Answer:
    return Answer(round_index=2, choice=choice, answered_at_ms=answered_at_ms)


def test_served_question_derives_its_window() -> None:
    question = served()

    assert question.limit_ms == 20_000
    assert question.ends_at_ms == 21_000


@pytest.mark.parametrize("seconds", [0, -5])
def test_served_question_rejects_non_positive_seconds(seconds: int) -> None:
    with pytest.raises(ValueError, match="seconds debe ser positivo"):
        ServedQuestion(
            round_index=0,
            question_id="q",
            difficulty=1,
            seconds=seconds,
            served_at_ms=0,
        )


@pytest.mark.parametrize("difficulty", [0, 6])
def test_served_question_rejects_difficulty_out_of_range(difficulty: int) -> None:
    with pytest.raises(ValueError, match="dificultad fuera de rango"):
        ServedQuestion(
            round_index=0,
            question_id="q",
            difficulty=difficulty,
            seconds=10,
            served_at_ms=0,
        )


@pytest.mark.parametrize("choice", [-1, 4, 99])
def test_answer_rejects_choice_out_of_range(choice: int) -> None:
    with pytest.raises(ValueError, match="choice fuera de rango"):
        Answer(round_index=0, choice=choice, answered_at_ms=0)


def test_missing_answer_consumes_the_whole_window() -> None:
    settled = settle(served(), None, correct_index=0)

    assert settled.answer is None
    assert settled.rejected is None
    assert settled.correct is False
    assert settled.elapsed_ms == 20_000


def test_on_time_answer_is_measured_from_the_served_moment() -> None:
    settled = settle(served(), answer(1, 4_500), correct_index=1)

    assert settled.rejected is None
    assert settled.correct is True
    assert settled.elapsed_ms == 3_500


def test_wrong_choice_is_judged_incorrect() -> None:
    settled = settle(served(), answer(3, 2_000), correct_index=0)

    assert settled.correct is False
    assert settled.elapsed_ms == 1_000


@pytest.mark.parametrize("answered_at_ms", [999, 21_001])
def test_answer_outside_the_window_does_not_exist(answered_at_ms: int) -> None:
    settled = settle(served(), answer(0, answered_at_ms), correct_index=0)

    assert settled.answer is None
    assert settled.rejected is RejectReason.OUTSIDE_WINDOW
    assert settled.correct is False
    assert settled.elapsed_ms == 20_000
