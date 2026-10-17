"""Ayudantes para los `CHECK`, que casi siempre terminan listando valores permitidos."""

from collections.abc import Iterable


def quoted_list(values: Iterable[object]) -> str:
    """`'a', 'b'` — para columnas de texto, o para comparar contra texto."""
    return ", ".join(f"'{value}'" for value in values)


def number_list(values: Iterable[int]) -> str:
    """`0, 1, 2` — sin comillas, para columnas numéricas."""
    return ", ".join(str(value) for value in values)
