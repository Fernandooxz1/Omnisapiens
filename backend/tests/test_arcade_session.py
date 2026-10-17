"""La corrida arcade pura: una conexión, una partida, sin sockets ni base.

Las transiciones se prueban con el reloj fijo del test y un `Random` con semilla:
una corrida entera corre en microsegundos y sin depender del orden de un pool.
"""

from collections.abc import Callable
from dataclasses import fields
from random import Random

import pytest

from app.game import protocols
from app.game.answers import RejectReason, ServedQuestion
from app.game.arcade_engine import ArcadeRun, RunStatus
from app.game.errors import InvalidTransition
from app.runtime import arcade_session
from app.runtime.arcade_session import ArcadeState, RoundInFlight
from app.services.question_bank import LoadedQuestion, RoundQuestion

NOW = 1_000


def loaded(
    qid: str = "q-0",
    *,
    difficulty: int = 1,
    correct_index: int = 1,
    explanation: str | None = "Porque sí.",
) -> LoadedQuestion:
    return LoadedQuestion(
        question=RoundQuestion(
            id=qid,
            prompt="¿Cuál es el río más largo?",
            options=["Paraná", "Amazonas", "Orinoco", "Magdalena"],
            category="geography",
            difficulty=difficulty,
            explanation=explanation,
        ),
        correct_index=correct_index,
    )


def started() -> ArcadeState:
    return arcade_session.start("run-1").state


def served(
    state: ArcadeState, question: LoadedQuestion | None = None, *, now_ms: int = NOW
) -> ArcadeState:
    step = arcade_session.serve(
        state, question=question or loaded(), now_ms=now_ms, rng=Random(1)
    )
    return step.state


def correct_choice(state: ArcadeState) -> int:
    assert state.round is not None
    return state.round.question.correct_index


def test_start_opens_the_run_with_three_lives_and_twenty_seconds() -> None:
    step = arcade_session.start("run-1")

    assert step.state.run_id == "run-1"
    assert step.state.run == ArcadeRun()
    assert step.state.needs_next_question is True
    assert step.record is None
    assert step.effects == (protocols.ArcadeStart(run_id="run-1", lives=3, seconds=20),)


def test_serve_sends_the_question_without_the_answer() -> None:
    step = arcade_session.serve(started(), question=loaded(), now_ms=NOW, rng=Random(1))
    message = step.effects[0]

    assert isinstance(message, protocols.ArcadeQuestion)
    assert message.round == 0
    assert message.prompt == "¿Cuál es el río más largo?"
    assert message.category == "geography"
    assert message.difficulty == 1
    assert message.seconds == 20
    assert message.ends_at == NOW + 20_000
    assert (message.score, message.lives, message.streak, message.correct_count) == (
        0,
        3,
        0,
        0,
    )
    assert "correct_index" not in {field.name for field in fields(message)}
    # Las opciones viajan barajadas y el índice correcto se remapeó con ellas.
    assert step.state.round is not None
    assert message.options[step.state.round.question.correct_index] == "Amazonas"


def test_a_correct_answer_scores_and_keeps_the_lives() -> None:
    step = arcade_session.serve(started(), question=loaded(), now_ms=NOW, rng=Random(1))
    choice = correct_choice(step.state)

    answered = arcade_session.answer(
        step.state, round_index=0, choice=choice, now_ms=NOW + 1_000
    )

    assert answered.record is not None
    assert answered.record.correct is True
    assert answered.record.points == 148
    assert answered.record.elapsed_ms == 1_000
    assert answered.record.choice == choice
    assert answered.state.run.score == 148
    assert answered.state.run.lives == 3
    assert answered.state.run.streak == 1
    assert answered.state.run.correct_count == 1
    assert answered.state.needs_next_question is True

    result = answered.effects[0]
    assert isinstance(result, protocols.ArcadeResult)
    assert result.round == 0
    assert result.correct_index == choice
    assert result.explanation == "Porque sí."
    assert result.you == protocols.RoundChoice(
        choice=choice, ms=1_000, points=148, correct=True
    )
    assert (result.score, result.lives, result.streak, result.correct_count) == (
        148,
        3,
        1,
        1,
    )


