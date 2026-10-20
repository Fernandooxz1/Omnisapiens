"""Las reglas de ronda del quiz: ventana, solución y rechazos."""

from random import Random

import pytest

from app.game.core import ChoiceSubmission, RejectReason, ServedItem, TextSubmission
from app.game.errors import InvalidTransition
from app.game.modes.base import LoadedItem, PublicItem, Solution
from app.game.modes.quiz import QuizRules


def _loaded(*, correct_index: int = 2) -> LoadedItem:
    return LoadedItem(
        content_id="item-1",
        public=PublicItem(
            payload={
                "v": 1,
                "prompt": "¿Cuál es la capital?",
                "options": ["A", "B", "C", "D"],
                "media": {"type": "none", "url": None},
            }
        ),
        solution=Solution(payload={"v": 1, "correct_index": correct_index}),
    )


def _served(rules: QuizRules, *, seconds: int = 10):
    return rules.serve(
        _loaded(),
        difficulty=2,
        seconds=seconds,
        now_ms=1_000,
        rng=Random(0),
    )


def test_serve_opens_the_window_from_the_injected_clock() -> None:
    served = _served(QuizRules())

    assert served.item_key == "item-1"
    assert served.served_at_ms == 1_000
    assert served.deadline == 11_000
    assert served.window_ms == 10_000


def test_grade_compares_against_the_solution_kept_by_serve() -> None:
    rules = QuizRules()
    served = _served(rules)

    correct = rules.grade(served, ChoiceSubmission(2), now_ms=1_500)
    wrong = rules.grade(served, ChoiceSubmission(0), now_ms=1_500)

    assert correct.correct
    assert correct.elapsed_ms == 500
    assert not wrong.correct
    assert wrong.elapsed_ms == 500


def test_grade_rejects_a_submission_outside_the_window() -> None:
    rules = QuizRules()
    served = _served(rules)

    before = rules.grade(served, ChoiceSubmission(2), now_ms=999)
    after = rules.grade(served, ChoiceSubmission(2), now_ms=11_001)

    assert before.rejected is RejectReason.OUTSIDE_WINDOW
    assert after.rejected is RejectReason.OUTSIDE_WINDOW
    assert not before.correct
    assert not after.correct


def test_a_submission_of_the_wrong_type_does_not_count() -> None:
    rules = QuizRules()
    served = _served(rules)

    verdict = rules.grade(served, TextSubmission("B"), now_ms=1_500)

    assert not verdict.correct
    assert verdict.rejected is None


def test_an_omitted_submission_consumes_the_whole_window() -> None:
    rules = QuizRules()
    served = _served(rules)

    omitted = rules.grade(served, None, now_ms=1_500)  # type: ignore[arg-type]

    assert not omitted.correct
    assert omitted.rejected is None
    assert omitted.elapsed_ms == served.window_ms


def test_grading_an_item_that_was_not_served_is_a_bug() -> None:
    rules = QuizRules()
    _served(rules)
    other = ServedItem(
        item_key="otro",
        difficulty=1,
        seconds=5,
        served_at_ms=0,
        deadline=5_000,
    )

    with pytest.raises(InvalidTransition, match="no fue servido"):
        rules.grade(other, ChoiceSubmission(0), now_ms=1_000)
