"""Cargar contenido desde un archivo: CSV o JSON con las mismas claves.

El parseo del archivo vive acá; la validación de una fila y la forma del payload
viven en el `ContentKind` (`app.game.modes.quiz`). El importador escribe siempre
en `content_items`/`content_solutions` y, mientras dure el refactor, también en
`questions` (dual-write) para que el juego siga leyendo la tabla vieja hasta 2.4.

El `content_hash` sale del `fingerprint` del kind, así que una importación nueva
y un backfill no pueden duplicar la misma pregunta.
"""

import csv
import io
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.game.modes.base import ContentDraft, ContentKind
from app.game.modes.quiz import QUIZ
from app.game.modes.quiz.content import (
    COLUMNS,
    CORRECT_LETTERS,
    OPTION_KEYS,
    REQUIRED,
    RowError,
    content_hash,
    normalize_prompt,
)
from app.models import ContentItem, ContentSolution, Question
from app.models.content import STATUSES as CONTENT_STATUSES

__all__ = [
    "COLUMNS",
    "CORRECT_LETTERS",
    "INSERT_BATCH",
    "OPTION_KEYS",
    "REQUIRED",
    "ImportFormatError",
    "ImportReport",
    "ParsedRow",
    "RawRow",
    "RejectedRow",
    "RowError",
    "content_hash",
    "detect_format",
    "import_file",
    "import_rows",
    "normalize_prompt",
    "parse_csv",
    "parse_json",
    "parse_text",
    "read_file",
    "validate_row",
]


class ImportFormatError(Exception):
    """El archivo entero no se puede leer (no es una fila mala: es el formato)."""


@dataclass(frozen=True)
class RawRow:
    """Una fila cruda, todavía sin validar. `position` es la línea del CSV (el
    encabezado es la 1) o el índice dentro del array de JSON (desde 1)."""

    position: int
    values: dict[str, Any]


@dataclass(frozen=True)
class ParsedRow:
    """Una fila ya validada, en la forma que espera la tabla vieja.

    La usa el dual-write a `questions`; el contenido genérico sale del
    `ContentDraft` que devuelve el `ContentKind`.
    """

    category: str
    difficulty: int
    prompt: str
    options: list[str]
    correct_index: int
    explanation: str | None
    source: str | None
    tags: list[str]
    content_hash: str


@dataclass(frozen=True)
class _ValidRow:
    """Una fila lista para las dos tablas: mismo UUID en ambas."""

    id: uuid.UUID
    legacy: ParsedRow
    draft: ContentDraft


@dataclass(frozen=True)
class RejectedRow:
    row: int
    reason: str


@dataclass(frozen=True)
class ImportReport:
    imported: int
    duplicated: int
    rejected: list[RejectedRow] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.imported + self.duplicated + len(self.rejected)


def validate_row(values: dict[str, Any]) -> ParsedRow:
    """Valida una fila con el `ContentKind` y la completa con los campos legacy.

    `source` y `tags` no existen en el contenido genérico: son de la tabla vieja
    y solo viven mientras dure el dual-write.
    """
    draft = QUIZ.parse_row(values)
    return _legacy_row(values, draft, fingerprint=QUIZ.fingerprint(draft))


def _text(raw: Any) -> str:
    return "" if raw is None else str(raw).strip()


def _tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(t).strip() for t in raw if str(t).strip()]
    if isinstance(raw, str):
        return [t.strip() for t in raw.split(";") if t.strip()]
    raise RowError("las etiquetas deben ser texto separado por `;` o una lista")


def parse_csv(text: str) -> list[RawRow]:
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ImportFormatError("el CSV está vacío: falta el encabezado")
    encabezado = {campo.strip() for campo in reader.fieldnames}
    # Se lee por nombre, así el orden del encabezado no importa; el conjunto sí:
    # una columna de más o de menos es un archivo que no es el que espera el plan.
    if encabezado != set(COLUMNS):
        faltan = sorted(set(COLUMNS) - encabezado)
        sobran = sorted(encabezado - set(COLUMNS))
        partes = []
        if faltan:
            partes.append(f"faltan {', '.join(faltan)}")
        if sobran:
            partes.append(f"sobran {', '.join(sobran)}")
        raise ImportFormatError(f"encabezado inesperado: {'; '.join(partes)}")
    return [RawRow(reader.line_num, dict(fila)) for fila in reader]


def parse_json(text: str) -> list[RawRow]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ImportFormatError(f"JSON inválido: {exc.msg}") from exc
    if not isinstance(data, list):
        raise ImportFormatError("se espera un array de objetos")
    filas = []
    for indice, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ImportFormatError(f"el elemento {indice} no es un objeto")
        filas.append(RawRow(indice, item))
    return filas


def detect_format(path: Path) -> str:
    sufijo = path.suffix.lower()
    if sufijo == ".csv":
        return "csv"
    if sufijo == ".json":
        return "json"
    raise ImportFormatError(f"no sé leer `{path.suffix}`: usá .csv o .json")


def parse_text(text: str, *, fmt: str) -> list[RawRow]:
    """El texto ya decodificado, según el formato. Elige por sí sola qué parser usar."""
    if fmt == "csv":
        return parse_csv(text)
    if fmt == "json":
        return parse_json(text)
    raise ImportFormatError(f"formato desconocido: {fmt!r}")


