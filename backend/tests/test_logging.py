"""El filtro que saca el token del log (H-08)."""

import logging

from app.logging_config import _HideWebSocketTokens

FILTRO = _HideWebSocketTokens()


def _registro(mensaje: str, *args: object) -> logging.LogRecord:
    return logging.LogRecord(
        "uvicorn.error", logging.INFO, __file__, 1, mensaje, args, None
    )


def test_the_websocket_handshake_is_dropped() -> None:
    # uvicorn.error loguea path + query, y el token viaja ahí.
    registro = _registro(
        '%s - "WebSocket %s" [accepted]',
        ("127.0.0.1", 1234),
        "/ws/room/K7M2QP?token=eyJhbGciOi.secreto",
    )

    assert FILTRO.filter(registro) is False


def test_a_query_with_token_is_dropped_even_if_the_path_is_not_ws() -> None:
    registro = _registro("conexión a %s", "/algo?token=secreto")

    assert FILTRO.filter(registro) is False


def test_the_rest_of_uvicorn_stays_visible() -> None:
    arranque = _registro("Application startup complete.")
    acceso = _registro(
        '%s - "%s %s HTTP/%s" %d',
        "127.0.0.1",
        "GET",
        "/health",
        "1.1",
        200,
    )
    error = _registro("Exception in ASGI application\n%s", "traceback")

    assert FILTRO.filter(arranque) is True
    assert FILTRO.filter(acceso) is True
    assert FILTRO.filter(error) is True
