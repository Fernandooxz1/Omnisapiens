"""Las reglas de una ronda de quiz.

`serve` fija la ventana y retiene la solución del ítem; `grade` la consulta y
delega la ventana en `core.settle`. El contrato de §3.3 no transporta la
solución hasta `grade`, así que la única forma de que el modo juzgue sin
cambiarlo es guardarla cuando se sirve. El mapa está acotado por el banco de
contenido y se indexa por el `item_key` que ya viaja en `ServedItem`.
"""

from dataclasses import dataclass, field
from random import Random

from app.game.core import ChoiceSubmission, ServedItem, Submission, Verdict, settle
from app.game.errors import InvalidTransition
from app.game.modes.base import LoadedItem
from app.game.modes.quiz.models import QuizSolution


@dataclass
class QuizRules:
    """Sirve y juzga una ronda de cuatro opciones."""

    _solutions: dict[str, QuizSolution] = field(
        default_factory=dict, repr=False, compare=False
    )

    def serve(
        self,
        item: LoadedItem,
        *,
        difficulty: int,
        seconds: int,
        now_ms: int,
        rng: Random,
    ) -> ServedItem:
        """Abre la ventana y deja la solución lista para `grade`."""
        # El barajado de opciones es del borde, no de la ventana.
        self._solutions[item.content_id] = QuizSolution.model_validate(
            dict(item.solution.payload)
        )
        return ServedItem(
            item_key=item.content_id,
            difficulty=difficulty,
            seconds=seconds,
            served_at_ms=now_ms,
            deadline=now_ms + seconds * 1000,
        )

    def grade(
        self, served: ServedItem, submission: Submission, *, now_ms: int
    ) -> Verdict[None]:
        """Compara la opción elegida con la solución del ítem servido."""
        solution = self._solutions.get(served.item_key)
        if solution is None:
            raise InvalidTransition(
                f"el ítem {served.item_key!r} no fue servido por estas reglas"
            )

        def grade_choice(choice: Submission) -> tuple[bool, None]:
            if not isinstance(choice, ChoiceSubmission):
                return False, None
            return choice.index == solution.correct_index, None

        return settle(served, submission, now_ms=now_ms, grade=grade_choice)


__all__ = ["QuizRules"]
