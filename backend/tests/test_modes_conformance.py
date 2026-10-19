"""La suite de conformidad que todo modo registrado tiene que pasar.

El registro todavía está vacío: la parametrización no recolecta casos. Las
funciones de aserción quedan listas para que la fase 6 las corra contra
`trivia_arcade` y `trivia_versus`.
"""

from collections.abc import Callable, Mapping

import pytest
from pydantic import BaseModel

from app.game.core import RejectReason, ServedItem, Submission, settle
from app.game.modes import registry
from app.game.modes.base import GameMode, RoundRules

# `correct_count` es un contador legítimo; el resto solo vive en la solución.
CLAVES_PROHIBIDAS = {"explanation", "is_correct"}
PREFIJOS_PROHIBIDOS = ("answer", "correct", "solution")
CLAVES_PERMITIDAS = {"correct_count"}


def _claves_filtradas(value: object) -> list[str]:
    if isinstance(value, Mapping):
        encontradas: list[str] = []
        for nombre, item in value.items():
            if (
                isinstance(nombre, str)
                and nombre not in CLAVES_PERMITIDAS
                and (
                    nombre in CLAVES_PROHIBIDAS
                    or nombre.startswith(PREFIJOS_PROHIBIDOS)
                )
            ):
                encontradas.append(nombre)
            encontradas.extend(_claves_filtradas(item))
        return encontradas
    if isinstance(value, (list, tuple)):
        return [clave for item in value for clave in _claves_filtradas(item)]
    return []


def assert_public_payload(payload: object) -> None:
    """El payload público no puede nombrar la solución de ninguna forma."""
    filtradas = _claves_filtradas(payload)
    assert not filtradas, f"el payload público filtra {sorted(set(filtradas))}"


def assert_deterministic(build: Callable[[], object]) -> None:
    """El mismo estado y la misma semilla tienen que dar el mismo resultado."""
    assert build() == build(), "el modo no es determinista"


def assert_window(
    rules: RoundRules, served: ServedItem, submission: Submission
) -> None:
    """Los dos bordes valen y todo lo de afuera no existe."""
    before = rules.grade(served, submission, now_ms=served.served_at_ms - 1)
    inside = rules.grade(served, submission, now_ms=served.served_at_ms)
    after = rules.grade(served, submission, now_ms=served.deadline + 1)

    assert before.rejected is RejectReason.OUTSIDE_WINDOW, (
        "la submission antes del borde no fue rechazada"
    )
    assert inside.rejected is None, "el borde inferior rechazó una submission válida"
    assert after.rejected is RejectReason.OUTSIDE_WINDOW, (
        "la submission después del deadline no fue rechazada"
    )


def assert_non_negative_points(points: int) -> None:
    assert points >= 0, f"puntos negativos: {points}"


MODES = registry.all()


@pytest.mark.parametrize("mode", MODES, ids=lambda mode: mode.code)
def test_every_mode_declares_a_complete_contract(mode: GameMode) -> None:
    assert mode.code
    assert mode.content.code == mode.content_kind
    assert mode.ruleset_version >= 1
    assert issubclass(mode.config_schema, BaseModel)
    assert issubclass(mode.public_schema, BaseModel)
    assert mode.players in {"solo", "versus"}


class _ChoiceRules:
    """Las reglas mínimas que necesita `assert_window` para probarse sola."""

    def grade(
        self, served: ServedItem, submission: Submission, *, now_ms: int
    ) -> object:
        from app.game.core import ChoiceSubmission

        def grade_choice(choice: Submission) -> tuple[bool, None]:
            assert isinstance(choice, ChoiceSubmission)
            return choice.index == 1, None

        return settle(served, submission, now_ms=now_ms, grade=grade_choice)


def _served() -> ServedItem:
    return ServedItem(
        item_key="q-1",
        difficulty=1,
        seconds=10,
        served_at_ms=1_000,
        deadline=11_000,
    )


def test_the_guard_rejects_a_solution_in_the_payload() -> None:
    with pytest.raises(AssertionError, match="correct_index"):
        assert_public_payload({"prompt": "¿?", "correct_index": 1})


def test_the_guard_rejects_an_explanation_in_the_payload() -> None:
    with pytest.raises(AssertionError, match="explanation"):
        assert_public_payload({"prompt": "¿?", "explanation": "porque sí"})


def test_the_guard_accepts_a_public_payload() -> None:
    assert_public_payload(
        {"prompt": "¿Cuál es el río más largo?", "options": ["Amazonas", "Paraná"]}
    )


def test_the_guard_accepts_the_correct_count() -> None:
    assert_public_payload({"correct_count": 3, "score": 400})


def test_determinism_compares_two_builds() -> None:
    assert_deterministic(lambda: {"options": ["a", "b"], "index": 1})
    valores = iter([1, 2])
    with pytest.raises(AssertionError, match="determinista"):
        assert_deterministic(lambda: next(valores))


def test_the_window_guard_rejects_an_outside_answer() -> None:
    from app.game.core import ChoiceSubmission

    rules = _ChoiceRules()
    served = _served()
    submission = ChoiceSubmission(1)

    assert_window(rules, served, submission)  # type: ignore[arg-type]


def test_the_window_guard_detects_a_ruleset_that_ignores_the_window() -> None:
    class _AlwaysCorrect:
        def grade(
            self, served: ServedItem, submission: Submission, *, now_ms: int
        ) -> object:
            from app.game.core import Verdict

            return Verdict(correct=True, elapsed_ms=0)

    with pytest.raises(AssertionError, match="no fue rechazada"):
        assert_window(_AlwaysCorrect(), _served(), submission=object())  # type: ignore[arg-type]


def test_points_may_be_zero_but_not_negative() -> None:
    assert_non_negative_points(0)
    with pytest.raises(AssertionError, match="negativos"):
        assert_non_negative_points(-1)
