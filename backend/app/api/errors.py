"""El formato de error que promete el plan: `{"error": {"code", "message"}}`.

Los errores con código propio pasan por acá. El 422 de validación de FastAPI
también, porque si no el cliente tendría que entender dos formatos distintos con
el mismo `status_code`. El 404 de ruta desconocida sigue siendo de FastAPI: la
app nunca pega a una ruta que no existe.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """Error con `status_code` de HTTP y código de negocio."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        detalle = "; ".join(error["msg"] for error in exc.errors())
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": detalle or "Pedido inválido.",
                }
            },
        )
