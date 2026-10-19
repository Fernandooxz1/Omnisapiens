"""`content_items` y `content_solutions`: el ítem genérico y su solución aparte."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ContentSolution

from .constraints import acepta, rechaza
from .factories import content_item, content_solution


async def test_a_content_item_is_accepted(session: AsyncSession) -> None:
    await acepta(session, content_item())


async def test_any_non_empty_kind_is_accepted(session: AsyncSession) -> None:
    # `kind` no está atado a una lista: los modos se registran en código.
    await acepta(
        session,
        content_item(kind="quiz"),
        content_item(kind="rosco", payload={"v": 1, "letter": "A"}),
    )


async def test_an_empty_kind_is_rejected(session: AsyncSession) -> None:
    await rechaza(session, content_item(kind=""), motivo="ck_content_items_kind_clean")


async def test_a_kind_with_spaces_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session, content_item(kind=" quiz "), motivo="ck_content_items_kind_clean"
    )


async def test_an_unknown_status_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session, content_item(status="borrador"), motivo="ck_content_items_status_known"
    )


async def test_difficulty_0_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session, content_item(difficulty=0), motivo="ck_content_items_difficulty_range"
    )


async def test_difficulty_6_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session, content_item(difficulty=6), motivo="ck_content_items_difficulty_range"
    )


async def test_a_payload_that_is_not_an_object_is_rejected(
    session: AsyncSession,
) -> None:
    await rechaza(
        session,
        content_item(payload=["v", 1]),
        motivo="ck_content_items_payload_object",
    )


async def test_a_payload_without_version_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        content_item(payload={"prompt": "sin versión"}),
        motivo="ck_content_items_payload_version_matches_schema",
    )


async def test_a_payload_version_that_differs_from_the_column_is_rejected(
    session: AsyncSession,
) -> None:
    await rechaza(
        session,
        content_item(schema_version=2, payload={"v": 1}),
        motivo="ck_content_items_payload_version_matches_schema",
    )


async def test_a_string_version_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        content_item(payload={"v": "1"}),
        motivo="ck_content_items_payload_version_matches_schema",
    )


async def test_a_boolean_version_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        content_item(payload={"v": True}),
        motivo="ck_content_items_payload_version_matches_schema",
    )


async def test_a_repeated_content_hash_is_rejected(session: AsyncSession) -> None:
    primero = content_item()
    await acepta(session, primero)

    await rechaza(
        session,
        content_item(content_hash=primero.content_hash),
        motivo="uq_content_items_content_hash",
    )


async def test_a_content_hash_of_63_characters_is_rejected(
    session: AsyncSession,
) -> None:
    await rechaza(
        session,
        content_item(content_hash="a" * 63),
        motivo="ck_content_items_content_hash_hex",
    )


async def test_an_uppercase_content_hash_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        content_item(content_hash="A" * 64),
        motivo="ck_content_items_content_hash_hex",
    )


async def test_an_unknown_media_type_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        content_item(media_type="video", media_url="https://x/y.mp4"),
        motivo="ck_content_items_media_type_known",
    )


async def test_an_image_without_a_url_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        content_item(media_type="image"),
        motivo="ck_content_items_media_consistent",
    )


async def test_media_type_none_with_a_url_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        content_item(media_type="none", media_url="https://x/y.mp3"),
        motivo="ck_content_items_media_consistent",
    )


async def test_an_audio_with_a_url_is_accepted(session: AsyncSession) -> None:
    await acepta(session, content_item(media_type="audio", media_url="https://x/y.mp3"))


async def test_defaults_of_a_new_content_item(session: AsyncSession) -> None:
    item = content_item()

    await acepta(session, item)

    assert item.status == "draft"
    assert item.language == "es"
    assert item.media_type == "none"
    assert item.created_at is not None
    assert item.updated_at is not None


async def test_a_content_item_supersedes_another(session: AsyncSession) -> None:
    anterior = content_item()
    await acepta(session, anterior)

    await acepta(session, content_item(supersedes_id=anterior.id))


async def test_a_solution_is_accepted(session: AsyncSession) -> None:
    item = content_item()

    await acepta(session, item, content_solution(item.id))


async def test_a_solution_without_its_item_is_rejected(session: AsyncSession) -> None:
    await rechaza(
        session,
        content_solution(uuid.uuid4()),
        motivo="fk_content_solutions_content_id",
    )


async def test_deleting_the_item_deletes_its_solution(
    session: AsyncSession,
) -> None:
    item = content_item()
    await acepta(session, item, content_solution(item.id))

    await session.delete(item)
    await session.commit()

    assert (await session.execute(select(ContentSolution))).scalars().all() == []
