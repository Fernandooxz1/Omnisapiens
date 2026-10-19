"""El servicio de sesiones: arranque, cierre atómico y cierres sin final.

La base es la real (fixture `session`): lo que se prueba es justamente el
`UPDATE` + `INSERT` en una transacción, y eso SQLite no lo reproduce.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GameParticipant, GameSession, SessionAttempt, SessionItem
from app.services import sessions
from app.services.sessions import (
    AttemptRecord,
    ItemRecord,
    Participant,
    ParticipantResult,
    SessionState,
    abandon_session,
    finish_session,
    invalidate_session,
    start_session,
)

from .factories import user

NOW = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
LATER = NOW + timedelta(minutes=3)


def item(key: str, **overrides: Any) -> ItemRecord:
    return ItemRecord(
        **(
            {
                "item_key": key,
                "position": int(key),
                "difficulty": 2,
                "seconds": 20,
                "served_at": NOW,
                "deadline_at": NOW + timedelta(seconds=20),
                "solution": {"v": 1, "correct_index": 1},
            }
            | overrides
        )
    )


def attempt(key: str, **overrides: Any) -> AttemptRecord:
    return AttemptRecord(
        **(
            {
                "item_key": key,
                "attempt_seq": 0,
                "submitted_at": NOW + timedelta(seconds=3),
                "submission": {"type": "choice", "index": 1},
                "correct": True,
                "elapsed_ms": 3_000,
                "points": 145,
            }
            | overrides
        )
    )


async def start(
    session: AsyncSession,
    *,
    session_id: uuid.UUID | None = None,
    participants: tuple[Participant, ...] = (),
    **overrides: Any,
) -> uuid.UUID:
    session_id = session_id or uuid.uuid4()
    base: dict[str, Any] = {
        "mode": "trivia_arcade",
        "content_kind": "quiz",
        "play_format": "arcade",
        "ruleset_version": 1,
        "config": {"lives": 3},
        "started_at": NOW,
        "participants": participants,
    }
    await start_session(session, session_id=session_id, **(base | overrides))
    return session_id


async def _count(session: AsyncSession, model: Any) -> int:
    return int(await session.scalar(select(func.count()).select_from(model)) or 0)


async def _session_row(session: AsyncSession, session_id: uuid.UUID) -> Any:
    """Columnas sueltas: el objeto que dejó `start_session` sigue en el mapa."""
    return (
        await session.execute(
            select(
                GameSession.status,
                GameSession.score,
                GameSession.correct_count,
                GameSession.longest_streak,
                GameSession.max_difficulty,
                GameSession.started_at,
                GameSession.ended_at,
            ).where(GameSession.id == session_id)
        )
    ).one()


# ------------------------------------------------------------------- arranque


async def test_start_writes_the_session_playing_with_its_seats(
    session: AsyncSession,
) -> None:
    ana, beto = user(), user()
    session.add_all([ana, beto])
    await session.flush()

    session_id = await start(
        session,
        participants=(
            Participant(seat=0, user_id=ana.id),
            Participant(seat=1, user_id=beto.id),
        ),
        mode="trivia_versus",
        play_format="versus",
        config={"rounds": 7, "seconds": 20},
    )

    row = await _session_row(session, session_id)
    assert row.status == "playing"
    assert (row.score, row.correct_count, row.longest_streak) == (0, 0, 0)
    assert row.max_difficulty == 1
    assert row.started_at == NOW
    assert row.ended_at is None

    seats = (
        await session.execute(
            select(GameParticipant.seat, GameParticipant.user_id)
            .where(GameParticipant.session_id == session_id)
            .order_by(GameParticipant.seat)
        )
    ).all()
    assert seats == [(0, ana.id), (1, beto.id)]


async def test_start_rejects_a_negative_seat() -> None:
    with pytest.raises(ValueError, match="seat negativo"):
        Participant(seat=-1, user_id=uuid.uuid4())


# --------------------------------------------------------------------- cierre


async def test_finish_writes_the_summary_items_and_attempts(
    session: AsyncSession,
) -> None:
    ana = user()
    session.add(ana)
    await session.flush()
    session_id = await start(
        session,
        owner_user_id=ana.id,
        participants=(Participant(seat=0, user_id=ana.id),),
    )

    await finish_session(
        session,
        session_id=session_id,
        state=SessionState(
            ended_at=LATER,
            score=290,
            correct_count=2,
            longest_streak=2,
            max_difficulty=3,
        ),
        items=(item("0"), item("1", difficulty=3)),
        attempts=(attempt("0"), attempt("1", correct=False, points=0)),
        participants=(ParticipantResult(seat=0, score=290, outcome="win"),),
    )

    row = await _session_row(session, session_id)
    assert row.status == "finished"
    assert (row.score, row.correct_count, row.longest_streak) == (290, 2, 2)
    assert (row.max_difficulty, row.ended_at) == (3, LATER)

    items = (
        await session.execute(
            select(
                SessionItem.id,
                SessionItem.item_key,
                SessionItem.difficulty,
                SessionItem.solution_snapshot,
            )
            .where(SessionItem.session_id == session_id)
            .order_by(SessionItem.position)
        )
    ).all()
    assert [(i.item_key, i.difficulty) for i in items] == [("0", 2), ("1", 3)]
    assert items[0].solution_snapshot == {"v": 1, "correct_index": 1}

    attempts = (
        await session.execute(
            select(
                SessionAttempt.item_id,
                SessionAttempt.correct,
                SessionAttempt.points,
            ).order_by(SessionAttempt.points.desc())
        )
    ).all()
    assert [a.points for a in attempts] == [145, 0]
    # El intento apunta al ítem que el servicio insertó, no a uno inventado.
    assert attempts[0].item_id == items[0].id

    participant = await session.get(GameParticipant, (session_id, 0))
    assert participant is not None
    assert (participant.score, participant.outcome) == (290, "win")


async def test_finish_is_idempotent(session: AsyncSession) -> None:
    session_id = await start(session)
    state = SessionState(ended_at=LATER, score=145, correct_count=1, longest_streak=1)

    await finish_session(
        session,
        session_id=session_id,
        state=state,
        items=(item("0"),),
        attempts=(attempt("0"),),
    )
    await finish_session(
        session,
        session_id=session_id,
        state=SessionState(ended_at=LATER, score=999, correct_count=9),
        items=(item("0"),),
        attempts=(attempt("0"),),
    )

    row = await _session_row(session, session_id)
    assert row.status == "finished"
    assert row.score == 145
    assert await _count(session, SessionItem) == 1
    assert await _count(session, SessionAttempt) == 1


async def test_finish_without_a_row_warns_and_does_not_raise(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    warnings: list[str] = []
    monkeypatch.setattr(
        sessions.logger, "warning", lambda msg, *args: warnings.append(msg % args)
    )

    await finish_session(
        session,
        session_id=uuid.uuid4(),
        state=SessionState(ended_at=LATER),
        items=(item("0"),),
        attempts=(),
    )

    assert warnings
    assert "no estaba en la base" in warnings[0]
    assert await _count(session, SessionItem) == 0


async def test_duplicate_item_keys_are_rejected(session: AsyncSession) -> None:
    session_id = await start(session)

    with pytest.raises(ValueError, match="item_key duplicado"):
        await finish_session(
            session,
            session_id=session_id,
            state=SessionState(ended_at=LATER),
            items=(item("0"), item("0", position=1)),
            attempts=(),
        )

    assert await _session_row(session, session_id) is not None
    assert (await _session_row(session, session_id)).status == "playing"
    assert await _count(session, SessionItem) == 0


async def test_an_attempt_without_its_item_is_rejected(session: AsyncSession) -> None:
    session_id = await start(session)

    with pytest.raises(ValueError, match="intento sin ítem"):
        await finish_session(
            session,
            session_id=session_id,
            state=SessionState(ended_at=LATER),
            items=(item("0"),),
            attempts=(attempt("1"),),
        )


async def test_a_repeated_attempt_sequence_is_rejected(
    session: AsyncSession,
) -> None:
    session_id = await start(session)

    with pytest.raises(ValueError, match="attempt_seq duplicado"):
        await finish_session(
            session,
            session_id=session_id,
            state=SessionState(ended_at=LATER),
            items=(item("0"),),
            attempts=(attempt("0"), attempt("0")),
        )


async def test_a_result_for_a_seat_that_never_played_is_rejected(
    session: AsyncSession,
) -> None:
    session_id = await start(session)

    with pytest.raises(ValueError, match="la silla 1 no jugó"):
        await finish_session(
            session,
            session_id=session_id,
            state=SessionState(ended_at=LATER),
            items=(),
            attempts=(),
            participants=(ParticipantResult(seat=1),),
        )


# ------------------------------------------------------- cierres sin final


async def test_abandon_closes_the_session_without_history(
    session: AsyncSession,
) -> None:
    session_id = await start(session)

    await abandon_session(session, session_id=session_id, ended_at=LATER)

    row = await _session_row(session, session_id)
    assert (row.status, row.ended_at) == ("abandoned", LATER)
    assert await _count(session, SessionItem) == 0


async def test_invalidate_takes_the_session_out_of_circulation(
    session: AsyncSession,
) -> None:
    session_id = await start(session)

    await invalidate_session(session, session_id=session_id, ended_at=LATER)

    row = await _session_row(session, session_id)
    assert (row.status, row.ended_at) == ("invalid", LATER)


async def test_a_closed_session_is_not_reopened_by_a_second_close(
    session: AsyncSession,
) -> None:
    session_id = await start(session)
    await abandon_session(session, session_id=session_id, ended_at=LATER)

    await finish_session(
        session,
        session_id=session_id,
        state=SessionState(ended_at=LATER, score=500),
        items=(item("0"),),
        attempts=(attempt("0"),),
    )

    row = await _session_row(session, session_id)
    assert row.status == "abandoned"
    assert row.score == 0
    assert await _count(session, SessionItem) == 0