def read_file(path: Path, *, fmt: str | None = None) -> list[RawRow]:
    """Lee el archivo y devuelve las filas crudas. Sin tocar la base.

    `utf-8-sig` y no `utf-8`: un CSV exportado de Excel arranca con BOM y sin esto
    la primera clave del encabezado llegaría con un carácter invisible adelante.
    """
    formato = fmt or detect_format(path)
    text = path.read_text(encoding="utf-8-sig")
    return parse_text(text, fmt=formato)


async def import_rows(
    session: AsyncSession,
    rows: list[RawRow],
    *,
    kind: ContentKind = QUIZ,
    status: str = "draft",
) -> ImportReport:
    """Valida e inserta. Las filas con un `fingerprint` ya presente se omiten.

    El `ON CONFLICT DO NOTHING` deja que la base decida el duplicado contra lo ya
    cargado; el duplicado *dentro del mismo archivo* lo frena el diccionario de
    hashes, porque dos filas iguales en un mismo INSERT no las cubre el conflicto.
    """
    if status not in CONTENT_STATUSES:
        raise ValueError(f"estado desconocido: {status!r}")

    validas: list[_ValidRow] = []
    rechazadas: list[RejectedRow] = []
    duplicadas = 0
    primera_por_hash: dict[str, int] = {}

    for row in rows:
        try:
            draft = kind.parse_row(row.values)
            legacy = _legacy_row(row.values, draft, fingerprint=kind.fingerprint(draft))
        except RowError as exc:
            rechazadas.append(RejectedRow(row.position, str(exc)))
            continue
        anterior = primera_por_hash.get(legacy.content_hash)
        if anterior is not None:
            duplicadas += 1
            continue
        primera_por_hash[legacy.content_hash] = row.position
        validas.append(_ValidRow(uuid.uuid4(), legacy, draft))

    insertadas = await _insert(session, validas, kind=kind, status=status)
    duplicadas += len(validas) - insertadas
    return ImportReport(imported=insertadas, duplicated=duplicadas, rejected=rechazadas)


def _legacy_row(
    values: dict[str, Any], draft: ContentDraft, *, fingerprint: str
) -> ParsedRow:
    """La fila en la forma de `questions`, para el dual-write temporal."""
    public = cast("dict[str, Any]", draft.public.payload)
    solution = cast("dict[str, Any]", draft.solution.payload)
    return ParsedRow(
        category=draft.categories[0],
        difficulty=draft.difficulty,
        prompt=public["prompt"],
        options=list(public["options"]),
        correct_index=solution["correct_index"],
        explanation=solution.get("explanation"),
        source=_text(values.get("source")) or None,
        tags=_tags(values.get("tags")),
        content_hash=fingerprint,
    )


INSERT_BATCH = 500


async def _insert(
    session: AsyncSession,
    filas: list[_ValidRow],
    *,
    kind: ContentKind,
    status: str,
) -> int:
    """Inserta las filas en lotes y devuelve cuántas entraron de verdad.

    Un INSERT con 100.000 filas es una sentencia gigante y un pico de memoria
    (H-15). Lotes de `INSERT_BATCH` mantienen la sentencia y el viaje acotados.
    El id se genera acá y se comparte con `questions`: el día que se corte el
    dual-write, el contenido nuevo ya tiene el mismo UUID en los dos lados.
    """
    insertadas = 0
    dual_write = kind.code == QUIZ.code
    for inicio in range(0, len(filas), INSERT_BATCH):
        lote = filas[inicio : inicio + INSERT_BATCH]
        valores = [
            {
                "id": fila.id,
                "kind": kind.code,
                "schema_version": fila.draft.schema_version,
                "status": status,
                "language": fila.draft.language,
                "difficulty": fila.draft.difficulty,
                "categories": list(fila.draft.categories),
                "payload": dict(fila.draft.public.payload),
                "media_type": fila.draft.public.media_type,
                "media_url": fila.draft.public.media_url,
                "content_hash": fila.legacy.content_hash,
            }
            for fila in lote
        ]
        resultado = await session.execute(
            pg_insert(ContentItem)
            .values(valores)
            .on_conflict_do_nothing(index_elements=["content_hash"])
            .returning(ContentItem.id)
        )
        creadas = set(resultado.scalars())
        if not creadas:
            continue
        creadas_filas = [fila for fila in lote if fila.id in creadas]

        await session.execute(
            pg_insert(ContentSolution)
            .values(
                [
                    {
                        "content_id": fila.id,
                        "payload": dict(fila.draft.solution.payload),
                    }
                    for fila in creadas_filas
                ]
            )
            .on_conflict_do_nothing(index_elements=["content_id"])
        )
        if dual_write:
            await session.execute(
                pg_insert(Question)
                .values([_question_values(fila, status) for fila in creadas_filas])
                .on_conflict_do_nothing(index_elements=["content_hash"])
            )
        insertadas += len(creadas)
    return insertadas


def _question_values(fila: _ValidRow, status: str) -> dict[str, Any]:
    pregunta = fila.legacy
    return {
        "id": fila.id,
        "category": pregunta.category,
        "difficulty": pregunta.difficulty,
        "prompt": pregunta.prompt,
        "options": pregunta.options,
        "correct_index": pregunta.correct_index,
        "explanation": pregunta.explanation,
        "source": pregunta.source,
        "status": status,
        "content_hash": pregunta.content_hash,
        "tags": pregunta.tags,
    }


async def import_file(
    session: AsyncSession,
    path: Path,
    *,
    kind: ContentKind = QUIZ,
    status: str = "draft",
    fmt: str | None = None,
) -> ImportReport:
    return await import_rows(
        session, read_file(path, fmt=fmt), kind=kind, status=status
    )
