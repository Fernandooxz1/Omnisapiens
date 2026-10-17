"""`questions`: el enunciado, las opciones, el hash y la coherencia del media."""

from sqlalchemy.ext.asyncio import AsyncSession

from .constraints import acepta, rechaza, rechaza_al_confirmar
from .factories import question


async def test_a_question_is_accepted(session: AsyncSession) -> None:
    await acepta(session, question())


async def test_a_repeated_content_hash_is_rejected(session: AsyncSession) -> None:
    primera = question()
    await acepta(session, primera)

    await rechaza(
        session,
        question(content_hash=primera.content_hash),
        motivo="uq_questions_content_hash",
    )


async def test_two_questions_with_different_content_are_accepted(
    session: AsyncSession,
) -> None:
    await acepta(session, question(), question(category="history", prompt="Otra"))


async def test_an_unknown_category_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session, question(category="futbol"), motivo="ck_questions_category_known"
    )


async def test_difficulty_0_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session, question(difficulty=0), motivo="ck_questions_difficulty_range"
    )


async def test_difficulty_6_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session, question(difficulty=6), motivo="ck_questions_difficulty_range"
    )


async def test_an_unknown_language_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session, question(language="en"), motivo="ck_questions_language_known"
    )


async def test_an_empty_prompt_is_rejected(session: AsyncSession) -> None:
    await rechaza(session, question(prompt=""), motivo="ck_questions_prompt_clean")


async def test_a_prompt_with_a_trailing_space_is_rejected(
    session: AsyncSession,
) -> None:
    await rechaza(
        session, question(prompt="¿Río? "), motivo="ck_questions_prompt_clean"
    )


async def test_a_prompt_of_301_characters_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session, question(prompt="x" * 301), motivo="ck_questions_prompt_clean"
    )


async def test_a_prompt_of_300_characters_is_accepted(session: AsyncSession) -> None:
    # El borde de arriba: el límite es 300 inclusive, y el tipo no lo corta
    # porque es TEXT.
    await acepta(session, question(prompt="x" * 300))


async def test_three_options_are_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        question(options=["a", "b", "c"]),
        motivo="ck_questions_options_shape",
    )


async def test_five_options_are_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        question(options=["a", "b", "c", "d", "e"]),
        motivo="ck_questions_options_shape",
    )


async def test_a_numeric_option_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        question(options=["a", "b", "c", 7]),
        motivo="ck_questions_options_strings",
    )


async def test_a_null_option_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        question(options=["a", "b", "c", None]),
        motivo="ck_questions_options_strings",
    )


async def test_options_that_are_not_an_array_are_rejected(
    session: AsyncSession,
) -> None:
    await rechaza(
        session,
        question(options="a,b,c,d"),
        motivo="ck_questions_options_shape",
    )


async def test_correct_index_4_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session, question(correct_index=4), motivo="ck_questions_correct_index_choice"
    )


async def test_an_unknown_status_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session, question(status="borrador"), motivo="ck_questions_status_known"
    )


async def test_a_content_hash_of_63_characters_is_rejected(
    session: AsyncSession,
) -> None:
    await rechaza(
        session, question(content_hash="a" * 63), motivo="ck_questions_content_hash_hex"
    )


async def test_an_uppercase_content_hash_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session, question(content_hash="A" * 64), motivo="ck_questions_content_hash_hex"
    )


async def test_an_image_without_a_url_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session, question(media_type="image"), motivo="ck_questions_media_consistent"
    )


async def test_media_type_none_with_a_url_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        question(media_type="none", media_url="https://x/y.mp3"),
        motivo="ck_questions_media_consistent",
    )


async def test_an_audio_with_a_url_is_accepted(session: AsyncSession) -> None:
    await acepta(
        session,
        question(media_type="audio", media_url="https://x/y.mp3", prompt="Con audio"),
    )


async def test_removing_the_url_of_an_audio_question_is_rejected(
    session: AsyncSession,
) -> None:
    con_audio = question(media_type="audio", media_url="https://x/y.mp3")
    await acepta(session, con_audio)

    con_audio.media_url = None
    await rechaza_al_confirmar(session, "ck_questions_media_consistent")


async def test_defaults_of_a_new_question(session: AsyncSession) -> None:
    pregunta = question()

    await acepta(session, pregunta)

    assert pregunta.status == "draft"
    assert pregunta.media_type == "none"
    assert pregunta.language == "es"
    assert pregunta.tags == []
    assert pregunta.created_at is not None
    assert pregunta.updated_at is not None
