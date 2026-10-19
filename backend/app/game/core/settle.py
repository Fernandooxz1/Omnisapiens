"""La ventana temporal de una submission, compartida por todos los modos.

El modo aporta el `grade`: qué significa acertar para su contenido. Acá viven
las reglas que no cambian con el formato: una submission fuera de la ventana no
existe y el intento se mide desde el momento en que el ítem se sirvió.
"""

from collections.abc import Callable

from app.game.core.items import RejectReason, ServedItem, Submission, Verdict


def settle[DetailT](
    served: ServedItem,
    submission: Submission | None,
    *,
    now_ms: int,
    grade: Callable[[Submission], tuple[bool, DetailT | None]],
) -> Verdict[DetailT]:
    """Juzga la submission si cayó dentro de la ventana; si no, la descarta.

    `submission=None` es una omisión, no un rechazo: consume la ventana entera,
    igual que hoy. Una submission fuera de los bordes tampoco se juzga: el
    `grade` no llega a verla y el veredicto queda marcado como rechazado.
    """
    if submission is None:
        return Verdict(correct=False, elapsed_ms=served.window_ms)

    if not served.served_at_ms <= now_ms <= served.deadline:
        return Verdict(
            correct=False,
            elapsed_ms=served.window_ms,
            rejected=RejectReason.OUTSIDE_WINDOW,
        )

    correct, detail = grade(submission)
    return Verdict(
        correct=correct,
        elapsed_ms=now_ms - served.served_at_ms,
        detail=detail,
    )
