"""El catálogo de modos disponibles.

El registro es la única lista de modos: `GET /modes`, la creación de sesiones y
el ranking leen de acá. Importar este módulo no registra nada; los modos se
registran explícitamente desde `app.game.modes` en la fase 6.
"""

from app.game.modes.base import GameMode


class ModeRegistry:
    """Un registro por código. La instancia global es la del proceso."""

    def __init__(self) -> None:
        self._modes: dict[str, GameMode] = {}

    def register(self, mode: GameMode) -> GameMode:
        if mode.code in self._modes:
            raise ValueError(f"modo duplicado: {mode.code}")
        self._modes[mode.code] = mode
        return mode

    def get(self, code: str) -> GameMode:
        try:
            return self._modes[code]
        except KeyError:
            raise KeyError(f"modo desconocido: {code}") from None

    def all(self) -> tuple[GameMode, ...]:
        return tuple(self._modes.values())


registry = ModeRegistry()


def register(mode: GameMode) -> GameMode:
    return registry.register(mode)


def get(code: str) -> GameMode:
    return registry.get(code)


def all() -> tuple[GameMode, ...]:
    return registry.all()


__all__ = ["ModeRegistry", "all", "get", "register", "registry"]
