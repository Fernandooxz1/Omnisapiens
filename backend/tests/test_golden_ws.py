"""Congela el protocolo WebSocket actual en transcripts normalizados.

Cada escenario se reproduce contra la app real y se compara línea por línea con
el JSONL de `tests/golden/`. Para regenerarlos (después de un cambio deliberado):

    UPDATE_GOLDEN=1 uv run pytest tests/test_golden_ws.py

Los ids, el código de sala y los `ends_at` se reemplazan por placeholders: el
golden cuida el orden y el contenido, no los valores que cambian en cada partida.
"""

import json
import os
from difflib import unified_diff
from pathlib import Path
from typing import Any

import pytest

from . import ws_fixtures
from .ws_scenarios import ESCENARIOS, Transcript

arcade_api = ws_fixtures.arcade_api
arcade_connect = ws_fixtures.arcade_connect
room_api = ws_fixtures.room_api
room_connect = ws_fixtures.room_connect
abrir = ws_fixtures.abrir

GOLDEN = Path(__file__).parent / "golden"
ACTUALIZAR = os.environ.get("UPDATE_GOLDEN") == "1"


def _comparar(nombre: str, transcript: Transcript) -> None:
    esperado_path = GOLDEN / f"{nombre}.jsonl"
    actual = "".join(
        json.dumps(line, ensure_ascii=False, sort_keys=True) + "\n"
        for line in transcript.lines()
    )

    if ACTUALIZAR:
        GOLDEN.mkdir(exist_ok=True)
        esperado_path.write_text(actual, encoding="utf-8")

    esperado = esperado_path.read_text(encoding="utf-8")
    if actual == esperado:
        return

    diff = "\n".join(
        unified_diff(
            esperado.splitlines(),
            actual.splitlines(),
            fromfile=f"golden/{nombre}.jsonl",
            tofile="recibido",
            lineterm="",
        )
    )
    pytest.fail(f"el transcript {nombre} cambió:\n{diff}")


async def test_the_arcade_transcript_is_frozen(
    arcade_api: Any, arcade_connect: Any
) -> None:
    _comparar(
        "arcade_complete",
        await ESCENARIOS["arcade_complete"](arcade_api, arcade_connect),
    )


async def test_the_versus_transcript_is_frozen(
    room_api: Any, room_connect: Any
) -> None:
    _comparar(
        "versus_complete", await ESCENARIOS["versus_complete"](room_api, room_connect)
    )


async def test_the_reconnect_transcript_is_frozen(
    room_api: Any, room_connect: Any
) -> None:
    _comparar(
        "versus_reconnect", await ESCENARIOS["versus_reconnect"](room_api, room_connect)
    )
