"""La máquina de estados de la sala, sin sockets ni reloj real."""

from app.game.match_engine import MatchConfig, MatchStatus, Player, difficulty_range
from app.game.protocols import (
    Error,
    MatchEnd,
    MatchStart,
    OpponentAnswered,
    OpponentReturned,
    ReconnectPending,
    RematchWaiting,
    RoundResult,
    RoundStart,
)
from app.game.protocols import RoomState as RoomStateMessage
from app.runtime import room as R
from app.services.question_bank import LoadedQuestion, RoundQuestion

HOST = "host-user"
GUEST = "guest-user"
GRACE = 20


def question(
    *,
    difficulty: int = 1,
    correct_index: int = 0,
    qid: str = "q",
    explanation: str | None = None,
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


def room(*, rounds: int = 3, seconds: int = 20) -> R.RoomState:
    return R.RoomState(
        code="K7M2QP", config=MatchConfig(rounds=rounds, seconds=seconds), host_id=HOST
    )


def joined(state: R.RoomState, *, now_ms: int = 0) -> R.RoomState:
    state, _ = R.join(state, user_id=HOST, nick="ana", now_ms=now_ms)
    state, _ = R.join(state, user_id=GUEST, nick="beto", now_ms=now_ms)
    return state


def playing(*, rounds: int = 3) -> R.RoomState:
    state, _ = R.start(joined(room(rounds=rounds)), user_id=HOST, match_id="m1")
    return state


def only(effects: R.Effects, user_id: str) -> object:
    messages = effects[user_id]
    assert len(messages) == 1, messages
    return messages[0]


def play_round(
    state: R.RoomState,
    *,
    a_choice: int = 0,
    b_choice: int = 0,
    correct_index: int = 0,
    start_ms: int = 1_000,
) -> tuple[R.RoomState, R.Effects]:
    assert state.match is not None
    low, _ = difficulty_range(state.match)
    state, _ = R.serve(
        state,
        question=question(
            difficulty=low,
            correct_index=correct_index,
            qid=f"q-{state.match.round_index}",
        ),
        now_ms=start_ms,
    )
    assert state.round is not None
    index = state.round.served.round_index
    state, _ = R.answer(
        state, user_id=HOST, round_index=index, choice=a_choice, now_ms=start_ms + 500
    )
    return R.answer(
        state, user_id=GUEST, round_index=index, choice=b_choice, now_ms=start_ms + 500
    )


def finished() -> R.RoomState:
    state = playing()
    for start_ms in (1_000, 30_000, 60_000):
        state, _ = play_round(
            state, a_choice=0, b_choice=1, correct_index=0, start_ms=start_ms
        )
    assert state.status is R.RoomStatus.FINISHED
    return state


def test_host_sits_in_a_and_guest_in_b() -> None:
    state = joined(room())

    assert state.seats[0] is not None and state.seats[0].user_id == HOST
    assert state.seats[1] is not None and state.seats[1].user_id == GUEST


def test_a_third_player_is_rejected() -> None:
    state = joined(room())

    same, effects = R.join(state, user_id="otro", nick="caro", now_ms=0)

    assert same is state
    assert isinstance(only(effects, "otro"), Error)


def test_join_broadcasts_the_state_to_both() -> None:
    state, effects = R.join(room(), user_id=HOST, nick="ana", now_ms=0)
    state, effects = R.join(state, user_id=GUEST, nick="beto", now_ms=0)

    host_state = only(effects, HOST)
    guest_state = only(effects, GUEST)
    assert isinstance(host_state, RoomStateMessage)
    assert isinstance(guest_state, RoomStateMessage)
    assert host_state.you.id == HOST
    assert guest_state.you.id == GUEST
    assert [p.id for p in guest_state.players] == [HOST, GUEST]


def test_only_the_host_starts() -> None:
    state = joined(room())

    same, effects = R.start(state, user_id=GUEST, match_id="m1")

    assert same is state
    assert isinstance(only(effects, GUEST), Error)


def test_start_needs_two_players() -> None:
    state, _ = R.join(room(), user_id=HOST, nick="ana", now_ms=0)

    same, effects = R.start(state, user_id=HOST, match_id="m1")

    assert same is state
    assert isinstance(only(effects, HOST), Error)


def test_start_sends_match_start_to_both() -> None:
    state = joined(room())

    state, effects = R.start(state, user_id=HOST, match_id="m1")

    assert state.status is R.RoomStatus.PLAYING
    assert isinstance(only(effects, HOST), MatchStart)
    assert isinstance(only(effects, GUEST), MatchStart)


def test_round_start_hides_the_correct_index() -> None:
    state = playing()

    state, effects = R.serve(state, question=question(correct_index=2), now_ms=1_000)

    message = only(effects, HOST)
    assert isinstance(message, RoundStart)
    assert not hasattr(message, "correct_index")
    assert message.ends_at == 21_000
    assert message.total_seconds == 20


def test_opponent_answered_is_sent_when_only_one_answered() -> None:
    state = playing()
    state, _ = R.serve(state, question=question(), now_ms=1_000)

    state, effects = R.answer(
        state, user_id=HOST, round_index=0, choice=1, now_ms=2_000
    )

    assert isinstance(only(effects, GUEST), OpponentAnswered)


def test_round_result_swaps_sides_per_player() -> None:
    state = playing()
    state, _ = R.serve(state, question=question(correct_index=0), now_ms=1_000)

    state, _ = R.answer(state, user_id=HOST, round_index=0, choice=0, now_ms=2_000)
    state, effects = R.answer(
        state, user_id=GUEST, round_index=0, choice=1, now_ms=2_000
    )

    for_user = only(effects, HOST)
    against = only(effects, GUEST)
    assert isinstance(for_user, RoundResult) and isinstance(against, RoundResult)
    assert for_user.you.correct is True
    assert for_user.opponent.correct is False
    assert for_user.scores.you == 148
    assert for_user.scores.opponent == 0
    assert against.you.correct is False
    assert against.scores.you == 0
    assert against.scores.opponent == 148


def test_a_repeated_answer_is_ignored() -> None:
    state = playing()
    state, _ = R.serve(state, question=question(), now_ms=1_000)
    state, _ = R.answer(state, user_id=HOST, round_index=0, choice=0, now_ms=2_000)

    same, effects = R.answer(state, user_id=HOST, round_index=0, choice=2, now_ms=3_000)

    assert same is state
    assert effects == {}


def test_an_old_round_is_rejected() -> None:
    state = playing()
    state, _ = R.serve(state, question=question(), now_ms=1_000)

    state, effects = R.answer(
        state, user_id=HOST, round_index=9, choice=0, now_ms=2_000
    )

    assert isinstance(only(effects, HOST), Error)


def test_the_round_resolves_on_the_clock() -> None:
    state = playing()
    state, _ = R.serve(state, question=question(correct_index=0), now_ms=1_000)

    state, effects = R.expire(state, now_ms=21_000)

    assert state.round is None
    assert isinstance(only(effects, HOST), RoundResult)


def test_expire_does_nothing_before_the_deadline() -> None:
    state = playing()
    state, _ = R.serve(state, question=question(), now_ms=1_000)

    same, effects = R.expire(state, now_ms=20_999)

    assert same is state
    assert effects == {}


def test_match_end_after_all_rounds() -> None:
    state = finished()

    assert state.match is not None
    assert state.match.status is MatchStatus.FINISHED
    assert state.match.winner is Player.A


def test_finishing_broadcasts_match_end_with_the_reason() -> None:
    state = playing()
    effects: R.Effects = {}
    for start_ms in (1_000, 30_000, 60_000):
        state, effects = play_round(
            state, a_choice=0, b_choice=1, correct_index=0, start_ms=start_ms
        )

    # La última ronda manda su `round_result` y, encima, el `match_end`.
    end = effects[HOST][-1]
    assert isinstance(end, MatchEnd)
    assert end.winner == "you"
    assert end.reason == "completed"
    assert len(end.rounds) == 3
    assert effects[GUEST][-1].winner == "opponent"  # type: ignore[union-attr]


def test_a_tie_opens_a_tiebreak_with_half_the_time() -> None:
    state = playing()
    for start_ms in (1_000, 30_000, 60_000):
        state, _ = play_round(
            state, a_choice=1, b_choice=1, correct_index=0, start_ms=start_ms
        )

    assert state.status is R.RoomStatus.PLAYING
    assert state.match is not None and state.match.in_tiebreak
    assert difficulty_range(state.match) == (4, 5)
    state, effects = R.serve(state, question=question(difficulty=4), now_ms=100_000)
    assert only(effects, HOST).total_seconds == 10  # type: ignore[union-attr]


def test_needs_next_round_only_between_rounds_and_with_both_players() -> None:
    state = playing()
    assert state.needs_next_round

    state, _ = R.serve(state, question=question(), now_ms=1_000)
    assert not state.needs_next_round


def test_disconnect_pauses_the_round_and_warns_the_other() -> None:
    state = playing()
    state, _ = R.serve(state, question=question(), now_ms=1_000)

    state, effects = R.disconnect(
        state, user_id=GUEST, now_ms=5_000, grace_seconds=GRACE
    )

    assert isinstance(only(effects, HOST), ReconnectPending)
    assert state.round is not None and state.round.paused_since_ms == 5_000
    assert state.grace_deadline_ms == 25_000


def test_the_paused_round_does_not_expire() -> None:
    state = playing()
    state, _ = R.serve(state, question=question(), now_ms=1_000)
    state, _ = R.disconnect(state, user_id=GUEST, now_ms=5_000, grace_seconds=GRACE)

    # 22 s: ya venció la ronda (21 s) pero sigue abierta la gracia (25 s).
    same, effects = R.expire(state, now_ms=22_000)

    assert same is state
    assert effects == {}


def test_a_reconnect_within_the_grace_resumes_the_clock() -> None:
    state = playing()
    state, _ = R.serve(state, question=question(), now_ms=1_000)
    state, _ = R.answer(state, user_id=HOST, round_index=0, choice=0, now_ms=3_000)
    state, _ = R.disconnect(state, user_id=GUEST, now_ms=5_000, grace_seconds=GRACE)

    state, effects = R.join(state, user_id=GUEST, nick="beto", now_ms=9_000)

    assert isinstance(only(effects, HOST), OpponentReturned)
    assert state.round is not None
    assert state.round.paused_since_ms is None
    assert state.grace_deadline_ms is None
    # 4 s de pausa corren todo: el arranque y la respuesta ya dada, por igual.
    assert state.round.served.served_at_ms == 5_000
    assert state.round.answers[0] is not None
    assert state.round.answers[0].answered_at_ms == 7_000


def test_missing_the_grace_hands_the_win_to_the_present_player() -> None:
    state = playing()
    state, _ = R.serve(state, question=question(), now_ms=1_000)
    state, _ = R.disconnect(state, user_id=GUEST, now_ms=5_000, grace_seconds=GRACE)

    state, effects = R.expire(state, now_ms=25_000)

    assert state.status is R.RoomStatus.FINISHED
    assert state.match is not None and state.match.status is MatchStatus.ABANDONED
    assert state.match.winner is Player.A
    end = only(effects, HOST)
    assert isinstance(end, MatchEnd) and end.reason == "abandoned"


def test_both_gone_is_a_void_match() -> None:
    state = playing()
    state, _ = R.serve(state, question=question(), now_ms=1_000)
    state, _ = R.disconnect(state, user_id=HOST, now_ms=3_000, grace_seconds=GRACE)
    state, _ = R.disconnect(state, user_id=GUEST, now_ms=4_000, grace_seconds=GRACE)

    state, _ = R.expire(state, now_ms=23_000)

    assert state.match is not None and state.match.status is MatchStatus.VOID
    assert state.match.winner is None


def test_rematch_needs_both_and_warns_the_other() -> None:
    state = finished()

    state, effects = R.rematch(state, user_id=HOST)
    assert isinstance(only(effects, GUEST), RematchWaiting)
    assert not state.ready_for_rematch

    state, _ = R.rematch(state, user_id=GUEST)
    assert state.ready_for_rematch


def test_rematch_before_finishing_is_rejected() -> None:
    state = playing()

    state, effects = R.rematch(state, user_id=HOST)

    assert isinstance(only(effects, HOST), Error)


def test_leaving_a_finished_room_returns_it_to_waiting() -> None:
    state = finished()

    state, _ = R.disconnect(state, user_id=GUEST, now_ms=200_000, grace_seconds=GRACE)

    assert state.status is R.RoomStatus.WAITING
    assert state.match is None and state.match_id is None


def test_sync_returns_the_state_and_the_round_in_course() -> None:
    state = playing()
    state, _ = R.serve(state, question=question(), now_ms=1_000)

    _, effects = R.sync(state, user_id=HOST, now_ms=2_000)

    messages = effects[HOST]
    assert isinstance(messages[0], RoomStateMessage)
    assert isinstance(messages[1], RoundStart)
