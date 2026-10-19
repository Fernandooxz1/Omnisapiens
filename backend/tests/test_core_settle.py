"""La ventana compartida: bordes, omisión, intento repetido y tipo inesperado."""

from collections.abc import Callable

import pytest

from app.game.core import (
    ChoiceSubmission,
    LetterSubmission,
    OrderSubmission,
    RejectReason,
    ServedItem,
    Submission,
    TextSubmission,
    Verdict,
    settle,
)


def served() -> ServedItem:
    return ServedItem(
        item_key="q-2",
        difficulty=3,
        seconds=20,
        served_at_ms=1_000,
        deadline=21_000,
    )


def grade_choice(
    expected: int, detail: str | None = None
) -> Callable[[Submission], tuple[bool, str | None]]:
    def grade(submission: Submission) -> tuple[bool, str | None]:
        assert isinstance(submission, ChoiceSubmission)
        return submission.index == expected, detail

    return grade


def test_served_item_derives_its_window() -> None:
    item = served()

    assert item.window_ms == 20_000


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"item_key": ""}, "item_key"),
        ({"difficulty": 0}, "dificultad"),
        ({"difficulty": 6}, "dificultad"),
        ({"seconds": 0}, "seconds"),
        ({"served_at_ms": -1}, "served_at_ms"),
        ({"deadline": 1_000}, "deadline"),
    ],
)
def test_served_item_rejects_an_impossible_item(
    overrides: dict[str, int | str], message: str
) -> None:
    base: dict[str, int | str] = {
        "item_key": "q-1",
        "difficulty": 1,
        "seconds": 10,
        "served_at_ms": 1_000,
        "deadline": 11_000,
    }

    with pytest.raises(ValueError, match=message):
        ServedItem(**(base | overrides))


@pytest.mark.parametrize(
    ("submission", "kind"),
    [
        (ChoiceSubmission(0), "choice"),
        (TextSubmission("Amazonas"), "text"),
        (LetterSubmission("a", "Amazonas"), "letter"),
        (OrderSubmission((0, 1)), "order"),
    ],
)
def test_each_submission_carries_its_discriminator(
    submission: Submission, kind: str
) -> None:
    assert submission.kind == kind


def test_choice_submission_rejects_a_negative_index() -> None:
    with pytest.raises(ValueError, match="index"):
        ChoiceSubmission(-1)


def test_the_lower_bound_is_inside_the_window() -> None:
    verdict = settle(
        served(),
        ChoiceSubmission(1),
        now_ms=1_000,
        grade=grade_choice(1),
    )

    assert verdict.correct is True
    assert verdict.rejected is None
    assert verdict.elapsed_ms == 0


def test_the_upper_bound_is_inside_the_window() -> None:
    verdict = settle(
        served(),
        ChoiceSubmission(1),
        now_ms=21_000,
        grade=grade_choice(1),
    )

    assert verdict.correct is True
    assert verdict.rejected is None
    assert verdict.elapsed_ms == 20_000


@pytest.mark.parametrize("now_ms", [999, 21_001])
def test_a_submission_outside_the_window_does_not_exist(now_ms: int) -> None:
    def no_debe_juzgar(_submission: Submission) -> tuple[bool, None]:
        raise AssertionError("el grade no puede ver una submission vencida")

    verdict = settle(served(), ChoiceSubmission(0), now_ms=now_ms, grade=no_debe_juzgar)

    assert verdict.correct is False
    assert verdict.rejected is RejectReason.OUTSIDE_WINDOW
    assert verdict.elapsed_ms == 20_000
    assert verdict.detail is None


def test_no_submission_consumes_the_whole_window() -> None:
    def no_debe_juzgar(_submission: Submission) -> tuple[bool, None]:
        raise AssertionError("sin submission no hay nada que juzgar")

    verdict = settle(served(), None, now_ms=5_000, grade=no_debe_juzgar)

    assert verdict.correct is False
    assert verdict.rejected is None
    assert verdict.elapsed_ms == 20_000
    assert verdict.detail is None


def test_a_duplicate_attempt_produces_the_same_verdict() -> None:
    """`settle` es puro: repetir el intento no muta el ítem ni el resultado."""
    vistos: list[Submission] = []

    def grade(submission: Submission) -> tuple[bool, str | None]:
        vistos.append(submission)
        assert isinstance(submission, ChoiceSubmission)
        return submission.index == 1, "el Amazonas"

    item = served()
    submission = ChoiceSubmission(1)
    primero = settle(item, submission, now_ms=2_000, grade=grade)
    segundo = settle(item, submission, now_ms=2_000, grade=grade)

    assert primero == segundo
    assert vistos == [submission, submission]
    assert item == served()


def test_a_submission_of_another_kind_is_not_coerced() -> None:
    def solo_choice(submission: Submission) -> tuple[bool, str | None]:
        if not isinstance(submission, ChoiceSubmission):
            return False, "se esperaba una opción"
        return submission.index == 1, None

    verdict = settle(
        served(), TextSubmission("Amazonas"), now_ms=2_000, grade=solo_choice
    )

    assert verdict.correct is False
    assert verdict.rejected is None
    assert verdict.elapsed_ms == 1_000
    assert verdict.detail == "se esperaba una opción"


def test_the_mode_detail_travels_in_the_verdict() -> None:
    verdict = settle(
        served(),
        ChoiceSubmission(1),
        now_ms=2_000,
        grade=grade_choice(1, "el Amazonas es el más caudaloso"),
    )

    assert verdict.detail == "el Amazonas es el más caudaloso"


def test_a_verdict_without_a_rejection_defaults_to_none() -> None:
    verdict = Verdict[str](correct=True, elapsed_ms=10)

    assert verdict.rejected is None
    assert verdict.detail is None
