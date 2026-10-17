import pytest

from app.game.answers import Answer, RejectReason
from app.game.errors import InvalidTransition
from app.game.match_engine import (
    MAX_TIEBREAK_ROUNDS,
    MatchConfig,
    MatchState,
    MatchStatus,
    Player,
    RoundRecord,
    abandon,
    difficulty_range,
    next_round,
    resolve_round,
    void,
)


def config() -> MatchConfig:
    return MatchConfig(rounds=3, seconds=20)


def state() -> MatchState:
    return MatchState(config=config())


def served(state: MatchState, *, difficulty: int = 1, now_ms: int = 1_000):
    return next_round(
        state,
        question_id=f"q-{state.round_index}",
        difficulty=difficulty,
        now_ms=now_ms,
    )


def answer(served_question, *, choice: int, offset_ms: int) -> Answer:
    return Answer(
        round_index=served_question.round_index,
        choice=choice,
        answered_at_ms=served_question.served_at_ms + offset_ms,
    )


def play(
    state: MatchState,
    *,
    a_choice: int | None,
    b_choice: int | None,
    difficulty: int = 1,
):
    served_question = served(state, difficulty=difficulty)
    return resolve_round(
        state,
        served_question,
        correct_index=0,
        a=None
        if a_choice is None
        else answer(served_question, choice=a_choice, offset_ms=1_000),
        b=None
        if b_choice is None
        else answer(served_question, choice=b_choice, offset_ms=1_000),
    )


def test_config_only_accepts_planned_values() -> None:
    with pytest.raises(ValueError, match="rounds no permitido"):
        MatchConfig(rounds=4, seconds=20)
    with pytest.raises(ValueError, match="seconds no permitido"):
        MatchConfig(rounds=3, seconds=15)


@pytest.mark.parametrize(
    ("round_index", "expected"),
    [
        (0, (1, 2)),
        (1, (1, 2)),
        (2, (2, 3)),
        (3, (2, 3)),
        (4, (3, 4)),
        (5, (3, 4)),
        (6, (4, 5)),
    ],
)
def test_difficulty_range_by_round(round_index: int, expected: tuple[int, int]) -> None:
    fake_rounds = tuple(
        RoundRecord(
            round_index=index,
            question_id=f"q-{index}",
            difficulty=1,
            seconds=20,
            correct_index=0,
            a_choice=None,
            b_choice=None,
            a_ms=None,
            b_ms=None,
            a_correct=False,
            b_correct=False,
            a_points=0,
            b_points=0,
            a_rejected=None,
            b_rejected=None,
        )
        for index in range(round_index)
    )
    state_ = MatchState(config=MatchConfig(rounds=7, seconds=20), rounds=fake_rounds)

    assert difficulty_range(state_) == expected


def test_served_round_uses_configured_seconds() -> None:
    served_question = served(state())

    assert served_question.seconds == 20
    assert served_question.round_index == 0
    assert served_question.question_id == "q-0"


def test_difficulty_outside_the_round_tier_is_rejected() -> None:
    with pytest.raises(ValueError, match="fuera del tramo"):
        served(state(), difficulty=4)


def test_both_players_are_scored_independently() -> None:
    resolved = play(state(), a_choice=0, b_choice=1)

    assert resolved.record.a_correct is True
    assert resolved.record.b_correct is False
    assert resolved.record.a_points == 148
    assert resolved.record.b_points == 0
    assert resolved.record.a_ms == 1_000
    assert resolved.record.b_ms == 1_000
    assert resolved.state.score_a == 148
    assert resolved.state.score_b == 0


def test_unanswered_round_scores_zero() -> None:
    resolved = play(state(), a_choice=None, b_choice=0)

    assert resolved.record.a_choice is None
    assert resolved.record.a_ms is None
    assert resolved.record.a_points == 0
    assert resolved.record.b_points == 148


def test_late_answer_is_discarded() -> None:
    state_ = state()
    served_question = served(state_)
    late = Answer(
        round_index=0, choice=0, answered_at_ms=served_question.ends_at_ms + 1
    )

    resolved = resolve_round(state_, served_question, correct_index=0, a=late, b=None)

    assert resolved.record.a_rejected is RejectReason.OUTSIDE_WINDOW
    assert resolved.record.a_choice is None
    assert resolved.record.a_points == 0
    assert resolved.record.a_ms is None


