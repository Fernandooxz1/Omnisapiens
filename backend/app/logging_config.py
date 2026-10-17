"""Logging de la API: una sola configuración y el pase fuera de los logs.

uvicorn loguea el handshake de un WebSocket con la URL completa (`uvicorn.error`),
y el token viaja en el query string porque el navegador no deja mandar headers en
`new WebSocket` (H-08). Sin filtro, cada conexión escribe un JWT válido 30 días en
el log. El filtro descarta **solo** esos renglones: el resto de `uvicorn.error`
(arranque, errores) sigue visible.
"""

import logging

from app.config import settings

FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


class _HideWebSocketTokens(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not isinstance(record.args, tuple):
            return True
        return not any(
            isinstance(arg, str) and (arg.startswith("/ws/") or "?token=" in arg)
            for arg in record.args
        )


def configure_logging() -> None:
    logging.basicConfig(level=settings.log_level, format=FORMAT)
    filtro = _HideWebSocketTokens()
    for nombre in ("uvicorn.access", "uvicorn.error"):
        logging.getLogger(nombre).addFilter(filtro)
