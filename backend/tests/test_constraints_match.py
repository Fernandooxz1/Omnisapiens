"""`rooms`, `matches` y `match_rounds`: la sala, la partida y sus rondas."""

import uuid
from typing import NamedTuple

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ContentItem, Match, MatchRound, Room, User

from .constraints import acepta, rechaza
from .factories import match, match_round, quiz_content, room, user


class Escenario(NamedTuple):
    ana: User
    beto: User
    anfitrion: User
    sala: Room
    pregunta: ContentItem
    partida: Match


async def escenario(session: AsyncSession) -> Escenario:
    """Lo que la sonda de shell armaba antes de empezar: dos jugadores, el host de
    la sala, un ítem de contenido y una partida ya en la base."""
    ana, beto, anfitrion = user(), user(), user()
    pregunta, solucion = quiz_content()
    sala = room(anfitrion.id)
    partida = match(player_a_id=ana.id, player_b_id=beto.id, room_id=sala.id)
    await acepta(session, ana, beto, anfitrion, sala, pregunta, solucion, partida)
    return Escenario(ana, beto, anfitrion, sala, pregunta, partida)


# ---------------------------------------------------------------- rooms


@pytest.fixture
async def host(session: AsyncSession) -> uuid.UUID:
    """Un host real ya en la base.

    `rooms.host_user_id` es FK: sin el host insertado, el rechazo que llegaría
    sería el de la FK y no el del `CHECK` que cada test quiere probar.
    """
    jugador = user()
    await acepta(session, jugador)
    return jugador.id


async def test_a_room_is_accepted(session: AsyncSession, host: uuid.UUID) -> None:
    await acepta(session, room(host))


async def test_a_room_code_with_a_zero_is_rejected(
    session: AsyncSession, host: uuid.UUID
) -> None:
    # El alfabeto excluye 0/1/I/O: se dicta por voz o se lee de una pantalla.
    await rechaza(session, room(host, code="ABCDE0"), motivo="ck_rooms_code_alphabet")


async def test_a_room_code_with_an_i_is_rejected(
    session: AsyncSession, host: uuid.UUID
) -> None:
    await rechaza(session, room(host, code="ABCDEI"), motivo="ck_rooms_code_alphabet")


async def test_a_room_code_of_5_characters_is_rejected(
    session: AsyncSession, host: uuid.UUID
) -> None:
    await rechaza(session, room(host, code="ABCDE"), motivo="ck_rooms_code_alphabet")


async def test_a_lowercase_room_code_is_rejected(
    session: AsyncSession, host: uuid.UUID
) -> None:
    await rechaza(session, room(host, code="abcdef"), motivo="ck_rooms_code_alphabet")


async def test_a_repeated_room_code_is_rejected(
    session: AsyncSession, host: uuid.UUID
) -> None:
    sala = room(host)
    await acepta(session, sala)

    await rechaza(session, room(host, code=sala.code), motivo="uq_rooms_code")


async def test_seconds_that_are_not_offered_are_rejected(
    session: AsyncSession, host: uuid.UUID
) -> None:
    await rechaza(
        session,
        room(host, config={"rounds": 7, "seconds": 15}),
        motivo="ck_rooms_config_valid",
    )


async def test_a_config_without_seconds_is_rejected(
    session: AsyncSession, host: uuid.UUID
) -> None:
    await rechaza(
        session, room(host, config={"rounds": 7}), motivo="ck_rooms_config_valid"
    )


async def test_a_config_without_rounds_is_rejected(
    session: AsyncSession, host: uuid.UUID
) -> None:
    await rechaza(
        session, room(host, config={"seconds": 20}), motivo="ck_rooms_config_valid"
    )


async def test_rounds_as_text_are_rejected(
    session: AsyncSession, host: uuid.UUID
) -> None:
    await rechaza(
        session,
        room(host, config={"rounds": "7", "seconds": 20}),
        motivo="ck_rooms_config_valid",
    )


async def test_a_config_that_is_not_an_object_is_rejected(
    session: AsyncSession, host: uuid.UUID
) -> None:
    await rechaza(session, room(host, config=[]), motivo="ck_rooms_config_valid")


async def test_an_unknown_room_status_is_rejected(
    session: AsyncSession, host: uuid.UUID
) -> None:
    await rechaza(session, room(host, status="abierta"), motivo="ck_rooms_status_known")