def test_match_finishes_when_all_rounds_are_played() -> None:
    state_ = state()
    for _ in range(3):
        state_ = play(state_, a_choice=0, b_choice=1, difficulty=2).state

    assert state_.status is MatchStatus.FINISHED
    assert state_.winner is Player.A
    assert state_.round_index == 3
    assert state_.score_a > state_.score_b


def test_tie_opens_a_tiebreak_with_half_the_time() -> None:
    state_ = state()
    for _ in range(3):
        state_ = play(state_, a_choice=1, b_choice=2, difficulty=2).state

    assert state_.status is MatchStatus.PLAYING
    assert state_.in_tiebreak is True
    assert state_.seconds_per_round == 10
    assert difficulty_range(state_) == (4, 5)


def test_tiebreak_ends_when_someone_scores() -> None:
    state_ = state()
    for _ in range(3):
        state_ = play(state_, a_choice=1, b_choice=2, difficulty=2).state

    state_ = play(state_, a_choice=0, b_choice=1, difficulty=4).state

    assert state_.status is MatchStatus.FINISHED
    assert state_.winner is Player.A


def test_tiebreak_repeats_while_tied() -> None:
    state_ = state()
    for _ in range(3):
        state_ = play(state_, a_choice=1, b_choice=2, difficulty=2).state

    state_ = play(state_, a_choice=1, b_choice=2, difficulty=5).state

    assert state_.status is MatchStatus.PLAYING
    assert state_.in_tiebreak is True
    assert state_.round_index == 4


def test_the_tiebreak_stops_at_the_cap_with_a_draw() -> None:
    state_ = state()
    for _ in range(3):
        state_ = play(state_, a_choice=1, b_choice=2, difficulty=2).state
    for _ in range(MAX_TIEBREAK_ROUNDS):
        state_ = play(state_, a_choice=1, b_choice=2, difficulty=4).state

    assert state_.status is MatchStatus.FINISHED
    assert state_.winner is None
    assert state_.round_index == 3 + MAX_TIEBREAK_ROUNDS


def test_scores_are_derived_from_the_round_history() -> None:
    state_ = state()
    for _ in range(3):
        state_ = play(state_, a_choice=0, b_choice=1, difficulty=2).state

    assert state_.score_a == sum(record.a_points for record in state_.rounds)
    assert state_.score_b == sum(record.b_points for record in state_.rounds)


def test_abandon_hands_the_win_to_the_other_player() -> None:
    state_ = play(state(), a_choice=0, b_choice=1).state

    state_ = abandon(state_, gone=Player.B)

    assert state_.status is MatchStatus.ABANDONED
    assert state_.winner is Player.A


def test_void_match_has_no_winner() -> None:
    state_ = void(state())

    assert state_.status is MatchStatus.VOID
    assert state_.winner is None


def test_cannot_resolve_a_finished_match() -> None:
    state_ = state()
    for _ in range(3):
        state_ = play(state_, a_choice=0, b_choice=1, difficulty=2).state

    with pytest.raises(InvalidTransition):
        served(state_)


def test_cannot_resolve_the_wrong_round() -> None:
    state_ = state()
    served_question = served(state_)
    state_ = play(state_, a_choice=0, b_choice=1).state

    with pytest.raises(InvalidTransition):
        resolve_round(state_, served_question, correct_index=0, a=None, b=None)


def test_round_indices_must_be_consecutive() -> None:
    record = RoundRecord(
        round_index=3,
        question_id="q",
        difficulty=1,
        seconds=20,
        correct_index=0,
        a_choice=None,
        b_choice=None,
        a_ms=None,
        b_ms=None,
        a_correct=False,
        b_correct=False,
        a_points=0,
        b_points=0,
        a_rejected=None,
        b_rejected=None,
    )

    with pytest.raises(ValueError, match="consecutivas"):
        MatchState(config=config(), rounds=(record,))


def test_finished_match_needs_a_winner() -> None:
    with pytest.raises(ValueError, match="terminada sin ganador"):
        MatchState(config=config(), status=MatchStatus.FINISHED)
