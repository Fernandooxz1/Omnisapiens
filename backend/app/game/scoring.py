from app.game.constants import (
    ARCADE_STREAK_BONUS_MAX,
    ARCADE_STREAK_BONUS_STEP,
    BASE_POINTS,
    TIME_BONUS_MAX,
)


def round_points(*, correct: bool, elapsed_ms: int, total_seconds: int) -> int:
    """Puntos de una ronda puntuada.

    Aritmética entera a propósito: round() de Python redondea al par y los
    floats derivan (1 - 19000/20000 no es exactamente 0.05). Acá el bonus se
    calcula con división entera y redondeo half-up, que es el mismo resultado
    en cualquier lenguaje.
    """
    if total_seconds <= 0:
        raise ValueError(f"total_seconds debe ser positivo: {total_seconds}")
    if elapsed_ms < 0:
        raise ValueError(f"elapsed_ms no puede ser negativo: {elapsed_ms}")
    if elapsed_ms > total_seconds * 1000:
        raise ValueError("respuesta fuera de la ventana: se descarta antes de puntuar")

    if not correct:
        return 0

    limit_ms = total_seconds * 1000
    remaining_ms = limit_ms - elapsed_ms
    bonus = (TIME_BONUS_MAX * remaining_ms + limit_ms // 2) // limit_ms
    return BASE_POINTS + bonus


def streak_bonus(streak: int) -> int:
    """streak = aciertos consecutivos *antes* de esta pregunta."""
    if streak < 0:
        raise ValueError(f"streak no puede ser negativo: {streak}")

    return min(ARCADE_STREAK_BONUS_STEP * streak, ARCADE_STREAK_BONUS_MAX)


def arcade_points(
    *, correct: bool, elapsed_ms: int, total_seconds: int, streak: int
) -> int:
    if not correct:
        return 0

    return round_points(
        correct=True, elapsed_ms=elapsed_ms, total_seconds=total_seconds
    ) + streak_bonus(streak)