async def test_a_room_without_an_expiry_is_rejected(
    session: AsyncSession, host: uuid.UUID
) -> None:
    await rechaza(session, room(host, expires_at=None), motivo="expires_at")


async def test_a_room_with_a_missing_host_is_rejected(session: AsyncSession) -> None:
    await rechaza(session, room(uuid.uuid4()), motivo="fk_rooms_host_user_id")


async def test_defaults_of_a_new_room(session: AsyncSession, host: uuid.UUID) -> None:
    sala = room(host)

    await acepta(session, sala)

    assert sala.status == "waiting"
    assert sala.created_at is not None


# ---------------------------------------------------------------- matches


async def test_a_match_is_accepted(session: AsyncSession) -> None:
    await escenario(session)


async def test_both_sides_cannot_be_the_same_player(session: AsyncSession) -> None:
    ana = user()
    await acepta(session, ana)

    await rechaza(
        session,
        match(player_a_id=ana.id, player_b_id=ana.id),
        motivo="ck_matches_players_differ",
    )


async def test_a_match_without_a_room_is_accepted(session: AsyncSession) -> None:
    # Sala nula es válida: el historial sobrevive a que se purgue la sala.
    ana, beto = user(), user()
    await acepta(session, ana, beto)

    await acepta(session, match(player_a_id=ana.id, player_b_id=beto.id))


async def test_a_match_in_a_missing_room_is_rejected(session: AsyncSession) -> None:
    ana, beto = user(), user()
    await acepta(session, ana, beto)

    await rechaza(
        session,
        match(player_a_id=ana.id, player_b_id=beto.id, room_id=uuid.uuid4()),
        motivo="fk_matches_room_id",
    )


async def test_a_match_with_an_invalid_config_is_rejected(
    session: AsyncSession,
) -> None:
    ana, beto = user(), user()
    await acepta(session, ana, beto)

    await rechaza(
        session,
        match(
            player_a_id=ana.id,
            player_b_id=beto.id,
            config={"rounds": 4, "seconds": 20},
        ),
        motivo="ck_matches_config_valid",
    )


async def test_an_unknown_match_status_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        match(esc.ana.id, esc.beto.id, status="tie"),
        motivo="ck_matches_status_known",
    )


async def test_a_negative_score_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        match(esc.ana.id, esc.beto.id, score_a=-1),
        motivo="ck_matches_scores_not_negative",
    )


async def test_a_winner_who_did_not_play_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        match(esc.ana.id, esc.beto.id, winner_id=uuid.uuid4()),
        motivo="ck_matches_winner_plays",
    )


async def test_a_winner_who_played_is_accepted(session: AsyncSession) -> None:
    esc = await escenario(session)

    await acepta(session, match(esc.ana.id, esc.beto.id, winner_id=esc.beto.id))


async def test_defaults_of_a_new_match(session: AsyncSession) -> None:
    esc = await escenario(session)
    partida = match(esc.ana.id, esc.beto.id)

    await acepta(session, partida)

    assert partida.status == "playing"
    assert partida.score_a == 0
    assert partida.score_b == 0
    assert partida.ended_at is None
    assert partida.started_at is not None


# ---------------------------------------------------------------- match_rounds


async def test_a_round_is_accepted(session: AsyncSession) -> None:
    esc = await escenario(session)

    await acepta(session, match_round(esc.partida.id, question_id=esc.pregunta.id))


async def test_a_repeated_round_index_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)
    await acepta(session, match_round(esc.partida.id, round_index=0))

    await rechaza(
        session,
        match_round(esc.partida.id, round_index=0),
        motivo="uq_match_rounds_match_id_round_index",
    )


async def test_a_round_where_nobody_hit_is_accepted(session: AsyncSession) -> None:
    esc = await escenario(session)

    await acepta(
        session,
        match_round(
            esc.partida.id, a_choice=2, b_choice=3, a_correct=False, b_correct=False
        ),
    )


async def test_a_round_where_nobody_answered_is_accepted(session: AsyncSession) -> None:
    esc = await escenario(session)

    await acepta(
        session,
        match_round(
            esc.partida.id,
            a_choice=None,
            b_choice=None,
            a_ms=None,
            b_ms=None,
            a_correct=False,
            b_correct=False,
        ),
    )


async def test_a_negative_round_index_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        match_round(esc.partida.id, round_index=-1),
        motivo="ck_match_rounds_round_index_not_negative",
    )