def test_a_wrong_answer_loses_a_life_and_resets_the_streak() -> None:
    step = arcade_session.serve(started(), question=loaded(), now_ms=NOW, rng=Random(1))
    wrong = (correct_choice(step.state) + 1) % 4

    answered = arcade_session.answer(
        step.state, round_index=0, choice=wrong, now_ms=NOW + 2_000
    )

    assert answered.record is not None
    assert answered.record.correct is False
    assert answered.record.points == 0
    assert answered.state.run.lives == 2
    assert answered.state.run.streak == 0
    result = answered.effects[0]
    assert isinstance(result, protocols.ArcadeResult)
    assert result.you == protocols.RoundChoice(
        choice=wrong, ms=2_000, points=0, correct=False
    )


def test_an_answer_at_the_deadline_still_counts() -> None:
    step = arcade_session.serve(started(), question=loaded(), now_ms=NOW, rng=Random(1))
    assert step.state.round is not None

    answered = arcade_session.answer(
        step.state,
        round_index=0,
        choice=correct_choice(step.state),
        now_ms=step.state.round.served.ends_at_ms,
    )

    assert answered.record is not None
    assert answered.record.correct is True
    assert answered.record.rejected is None


def test_an_answer_after_the_deadline_is_missing() -> None:
    step = arcade_session.serve(started(), question=loaded(), now_ms=NOW, rng=Random(1))
    assert step.state.round is not None
    deadline = step.state.round.served.ends_at_ms

    answered = arcade_session.answer(
        step.state,
        round_index=0,
        choice=correct_choice(step.state),
        now_ms=deadline + 1,
    )

    assert answered.record is not None
    assert answered.record.rejected is RejectReason.OUTSIDE_WINDOW
    assert answered.record.choice is None
    assert answered.state.run.lives == 2


def test_expire_waits_for_the_deadline_then_resolves_as_missing() -> None:
    step = arcade_session.serve(started(), question=loaded(), now_ms=NOW, rng=Random(1))
    assert step.state.round is not None
    deadline = step.state.round.served.ends_at_ms

    early = arcade_session.expire(step.state, now_ms=deadline - 1)
    assert early.state is step.state
    assert early.effects == ()
    assert early.record is None

    late = arcade_session.expire(step.state, now_ms=deadline)
    assert late.record is not None
    assert late.record.correct is False
    assert late.record.choice is None
    assert late.record.elapsed_ms == 20_000
    assert late.state.run.lives == 2


def test_the_third_miss_finishes_the_run() -> None:
    state = started()
    now = NOW
    for index in range(3):
        state = served(state, loaded(f"q-{index}"), now_ms=now)
        assert state.round is not None
        ended = arcade_session.expire(state, now_ms=state.round.served.ends_at_ms)
        state = ended.state
        assert ended.record is not None
        now += 100_000

    assert state.finished is True
    assert state.run.status is RunStatus.FINISHED
    assert state.run.lives == 0
    assert state.needs_next_question is False
    assert [message.type for message in ended.effects] == [
        "arcade_result",
        "arcade_end",
    ]
    end = ended.effects[1]
    assert isinstance(end, protocols.ArcadeEnd)
    assert end == protocols.ArcadeEnd(
        run_id="run-1",
        score=0,
        correct_count=0,
        max_difficulty=1,
        longest_streak=0,
        rank_global=None,
        rank_weekly=None,
        personal_best=None,
        is_new_best=False,
    )


def test_a_finished_run_does_not_serve_or_answer() -> None:
    state = started()
    for index in range(3):
        state = served(state, loaded(f"q-{index}"))
        assert state.round is not None
        state = arcade_session.expire(state, now_ms=state.round.served.ends_at_ms).state

    with pytest.raises(InvalidTransition, match="terminó"):
        arcade_session.serve(state, question=loaded("q-9"), now_ms=NOW, rng=Random(1))

    answered = arcade_session.answer(state, round_index=3, choice=0, now_ms=NOW)
    assert answered.state is state
    error = answered.effects[0]
    assert isinstance(error, protocols.Error)
    assert error.code == "NOT_PLAYING"

    expired = arcade_session.expire(state, now_ms=NOW + 10**9)
    assert expired.state is state
    assert expired.effects == ()


def test_answering_without_a_round_is_rejected() -> None:
    state = started()

    answered = arcade_session.answer(state, round_index=0, choice=0, now_ms=NOW)

    assert answered.state is state
    error = answered.effects[0]
    assert isinstance(error, protocols.Error)
    assert error.code == "NOT_PLAYING"


