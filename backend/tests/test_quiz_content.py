"""El `ContentKind` del quiz: fila → payload, candidatas y carga con solución."""

import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.cli import _build_parser
from app.game.modes.base import ItemRef
from app.game.modes.quiz import QUIZ, QuizCandidatesConfig, get_content_kind
from app.game.modes.quiz.content import RowError
from app.game.modes.quiz.models import QuizPayload, QuizSolution

from .constraints import acepta
from .factories import content_item, content_solution


def fila(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "category": "geography",
        "difficulty": "2",
        "prompt": "¿Cuál es el río más largo?",
        "option_a": "Paraná",
        "option_b": "Amazonas",
        "option_c": "Orinoco",
        "option_d": "Magdalena",
        "correct": "B",
        "explanation": "El Amazonas.",
        "source": "manual",
        "tags": "mundo;ríos",
    }
    return base | overrides


# --- parseo ------------------------------------------------------------------


def test_a_valid_row_becomes_a_public_payload_and_a_solution() -> None:
    draft = QUIZ.parse_row(fila())

    assert draft.schema_version == 1
    assert draft.difficulty == 2
    assert draft.categories == ("geography",)
    assert draft.language == "es"
    assert draft.public.media_type == "none"
    assert draft.public.media_url is None
    assert draft.public.payload == {
        "v": 1,
        "prompt": "¿Cuál es el río más largo?",
        "options": ["Paraná", "Amazonas", "Orinoco", "Magdalena"],
        "media": {"type": "none", "url": None},
    }
    assert draft.solution.payload == {
        "v": 1,
        "correct_index": 1,
        "explanation": "El Amazonas.",
    }


def test_the_public_payload_does_not_carry_the_solution() -> None:
    draft = QUIZ.parse_row(fila())

    assert "correct_index" not in draft.public.payload
    assert "explanation" not in draft.public.payload
    assert "correct_index" in draft.solution.payload


def test_the_fingerprint_is_the_frozen_prompt_hash() -> None:
    from app.services.importer import content_hash

    assert QUIZ.fingerprint(QUIZ.parse_row(fila())) == content_hash(
        "¿Cuál es el río más largo?"
    )
    assert QUIZ.fingerprint(
        QUIZ.parse_row(fila(prompt="Cual es el rio mas largo"))
    ) == QUIZ.fingerprint(QUIZ.parse_row(fila()))


@pytest.mark.parametrize(
    "overrides",
    [
        {"category": "futbol"},
        {"difficulty": "6"},
        {"prompt": "  "},
        {"option_c": ""},
        {"option_b": "paraná"},
        {"correct": "E"},
    ],
)
def test_an_invalid_row_is_a_row_error(overrides: dict[str, object]) -> None:
    with pytest.raises(RowError):
        QUIZ.parse_row(fila(**overrides))


def test_the_kind_is_resolved_by_code() -> None:
    assert get_content_kind("quiz") is QUIZ
    with pytest.raises(ValueError, match="rosco"):
        get_content_kind("rosco")


def test_the_cli_rejects_an_unknown_kind() -> None:
    with pytest.raises(SystemExit):
        _build_parser().parse_args(
            ["import-content", "--kind", "rosco", "preguntas.csv"]
        )


# --- payloads versionados ----------------------------------------------------


def test_a_payload_with_another_version_is_rejected() -> None:
    with pytest.raises(ValidationError):
        QuizPayload.model_validate(
            {"v": 2, "prompt": "¿?", "options": ["a", "b", "c", "d"]}
        )


def test_a_solution_outside_the_options_is_rejected() -> None:
    with pytest.raises(ValidationError):
        QuizSolution(correct_index=4)


def test_media_without_a_url_is_rejected() -> None:
    with pytest.raises(ValidationError):
        QuizPayload(
            prompt="¿?",
            options=["a", "b", "c", "d"],
            media={"type": "image", "url": None},
        )


def test_a_difficulty_range_inverted_is_rejected() -> None:
    with pytest.raises(ValidationError):
        QuizCandidatesConfig(low=5, high=2)


# --- candidatas y carga ------------------------------------------------------


async def test_candidates_are_published_quiz_items_in_the_range(
    session: AsyncSession,
) -> None:
    facil = content_item(difficulty=1, status="published")
    dificil = content_item(difficulty=5, status="published")
    borrador = content_item(difficulty=1, status="draft")
    otro_kind = content_item(kind="rosco", difficulty=1, status="published")
    await acepta(session, facil, dificil, borrador, otro_kind)

    todas = await QUIZ.candidates(session, config=QuizCandidatesConfig())
    tramo = await QUIZ.candidates(session, config=QuizCandidatesConfig(low=2, high=4))

    assert {ref.content_id for ref in todas} == {str(facil.id), str(dificil.id)}
    assert tramo == []
    assert todas[0].difficulty in (1, 5)


async def test_load_returns_the_public_item_and_the_solution(
    session: AsyncSession,
) -> None:
    item = content_item(
        payload={
            "v": 1,
            "prompt": "¿Cuál es el río más largo?",
            "options": ["Paraná", "Amazonas", "Orinoco", "Magdalena"],
            "media": {"type": "none", "url": None},
        }
    )
    solucion = content_solution(item.id, payload={"v": 1, "correct_index": 1})
    await acepta(session, item, solucion)

    cargado = await QUIZ.load(session, ItemRef(str(item.id), item.difficulty))

    assert cargado.content_id == str(item.id)
    assert cargado.public.payload["prompt"] == "¿Cuál es el río más largo?"
    assert "correct_index" not in cargado.public.payload
    assert cargado.solution.payload["correct_index"] == 1


async def test_load_rejects_a_missing_item_a_foreign_kind_and_a_missing_solution(
    session: AsyncSession,
) -> None:
    rosco = content_item(kind="rosco")
    sin_solucion = content_item()
    await acepta(session, rosco, sin_solucion)

    with pytest.raises(KeyError):
        await QUIZ.load(session, ItemRef(str(uuid.uuid4()), 2))
    with pytest.raises(KeyError):
        await QUIZ.load(session, ItemRef(str(rosco.id), 2))
    with pytest.raises(KeyError, match="solución"):
        await QUIZ.load(session, ItemRef(str(sin_solucion.id), 2))
