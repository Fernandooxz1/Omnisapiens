"""Guardia de fuga: la solución no puede viajar antes de la revelación.

No alcanza con que el dataclass no declare `correct_index`: el test recorre los
mensajes reales de los tres escenarios y falla si aparece una clave prohibida o
el texto de la respuesta fuera del arreglo de opciones.
"""

from typing import Any, cast

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ContentItem, ContentSolution

from . import ws_fixtures
from .ws_scenarios import ESCENARIOS, es_revelacion

arcade_api = ws_fixtures.arcade_api
arcade_connect = ws_fixtures.arcade_connect
session_api = ws_fixtures.session_api
session_connect = ws_fixtures.session_connect
room_api = ws_fixtures.room_api
room_connect = ws_fixtures.room_connect
abrir = ws_fixtures.abrir

# `correct_count` es un contador legítimo de la partida; el resto de las claves
# con `correct`, `answer` o `solution` solo existen en el resultado.
CLAVES_PROHIBIDAS = {"is_correct"}


def _es_prohibida(nombre: str) -> bool:
    if nombre == "correct_count":
        return False
    return nombre in CLAVES_PROHIBIDAS or nombre.startswith(
        ("answer", "correct", "solution")
    )


def _claves(value: Any) -> list[str]:
    if isinstance(value, dict):
        encontradas: list[str] = []
        for nombre, item in value.items():
            if _es_prohibida(nombre):
                encontradas.append(nombre)
            encontradas.extend(_claves(item))
        return encontradas
    if isinstance(value, list):
        return [clave for item in value for clave in _claves(item)]
    return []


def _textos(value: Any, *, dentro_de_opciones: bool = False) -> list[str]:
    if isinstance(value, dict):
        return [
            texto
            for nombre, item in value.items()
            for texto in _textos(
                item, dentro_de_opciones=dentro_de_opciones or nombre == "options"
            )
        ]
    if isinstance(value, list):
        return [
            texto
            for item in value
            for texto in _textos(item, dentro_de_opciones=dentro_de_opciones)
        ]
    if isinstance(value, str) and not dentro_de_opciones:
        return [value]
    return []


def _assert_publico(message: dict[str, Any], soluciones: set[str]) -> None:
    if es_revelacion(message):
        return

    filtradas = set(_claves(message))
    if filtradas:
        raise AssertionError(
            f"{message['t']} filtra {sorted(filtradas)} antes de la revelación"
        )

    expuestas = soluciones.intersection(_textos(message))
    if expuestas:
        raise AssertionError(
            f"{message['t']} expone la respuesta "
            f"{sorted(expuestas)} antes del resultado"
        )


async def _soluciones(session: AsyncSession) -> set[str]:
    items = (await session.scalars(select(ContentItem))).all()
    soluciones: set[str] = set()
    for item in items:
        solucion = await session.get(ContentSolution, item.id)
        if solucion is None:
            continue
        opciones = cast("list[str]", item.payload["options"])
        indice = cast(int, solucion.payload["correct_index"])
        soluciones.add(opciones[indice])
    return soluciones


def _revisar(transcript: Any, soluciones: set[str]) -> None:
    for message in transcript.lines():
        _assert_publico(message, soluciones)


async def test_the_arcade_messages_do_not_leak_before_the_result(
    arcade_api: Any, arcade_connect: Any
) -> None:
    transcript = await ESCENARIOS["arcade_complete"](arcade_api, arcade_connect)
    _revisar(transcript, await _soluciones(arcade_api.session))


async def test_the_canonical_messages_do_not_leak_before_the_result(
    session_api: Any, session_connect: Any
) -> None:
    transcript = await ESCENARIOS["session_complete"](session_api, session_connect)
    _revisar(transcript, await _soluciones(session_api.session))


async def test_the_versus_messages_do_not_leak_before_the_result(
    room_api: Any, room_connect: Any
) -> None:
    transcript = await ESCENARIOS["versus_complete"](room_api, room_connect)
    _revisar(transcript, await _soluciones(room_api.session))


async def test_the_reconnect_messages_do_not_leak_before_the_result(
    room_api: Any, room_connect: Any
) -> None:
    transcript = await ESCENARIOS["versus_reconnect"](room_api, room_connect)
    _revisar(transcript, await _soluciones(room_api.session))


def test_the_guard_rejects_a_correct_index_in_a_round_start() -> None:
    with pytest.raises(AssertionError, match="correct_index"):
        _assert_publico({"t": "round_start", "d": {"correct_index": 1}}, set())


def test_the_guard_rejects_the_solution_outside_the_options() -> None:
    ronda = {
        "t": "round_start",
        "d": {"prompt": "Amazonas", "options": ["Amazonas", "Paraná"]},
    }
    with pytest.raises(AssertionError, match="Amazonas"):
        _assert_publico(ronda, {"Amazonas"})


def test_the_guard_accepts_the_solution_inside_the_options() -> None:
    ronda = {
        "t": "round_start",
        "d": {
            "prompt": "¿Cuál es el río más largo?",
            "options": ["Amazonas", "Paraná"],
        },
    }
    _assert_publico(ronda, {"Amazonas"})


def test_the_guard_accepts_the_solution_in_the_reveal() -> None:
    resultado = {
        "t": "round_result",
        "d": {"correct_index": 0, "you": {"correct": True}},
    }
    _assert_publico(resultado, {"Amazonas"})
