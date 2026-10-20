"""El motor solo: curvas parametrizadas, vidas y fin de partida.

Las curvas genéricas fijan que las reglas salgan de `SoloRules` y que el estado
no esconda historial. La sección final juega con `ARCADE_RULES`: son los valores
del formato que el cliente ya conoce y no pueden cambiar con el refactor.
"""

from dataclasses import fields

import pytest

from app.game.answers import Answer, RejectReason, ServedQuestion
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
from app.game.modes.arcade import ARCADE_RULES
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


# --------------------------------------------------------------------------
# El formato arcade con sus valores reales: el refactor no puede moverlos.
# --------------------------------------------------------------------------

ARCADE = SoloEngine(ARCADE_RULES)


def arcade_served(run: SoloRun, *, now_ms: int = 1_000) -> ServedQuestion:
    return served(ARCADE, run, now_ms=now_ms)


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
def test_arcade_difficulty_progression(correct_count: int, expected: int) -> None:
    assert ARCADE_RULES.difficulty_for(correct_count) == expected


@pytest.mark.parametrize(
    ("correct_count", "expected"),
    [(0, 20), (2, 20), (3, 19), (6, 18), (42, 6), (45, 5), (90, 5)],
)
def test_arcade_seconds_progression(correct_count: int, expected: int) -> None:
    assert ARCADE_RULES.seconds_for(correct_count) == expected


def test_the_first_arcade_question_is_easy_and_long() -> None:
    served_ = arcade_served(ARCADE.start())

    assert served_.difficulty == 1
    assert served_.seconds == 20
    assert served_.served_at_ms == 1_000
    assert served_.ends_at_ms == 21_000


def test_arcade_difficulty_follows_the_accumulated_hits() -> None:
    run = SoloRun(
        rules=ARCADE_RULES,
        lives=ARCADE_LIVES,
        correct_count=4,
        streak=4,
        longest_streak=4,
        score=600,
    )

    assert arcade_served(run).difficulty == 2


def test_an_arcade_correct_answer_scores_and_keeps_the_lives() -> None:
    run = ARCADE.start()
    served_ = arcade_served(run)

    resolved = ARCADE.resolve(
        run, served_, correct_index=2, answer=answer(served_, choice=2, at_ms=2_000)
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


def test_an_arcade_wrong_answer_loses_a_life_and_resets_the_streak() -> None:
    run = SoloRun(
        rules=ARCADE_RULES,
        lives=ARCADE_LIVES,
        correct_count=4,
        streak=4,
        longest_streak=4,
        score=600,
    )
    served_ = arcade_served(run, now_ms=10_000)

    resolved = ARCADE.resolve(
        run, served_, correct_index=0, answer=answer(served_, choice=3, at_ms=11_000)
    )

    assert resolved.record.points == 0
    assert resolved.run.score == 600
    assert resolved.run.lives == 2
    assert resolved.run.streak == 0
    assert resolved.run.longest_streak == 4
    assert resolved.run.status is RunStatus.PLAYING


def test_an_arcade_late_answer_counts_as_missing() -> None:
    run = ARCADE.start()
    served_ = arcade_served(run)

    resolved = ARCADE.resolve(
        run, served_, correct_index=0, answer=answer(served_, choice=0, at_ms=21_001)
    )

    assert resolved.record.rejected is RejectReason.OUTSIDE_WINDOW
    assert resolved.record.correct is False
    assert resolved.record.choice is None
    assert resolved.record.elapsed_ms == 20_000
    assert resolved.record.points == 0
    assert resolved.run.lives == 2


def test_an_arcade_missing_answer_counts_as_wrong() -> None:
    run = ARCADE.start()
    served_ = arcade_served(run)

    resolved = ARCADE.resolve(run, served_, correct_index=0, answer=None)

    assert resolved.record.choice is None
    assert resolved.record.correct is False
    assert resolved.run.lives == 2
    assert resolved.run.score == 0


def test_the_third_arcade_miss_finishes_the_run() -> None:
    run = ARCADE.start()
    for _ in range(3):
        served_ = arcade_served(run)
        run = ARCADE.resolve(run, served_, correct_index=0, answer=None).run

    assert run.status is RunStatus.FINISHED
    assert run.finished is True
    assert run.lives == 0


def test_the_arcade_streak_bonus_grows_with_consecutive_hits() -> None:
    run = ARCADE.start()
    points = []

    for _ in range(3):
        served_ = arcade_served(run)
        resolved = ARCADE.resolve(
            run,
            served_,
            correct_index=0,
            answer=answer(served_, choice=0, at_ms=served_.served_at_ms),
        )
        points.append(resolved.record.points)
        run = resolved.run

    assert run.streak == 3
    assert points[0] < points[1] < points[2]


def test_the_arcade_record_keeps_what_was_served() -> None:
    run = ARCADE.start()
    served_ = arcade_served(run)

    record = ARCADE.resolve(run, served_, correct_index=0, answer=None).record

    assert record.question_id == "q-0"
    assert record.difficulty == served_.difficulty
    assert record.seconds == served_.seconds
    assert record.round_index == served_.round_index


def test_arcade_max_difficulty_tracks_the_played_questions() -> None:
    run = ARCADE.start()
    for _ in range(5):
        served_ = arcade_served(run)
        run = ARCADE.resolve(
            run,
            served_,
            correct_index=0,
            answer=answer(served_, choice=0, at_ms=served_.served_at_ms),
        ).run

    assert run.max_difficulty == 2


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
def test_impossible_arcade_states_are_rejected(overrides: dict[str, object]) -> None:
    base: dict[str, object] = {"lives": ARCADE_LIVES}
    with pytest.raises(
        ValueError, match=r"fuera de rango|negativo|streak|se contradicen"
    ):
        SoloRun(rules=ARCADE_RULES, **(base | overrides))  # type: ignore[arg-type]
