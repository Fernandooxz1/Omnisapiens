"""El panel de preguntas. Todo `/admin` pide `X-Admin-Token`, ruta por ruta.

La dependencia va en el router y no en cada endpoint: se agrega una ruta nueva y
nace protegida, en vez de depender de que alguien se acuerde de repetir el
`Depends`.
"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from app.api.deps import SessionDep, require_admin
from app.api.errors import ApiError
from app.game.constants import CATEGORIES, DIFFICULTY_MAX, DIFFICULTY_MIN
from app.models.question import PROMPT_MAX_LENGTH
from app.schemas.admin import (
    AdminQuestionOut,
    AdminQuestionPage,
    ImportReportOut,
    QuestionStatus,
    RejectedRowOut,
)
from app.services import importer, question_admin

MAX_PAGE_SIZE = 100

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


@router.get("/questions")
async def list_questions(
    session: SessionDep,
    status: QuestionStatus | None = None,
    category: str | None = None,
    difficulty: Annotated[
        int | None, Query(ge=DIFFICULTY_MIN, le=DIFFICULTY_MAX)
    ] = None,
    q: Annotated[str | None, Query(max_length=PROMPT_MAX_LENGTH)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 20,
) -> AdminQuestionPage:
    # `status` y `difficulty` los valida FastAPI con el enum y el rango. Las
    # categorías viven en una tupla del dominio, así que se validan acá para no
    # duplicar la lista en un `Literal` que se desincronice.
    if category is not None and category not in CATEGORIES:
        raise ApiError(422, "VALIDATION_ERROR", f"categoría desconocida: {category!r}")

    resultado = await question_admin.list_questions(
        session,
        status=status.value if status is not None else None,
        category=category,
        difficulty=difficulty,
        # Un buscador vacío o de espacios es "sin filtro", no "enunciado en blanco".
        q=q.strip() if q is not None else None,
        page=page,
        page_size=page_size,
    )
    total = resultado.total
    return AdminQuestionPage(
        items=[
            AdminQuestionOut.model_validate(pregunta) for pregunta in resultado.items
        ],
        page=page,
        page_size=page_size,
        total=total,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/questions/import")
async def import_questions(
    session: SessionDep,
    file: Annotated[UploadFile, File()],
    # Form y no query: el archivo y sus opciones viajan en el mismo pedido.
    status: Annotated[QuestionStatus, Form()] = QuestionStatus.DRAFT,
) -> ImportReportOut:
    # El límite de 1 MB del middleware ya cortó lo grande; acá el archivo entero
    # tiene que entrar en memoria para parsearlo, igual que en la CLI.
    contenido = await file.read()
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Sin este caso, un archivo en latin-1 salía como 500 y no decía por qué.
        raise ApiError(
            400, "IMPORT_FORMAT", "El archivo no está codificado en UTF-8."
        ) from None

    try:
        formato = importer.detect_format(Path(file.filename or ""))
        filas = importer.parse_text(texto, fmt=formato)
    except importer.ImportFormatError as exc:
        # Errores de formato (encabezado, JSON roto, extensión) son 400 con el
        # motivo tal cual: es lo que necesita quien está subiendo el archivo.
        raise ApiError(400, "IMPORT_FORMAT", str(exc)) from None

    reporte = await importer.import_rows(session, filas, status=status.value)
    # El endpoint que escribe commitea él: la respuesta no puede salir antes de
    # que las filas estén guardadas.
    await session.commit()
    return ImportReportOut(
        total=reporte.total,
        imported=reporte.imported,
        duplicated=reporte.duplicated,
        rejected=[
            RejectedRowOut(row=fila.row, reason=fila.reason)
            for fila in reporte.rejected
        ],
    )
