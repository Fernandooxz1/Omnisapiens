"""`game_sessions`, `game_participants`, `session_items` y `session_attempts`."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import NamedTuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ContentItem,
    GameParticipant,
    GameSession,
    Room,
    SessionAttempt,
    SessionItem,
    User,
)

from .constraints import acepta, rechaza
from .factories import (
    game_participant,
    game_session,
    quiz_content,
    room,
    session_attempt,
    session_item,
    user,
)


class Escenario(NamedTuple):
    ana: User
    beto: User
    pregunta: ContentItem
    sala: Room
    sesion: GameSession


async def escenario(session: AsyncSession) -> Escenario:
    """Dos jugadores, un ítem de contenido, una sala y una sesión ya escritas."""
    ana, beto = user(), user()
    pregunta, solucion = quiz_content()
    sala = room(ana.id)
    sesion = game_session(owner_user_id=ana.id, room_id=sala.id)
    await acepta(session, ana, beto, sala, pregunta, solucion, sesion)
    return Escenario(ana, beto, pregunta, sala, sesion)


# ---------------------------------------------------------------- game_sessions


async def test_a_session_is_accepted(session: AsyncSession) -> None:
    await escenario(session)


async def test_an_unknown_session_status_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        game_session(
            status="terminada",
            started_at=datetime.now(UTC) - timedelta(minutes=1),
            ended_at=datetime.now(UTC),
        ),
        motivo="ck_game_sessions_status_known",
    )


async def test_a_playing_session_cannot_have_an_end(session: AsyncSession) -> None:
    await rechaza(
        session,
        game_session(ended_at=datetime.now(UTC)),
        motivo="ck_game_sessions_ending_matches_status",
    )


async def test_a_closed_session_must_have_an_end(session: AsyncSession) -> None:
    await rechaza(
        session,
        game_session(status="finished"),
        motivo="ck_game_sessions_ending_matches_status",
    )


async def test_a_negative_score_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        game_session(score=-1),
        motivo="ck_game_sessions_counters_not_negative",
    )


async def test_a_negative_correct_count_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        game_session(correct_count=-1),
        motivo="ck_game_sessions_counters_not_negative",
    )


async def test_a_streak_longer_than_the_hits_is_rejected(
    session: AsyncSession,
) -> None:
    await rechaza(
        session,
        game_session(correct_count=2, longest_streak=3),
        motivo="ck_game_sessions_streak_within_corrects",
    )


async def test_a_negative_streak_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        game_session(longest_streak=-1),
        motivo="ck_game_sessions_streak_within_corrects",
    )


async def test_difficulty_0_in_a_session_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        game_session(max_difficulty=0),
        motivo="ck_game_sessions_difficulty_range",
    )


async def test_difficulty_6_in_a_session_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        game_session(max_difficulty=6),
        motivo="ck_game_sessions_difficulty_range",
    )


async def test_a_session_cannot_end_before_it_starts(
    session: AsyncSession,
) -> None:
    ahora = datetime.now(UTC)
    await rechaza(
        session,
        game_session(
            status="finished",
            started_at=ahora,
            ended_at=ahora - timedelta(seconds=1),
        ),
        motivo="ck_game_sessions_ends_after_start",
    )


async def test_a_config_that_is_not_an_object_is_rejected(
    session: AsyncSession,
) -> None:
    await rechaza(
        session,
        game_session(config=["lives", 3]),
        motivo="ck_game_sessions_config_object",
    )


async def test_defaults_of_a_new_session(session: AsyncSession) -> None:
    sesion = game_session()

    await acepta(session, sesion)

    assert sesion.status == "playing"
    assert sesion.score == 0
    assert sesion.correct_count == 0
    assert sesion.longest_streak == 0
    assert sesion.max_difficulty == 1
    assert sesion.started_at is not None
    assert sesion.ended_at is None


async def test_a_versus_session_has_neither_owner_nor_room(
    session: AsyncSession,
) -> None:
    await acepta(
        session,
        game_session(mode="trivia_versus", play_format="versus", owner_user_id=None),
    )


async def test_a_session_with_a_missing_owner_is_rejected(
    session: AsyncSession,
) -> None:
    await rechaza(
        session, game_session(owner_user_id=uuid.uuid4()), motivo="owner_user_id"
    )


async def test_a_session_in_a_missing_room_is_rejected(
    session: AsyncSession,
) -> None:
    await rechaza(session, game_session(room_id=uuid.uuid4()), motivo="room_id")


async def test_deleting_a_room_leaves_the_session_standing(
    session: AsyncSession,
) -> None:
    # SET NULL: purgar salas viejas no se lleva el historial.
    esc = await escenario(session)

    await session.delete(esc.sala)
    await session.commit()
    await session.refresh(esc.sesion)

    assert esc.sesion.room_id is None


async def test_deleting_a_session_deletes_its_children(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)
    participante = game_participant(esc.sesion.id, esc.ana.id)
    item = session_item(esc.sesion.id)
    intento = session_attempt(item.id)
    await acepta(session, participante, item, intento)

    await session.delete(esc.sesion)
    await session.commit()

    for modelo in (GameParticipant, SessionItem, SessionAttempt):
        quedan = await session.scalar(select(func.count()).select_from(modelo))
        assert quedan == 0


# ------------------------------------------------------------ game_participants


async def test_a_participant_is_accepted(session: AsyncSession) -> None:
    esc = await escenario(session)

    await acepta(session, game_participant(esc.sesion.id, esc.ana.id, seat=1))


async def test_two_participants_cannot_share_a_seat(session: AsyncSession) -> None:
    esc = await escenario(session)
    await acepta(session, game_participant(esc.sesion.id, esc.ana.id, seat=0))

    await rechaza(
        session,
        game_participant(esc.sesion.id, esc.beto.id, seat=0),
        motivo="pk_game_participants",
    )


async def test_a_user_cannot_play_twice_in_the_same_session(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)
    await acepta(session, game_participant(esc.sesion.id, esc.ana.id, seat=0))

    await rechaza(
        session,
        game_participant(esc.sesion.id, esc.ana.id, seat=1),
        motivo="uq_game_participants_session_id_user_id",
    )


async def test_the_same_user_can_play_in_two_sessions(session: AsyncSession) -> None:
    esc = await escenario(session)
    otra = game_session()
    await acepta(session, otra)

    await acepta(
        session,
        game_participant(esc.sesion.id, esc.ana.id),
        game_participant(otra.id, esc.ana.id),
    )


async def test_a_participant_with_a_missing_user_is_rejected(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        game_participant(esc.sesion.id, uuid.uuid4()),
        motivo="fk_game_participants_user_id",
    )


async def test_an_unknown_outcome_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        game_participant(esc.sesion.id, esc.ana.id, outcome="empate"),
        motivo="ck_game_participants_outcome_known",
    )


async def test_a_negative_participant_score_is_rejected(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        game_participant(esc.sesion.id, esc.ana.id, score=-1),
        motivo="ck_game_participants_score_not_negative",
    )


# ---------------------------------------------------------------- session_items


async def test_a_session_item_is_accepted(session: AsyncSession) -> None:
    esc = await escenario(session)

    await acepta(session, session_item(esc.sesion.id, content_id=esc.pregunta.id))


async def test_a_repeated_item_key_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)
    await acepta(session, session_item(esc.sesion.id, item_key="0"))

    await rechaza(
        session,
        session_item(esc.sesion.id, item_key="0"),
        motivo="uq_session_items_session_id_item_key",
    )


async def test_difficulty_0_in_an_item_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        session_item(esc.sesion.id, difficulty=0),
        motivo="ck_session_items_difficulty_range",
    )


async def test_an_item_of_0_seconds_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        session_item(esc.sesion.id, seconds=0),
        motivo="ck_session_items_seconds_positive",
    )


async def test_a_negative_position_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        session_item(esc.sesion.id, position=-1),
        motivo="ck_session_items_position_not_negative",
    )


async def test_an_item_with_a_missing_session_is_rejected(
    session: AsyncSession,
) -> None:
    await rechaza(
        session,
        session_item(uuid.uuid4()),
        motivo="fk_session_items_session_id",
    )


async def test_an_item_with_a_missing_content_is_rejected(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        session_item(esc.sesion.id, content_id=uuid.uuid4()),
        motivo="fk_session_items_content_id",
    )


async def test_deleting_the_content_leaves_the_item_standing(
    session: AsyncSession,
) -> None:
    # La solución congelada hace que la fila se pueda auditar sin el contenido.
    esc = await escenario(session)
    item = session_item(esc.sesion.id, content_id=esc.pregunta.id)
    await acepta(session, item)

    await session.delete(esc.pregunta)
    await session.commit()
    await session.refresh(item)

    assert item.content_id is None


# ------------------------------------------------------------- session_attempts


async def test_an_attempt_is_accepted(session: AsyncSession) -> None:
    esc = await escenario(session)
    item = session_item(esc.sesion.id)

    await acepta(session, item, session_attempt(item.id))


async def test_a_repeated_attempt_sequence_is_rejected(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)
    item = session_item(esc.sesion.id)
    await acepta(session, item, session_attempt(item.id, attempt_seq=0))

    await rechaza(
        session,
        session_attempt(item.id, attempt_seq=0),
        motivo="uq_session_attempts_item_id_seat_attempt_seq",
    )


async def test_the_same_sequence_in_another_seat_is_accepted(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)
    item = session_item(esc.sesion.id)

    await acepta(
        session,
        item,
        session_attempt(item.id, attempt_seq=0, seat=0),
        session_attempt(item.id, attempt_seq=0, seat=1),
    )


async def test_a_negative_attempt_sequence_is_rejected(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)
    item = session_item(esc.sesion.id)

    await rechaza(
        session,
        item,
        session_attempt(item.id, attempt_seq=-1),
        motivo="ck_session_attempts_attempt_seq_not_negative",
    )


async def test_a_negative_elapsed_time_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)
    item = session_item(esc.sesion.id)

    await rechaza(
        session,
        item,
        session_attempt(item.id, elapsed_ms=-1),
        motivo="ck_session_attempts_elapsed_ms_not_negative",
    )


async def test_negative_points_in_an_attempt_are_rejected(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)
    item = session_item(esc.sesion.id)

    await rechaza(
        session,
        item,
        session_attempt(item.id, points=-1),
        motivo="ck_session_attempts_points_not_negative",
    )


async def test_an_attempt_with_a_missing_item_is_rejected(
    session: AsyncSession,
) -> None:
    await rechaza(
        session, session_attempt(uuid.uuid4()), motivo="fk_session_attempts_item_id"
    )


async def test_deleting_an_item_deletes_its_attempts(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)
    item = session_item(esc.sesion.id)
    await acepta(session, item, session_attempt(item.id))

    await session.delete(item)
    await session.commit()

    quedan = await session.scalar(
        select(func.count())
        .select_from(SessionAttempt)
        .where(SessionAttempt.item_id == item.id)
    )
    assert quedan == 0