def test_an_old_round_is_rejected_without_touching_the_round() -> None:
    state = served(started())

    answered = arcade_session.answer(state, round_index=4, choice=0, now_ms=NOW)

    assert answered.state is state
    assert answered.state.round is not None
    error = answered.effects[0]
    assert isinstance(error, protocols.Error)
    assert error.code == "ROUND_MISMATCH"


def test_a_choice_outside_the_range_is_rejected() -> None:
    state = served(started())

    answered = arcade_session.answer(state, round_index=0, choice=4, now_ms=NOW)

    assert answered.state is state
    assert answered.state.round is not None
    error = answered.effects[0]
    assert isinstance(error, protocols.Error)
    assert error.code == "BAD_CHOICE"


def test_a_question_cannot_repeat_within_the_run() -> None:
    first = arcade_session.serve(
        started(), question=loaded("q-0"), now_ms=NOW, rng=Random(1)
    )
    answered = arcade_session.answer(
        first.state,
        round_index=0,
        choice=correct_choice(first.state),
        now_ms=NOW,
    )
    assert answered.state.seen == frozenset({"q-0"})

    with pytest.raises(InvalidTransition, match="ya salió"):
        arcade_session.serve(
            answered.state,
            question=loaded("q-0"),
            now_ms=NOW,
            rng=Random(1),
        )


def test_a_question_can_repeat_as_a_last_resort() -> None:
    first = arcade_session.serve(
        started(), question=loaded("q-0"), now_ms=NOW, rng=Random(1)
    )
    answered = arcade_session.answer(
        first.state,
        round_index=0,
        choice=correct_choice(first.state),
        now_ms=NOW,
    )

    # §9.4: el pool se quedó sin preguntas nuevas, se repite y se sigue jugando.
    repeated = arcade_session.serve(
        answered.state,
        question=loaded("q-0"),
        now_ms=NOW,
        rng=Random(1),
        allow_repeat=True,
    )

    assert repeated.state.round is not None
    assert repeated.state.round.served.question_id == "q-0"
    assert repeated.state.seen == frozenset({"q-0"})
    assert repeated.effects[0].type == "arcade_question"


def test_difficulty_and_time_follow_the_accumulated_hits() -> None:
    state = started()
    now = NOW
    for index in range(4):
        served_step = arcade_session.serve(
            state, question=loaded(f"q-{index}"), now_ms=now, rng=Random(index)
        )
        state = served_step.state
        assert state.round is not None
        state = arcade_session.answer(
            state,
            round_index=index,
            choice=state.round.question.correct_index,
            now_ms=now,
        ).state
        now += 10

    next_step = arcade_session.serve(
        state, question=loaded("q-4"), now_ms=now, rng=Random(1)
    )
    question = next_step.effects[0]
    assert isinstance(question, protocols.ArcadeQuestion)
    assert question.difficulty == 2
    assert question.seconds == 19
    assert question.correct_count == 4
    assert question.streak == 4


def _served_round(*, round_index: int = 0, question_id: str = "q-0") -> RoundInFlight:
    return RoundInFlight(
        served=ServedQuestion(
            round_index=round_index,
            question_id=question_id,
            difficulty=1,
            seconds=20,
            served_at_ms=0,
        ),
        question=loaded(question_id),
    )


@pytest.mark.parametrize(
    ("factory", "motivo"),
    [
        (lambda: ArcadeState(run_id=""), "run_id vacío"),
        (
            lambda: ArcadeState(
                run_id="run-1",
                run=ArcadeRun(lives=0, status=RunStatus.FINISHED),
                round=_served_round(),
                seen=frozenset({"q-0"}),
            ),
            "terminada",
        ),
        (
            lambda: ArcadeState(
                run_id="run-1",
                round=_served_round(round_index=3),
                seen=frozenset({"q-0"}),
            ),
            "no es la del motor",
        ),
        (
            lambda: ArcadeState(run_id="run-1", round=_served_round()),
            "no está en las vistas",
        ),
    ],
)
def test_impossible_states_are_rejected(
    factory: Callable[[], ArcadeState], motivo: str
) -> None:
    with pytest.raises(ValueError, match=motivo):
        factory()
