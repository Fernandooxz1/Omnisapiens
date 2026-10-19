"""El motor solo: curvas parametrizadas, vidas y fin de corrida.

El arcade ya prueba el comportamiento histórico a través de su fachada; acá se
fija lo nuevo: que las reglas salgan de `SoloRules` y que el estado no esconda
historial.
"""

from dataclasses import fields

import pytest

from app.game.answers import Answer, ServedQuestion
from app.game.arcade_engine import ARCADE_RULES
from app.game.constants import (
    ARCADE_DIFFICULTY_TIERS,
    ARCADE_LIVES,
    ARCADE_SECONDS_FLOOR,
    ARCADE_SECONDS_START,
    ARCADE_SECONDS_STEP_EVERY,
    ARCADE_STREAK_BONUS_MAX,
    ARCADE_STREAK_BONUS_STEP,
)
from app.game.errors import InvalidTransition
from app.game.solo_engine import RunStatus, SoloEngine, SoloRules, SoloRun


def custom_rules(**overrides: object) -> SoloRules:
    base: dict[str, object] = {
        "lives": 2,
        "difficulty_tiers": (0, 2),
        "seconds_start": 10,
        "seconds_floor": 5,
        "seconds_step_every": 2,
        "streak_bonus_step": 0,
        "streak_bonus_max": 0,
    }
    return SoloRules(**(base | overrides))  # type: ignore[arg-type]


def served(engine: SoloEngine, run: SoloRun, *, now_ms: int = 1_000) -> ServedQuestion:
    return engine.next_question(run, question_id=f"q-{run.round_index}", now_ms=now_ms)


def answer(served: ServedQuestion, *, choice: int, at_ms: int) -> Answer:
    return Answer(round_index=served.round_index, choice=choice, answered_at_ms=at_ms)


def test_arcade_rules_are_the_current_format_values() -> None:
    assert (
        SoloRules(
            lives=ARCADE_LIVES,
            difficulty_tiers=ARCADE_DIFFICULTY_TIERS,
            seconds_start=ARCADE_SECONDS_START,
            seconds_floor=ARCADE_SECONDS_FLOOR,
            seconds_step_every=ARCADE_SECONDS_STEP_EVERY,
            streak_bonus_step=ARCADE_STREAK_BONUS_STEP,
            streak_bonus_max=ARCADE_STREAK_BONUS_MAX,
        )
        == ARCADE_RULES
    )


def test_a_new_run_starts_with_the_configured_lives() -> None:
    engine = SoloEngine(custom_rules())

    run = engine.start()

    assert run.lives == 2
    assert run.rules is engine.rules
    assert run.status is RunStatus.PLAYING
    assert run.finished is False


@pytest.mark.parametrize(
    ("correct_count", "expected"),
    [(0, 1), (1, 1), (2, 2), (100, 2)],
)
def test_difficulty_follows_the_configured_curve(
    correct_count: int, expected: int
) -> None:
    assert custom_rules().difficulty_for(correct_count) == expected


@pytest.mark.parametrize(
    ("correct_count", "expected"), [(0, 10), (1, 10), (2, 9), (10, 5), (100, 5)]
)
def test_seconds_follow_the_configured_curve(correct_count: int, expected: int) -> None:
    assert custom_rules().seconds_for(correct_count) == expected


def test_negative_progress_raises() -> None:
    with pytest.raises(ValueError, match="correct_count negativo"):
        custom_rules().difficulty_for(-1)
    with pytest.raises(ValueError, match="correct_count negativo"):
        custom_rules().seconds_for(-1)


def test_negative_streak_has_no_bonus() -> None:
    with pytest.raises(ValueError, match="streak no puede ser negativo"):
        custom_rules().streak_bonus(-1)


