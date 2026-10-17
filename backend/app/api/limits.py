"""Límite de tamaño del cuerpo HTTP (H-15).

Un cuerpo de 10 MB se parsea antes de que ningún validador lo mire, así que el
tope tiene que estar en la puerta. Sin `Content-Length` (chunked) no se puede
decidir sin leer; ahí el límite queda del lado de uvicorn/proxy.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

MAX_BODY_BYTES = 1_000_000


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        declarado = request.headers.get("content-length")
        if declarado is not None:
            try:
                tamano = int(declarado)
            except ValueError:
                tamano = 0
            if tamano > MAX_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": {
                            "code": "PAYLOAD_TOO_LARGE",
                            "message": "El cuerpo del pedido es demasiado grande.",
                        }
                    },
                )
        return await call_next(request)