async def test_difficulty_0_in_a_round_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        match_round(esc.partida.id, difficulty=0),
        motivo="ck_match_rounds_difficulty_range",
    )


async def test_a_round_of_0_seconds_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        # Los `ms` en 0 para que la única regla violada sea la de los segundos.
        match_round(esc.partida.id, seconds=0, a_ms=0, b_ms=0),
        motivo="ck_match_rounds_seconds_positive",
    )


async def test_correct_index_4_in_a_round_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        match_round(
            esc.partida.id,
            correct_index=4,
            a_choice=None,
            b_choice=None,
            a_ms=None,
            b_ms=None,
            a_correct=False,
            b_correct=False,
        ),
        motivo="ck_match_rounds_correct_index_choice",
    )


async def test_a_choice_out_of_range_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        match_round(esc.partida.id, a_choice=4, a_correct=False),
        motivo="ck_match_rounds_choices_in_range",
    )


async def test_a_choice_without_measured_time_is_rejected(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        match_round(esc.partida.id, a_ms=None),
        motivo="ck_match_rounds_times_consistent",
    )


async def test_measured_time_without_a_choice_is_rejected(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        match_round(esc.partida.id, a_choice=None, a_correct=False),
        motivo="ck_match_rounds_times_consistent",
    )


async def test_a_negative_measured_time_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        match_round(esc.partida.id, a_ms=-3_000),
        motivo="ck_match_rounds_times_consistent",
    )


async def test_a_hit_with_another_option_is_rejected(session: AsyncSession) -> None:
    # `a_correct` no se deriva de `a_choice`: si se contradicen, lo dice la base.
    esc = await escenario(session)

    await rechaza(
        session,
        match_round(esc.partida.id, a_choice=2, a_correct=True),
        motivo="ck_match_rounds_correctness_from_choice",
    )


async def test_a_hit_without_choosing_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        match_round(esc.partida.id, a_choice=None, a_ms=None, a_correct=True),
        motivo="ck_match_rounds_correctness_from_choice",
    )


async def test_a_rejection_with_a_stored_choice_is_rejected(
    session: AsyncSession,
) -> None:
    # Una respuesta fuera de la ventana no tiene elección que guardar.
    esc = await escenario(session)

    await rechaza(
        session,
        match_round(esc.partida.id, a_rejected="outside_window", a_choice=1),
        motivo="ck_match_rounds_rejections_consistent",
    )


async def test_an_unknown_reject_reason_is_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        match_round(
            esc.partida.id,
            a_choice=None,
            a_ms=None,
            a_correct=False,
            a_rejected="trampa",
        ),
        motivo="ck_match_rounds_rejections_consistent",
    )


async def test_an_answer_out_of_the_window_is_accepted(session: AsyncSession) -> None:
    esc = await escenario(session)

    await acepta(
        session,
        match_round(
            esc.partida.id,
            a_choice=None,
            a_ms=None,
            a_correct=False,
            a_rejected="outside_window",
        ),
    )


async def test_negative_points_in_a_round_are_rejected(session: AsyncSession) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        match_round(esc.partida.id, a_points=-5),
        motivo="ck_match_rounds_points_not_negative",
    )


async def test_a_round_with_a_missing_question_is_rejected(
    session: AsyncSession,
) -> None:
    esc = await escenario(session)

    await rechaza(
        session,
        match_round(esc.partida.id, question_id=uuid.uuid4()),
        motivo="fk_match_rounds_question_id",
    )


async def test_deleting_a_question_leaves_the_round_standing(
    session: AsyncSession,
) -> None:
    # SET NULL: la ronda se puede auditar después de purgar la pregunta.
    esc = await escenario(session)
    ronda = match_round(esc.partida.id, question_id=esc.pregunta.id)
    await acepta(session, ronda)

    await session.delete(esc.pregunta)
    await session.commit()
    await session.refresh(ronda)

    assert ronda.question_id is None


async def test_deleting_a_match_deletes_its_rounds(session: AsyncSession) -> None:
    esc = await escenario(session)
    await acepta(session, match_round(esc.partida.id), match_round(esc.partida.id))

    await session.delete(esc.partida)
    await session.commit()

    quedan = await session.scalar(
        select(func.count())
        .select_from(MatchRound)
        .where(MatchRound.match_id == esc.partida.id)
    )
    assert quedan == 0