def test_an_impossible_run_state_is_rejected() -> None:
    engine = SoloEngine(custom_rules())

    with pytest.raises(ValueError, match="round_index negativo"):
        SoloRun(rules=engine.rules, lives=2, round_index=-1)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"lives": 0}, "lives"),
        ({"difficulty_tiers": ()}, "vacío"),
        ({"difficulty_tiers": (1, 2)}, "empezar en 0"),
        ({"difficulty_tiers": (0, 0)}, "creciente"),
        ({"difficulty_tiers": (0, 1, 2, 3, 4, 5)}, "máxima"),
        ({"seconds_start": 0}, "seconds_start"),
        ({"seconds_floor": 0}, "seconds_floor"),
        ({"seconds_floor": 20}, "superar"),
        ({"seconds_step_every": 0}, "seconds_step_every"),
        ({"streak_bonus_step": -1}, "streak_bonus_step"),
        ({"streak_bonus_max": -1}, "streak_bonus_max"),
    ],
)
def test_impossible_rules_are_rejected(
    overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        custom_rules(**overrides)


def test_streak_bonus_can_be_disabled_by_the_format() -> None:
    engine = SoloEngine(custom_rules())
    run = engine.start()
    served_ = served(engine, run)

    resolved = engine.resolve(
        run,
        served_,
        correct_index=0,
        answer=answer(served_, choice=0, at_ms=served_.served_at_ms),
    )

    assert resolved.run.streak == 1
    # Base 100 + todo el bonus de tiempo: la racha no suma nada en este formato.
    assert resolved.record.points == 150


def test_streak_bonus_follows_the_configured_curve() -> None:
    rules = custom_rules(streak_bonus_step=7, streak_bonus_max=7)
    engine = SoloEngine(rules)
    run = engine.start()
    served_ = served(engine, run)

    first = engine.resolve(
        run,
        served_,
        correct_index=0,
        answer=answer(served_, choice=0, at_ms=served_.served_at_ms),
    )
    second_served = served(engine, first.run, now_ms=served_.served_at_ms)
    second = engine.resolve(
        first.run,
        second_served,
        correct_index=0,
        answer=answer(second_served, choice=0, at_ms=second_served.served_at_ms),
    )

    assert first.record.points == 150
    assert second.record.points == 157


def test_the_run_finishes_when_the_configured_lives_are_gone() -> None:
    engine = SoloEngine(custom_rules())
    run = engine.start()
    served_ = served(engine, run)

    first = engine.resolve(run, served_, correct_index=0, answer=None)
    assert first.run.finished is False
    assert first.run.lives == 1

    second_served = served(engine, first.run, now_ms=served_.served_at_ms)
    second = engine.resolve(first.run, second_served, correct_index=0, answer=None)
    assert second.run.finished is True
    assert second.run.lives == 0
    assert second.run.status is RunStatus.FINISHED


def test_resolving_is_pure_and_keeps_no_history_in_the_state() -> None:
    engine = SoloEngine(custom_rules())
    run = engine.start()
    served_ = served(engine, run)

    resolved = engine.resolve(
        run,
        served_,
        correct_index=0,
        answer=answer(served_, choice=0, at_ms=served_.served_at_ms),
    )

    assert run.round_index == 0
    assert run.score == 0
    assert run.lives == 2
    assert resolved.run is not run
    assert {field.name for field in fields(SoloRun)}.isdisjoint(
        {"records", "history", "answers"}
    )


def test_an_unknown_correct_index_is_rejected_before_grading() -> None:
    engine = SoloEngine(custom_rules())
    run = engine.start()
    served_ = served(engine, run)

    with pytest.raises(ValueError, match="correct_index fuera de rango"):
        engine.resolve(run, served_, correct_index=9, answer=None)


def test_a_finished_run_does_not_serve_or_resolve() -> None:
    engine = SoloEngine(custom_rules(lives=1))
    run = engine.start()
    served_ = served(engine, run)
    finished = engine.resolve(run, served_, correct_index=0, answer=None).run

    with pytest.raises(InvalidTransition, match="terminó"):
        engine.next_question(finished, question_id="q", now_ms=0)
    with pytest.raises(InvalidTransition, match="terminó"):
        engine.resolve(finished, served_, correct_index=0, answer=None)


def test_an_answer_from_another_round_is_rejected() -> None:
    engine = SoloEngine(custom_rules())
    served_ = ServedQuestion(
        round_index=1, question_id="q", difficulty=1, seconds=10, served_at_ms=0
    )

    with pytest.raises(InvalidTransition, match="ronda 1"):
        engine.resolve(engine.start(), served_, correct_index=0, answer=None)
