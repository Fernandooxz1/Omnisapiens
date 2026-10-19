"""El panel de contenido. Todo `/admin` pide `X-Admin-Token`, ruta por ruta.

La dependencia va en el router y no en cada endpoint: se agrega una ruta nueva y
nace protegida, en vez de depender de que alguien se acuerde de repetir el
`Depends`.

`/admin/content/{kind}` es la ruta nueva; `/admin/questions` y su `/import` son
el alias de compatibilidad del quiz (`/admin/content/quiz`). Las dos escriben
siempre en las tablas genéricas; desde 2.4 la tabla vieja `questions` queda de
solo lectura hasta la fase 10.
"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SessionDep, require_admin
from app.api.errors import ApiError
from app.game.constants import CATEGORIES, DIFFICULTY_MAX, DIFFICULTY_MIN
from app.game.modes.quiz import QUIZ, QuizContent, get_content_kind
from app.models.question import PROMPT_MAX_LENGTH
from app.schemas.admin import (
    AdminQuestionPage,
    ImportReportOut,
    QuestionStatus,
    RejectedRowOut,
    admin_question,
)
from app.services import importer, question_admin

MAX_PAGE_SIZE = 100

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


def _content_kind(code: str) -> QuizContent:
    try:
        return get_content_kind(code)
    except ValueError as exc:
        # Mismo código que una categoría desconocida: el path trae un valor que
        # el servidor no conoce y el motivo viaja en el mensaje.
        raise ApiError(422, "VALIDATION_ERROR", str(exc)) from None


async def _list_content(
    session: AsyncSession,
    *,
    kind: str,
    status: QuestionStatus | None,
    category: str | None,
    difficulty: int | None,
    q: str | None,
    page: int,
    page_size: int,
) -> AdminQuestionPage:
    _content_kind(kind)
    # `status` y `difficulty` los valida FastAPI con el enum y el rango. Las
    # categorías viven en una tupla del dominio, así que se validan acá para no
    # duplicar la lista en un `Literal` que se desincronice.
    if category is not None and category not in CATEGORIES:
        raise ApiError(422, "VALIDATION_ERROR", f"categoría desconocida: {category!r}")

    resultado = await question_admin.list_content(
        session,
        kind=kind,
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
        items=[admin_question(fila.item, fila.solution) for fila in resultado.items],
        page=page,
        page_size=page_size,
        total=total,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/content/{kind}")
async def list_content(
    kind: str,
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
    return await _list_content(
        session,
        kind=kind,
        status=status,
        category=category,
        difficulty=difficulty,
        q=q,
        page=page,
        page_size=page_size,
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
    """Alias de `/admin/content/quiz` con la forma histórica del panel."""
    return await _list_content(
        session,
        kind=QUIZ.code,
        status=status,
        category=category,
        difficulty=difficulty,
        q=q,
        page=page,
        page_size=page_size,
    )


async def _import_content(
    session: AsyncSession,
    *,
    kind: str,
    file: UploadFile,
    status: QuestionStatus,
) -> ImportReportOut:
    content = _content_kind(kind)
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

    reporte = await importer.import_rows(
        session, filas, kind=content, status=status.value
    )
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


@router.post("/content/{kind}")
@router.post("/content/{kind}/import", include_in_schema=False)
async def import_content(
    kind: str,
    session: SessionDep,
    file: Annotated[UploadFile, File()],
    # Form y no query: el archivo y sus opciones viajan en el mismo pedido.
    status: Annotated[QuestionStatus, Form()] = QuestionStatus.DRAFT,
) -> ImportReportOut:
    return await _import_content(session, kind=kind, file=file, status=status)


@router.post("/questions/import")
async def import_questions(
    session: SessionDep,
    file: Annotated[UploadFile, File()],
    status: Annotated[QuestionStatus, Form()] = QuestionStatus.DRAFT,
) -> ImportReportOut:
    """Alias histórico de `/admin/content/quiz`."""
    return await _import_content(session, kind=QUIZ.code, file=file, status=status)
