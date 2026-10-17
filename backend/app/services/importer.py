"""Cargar preguntas desde un archivo: CSV o JSON con las mismas claves.

Igual que `questions.py` (puro) contra `question_bank.py` (toca la base), acá
conviven las dos mitades y se pueden probar por separado: `read_file` +
`validate_row` no saben de Postgres, y `import_rows` no sabe de archivos. El
formato es el de §13.1 del plan: encabezado con estas columnas, `correct` en
letras, y el `content_hash` sale del enunciado normalizado para no cargar dos
veces la misma pregunta.

Reglas que el importador repite de la base a propósito: las del `CHECK` (categoría
conocida, dificultad 1–5, enunciado 1–300) más las que la base **no** puede
expresar (opciones no vacías y distintas). Se valida acá para poder informar la
fila exacta en vez de dejar reventar un `IntegrityError`.
"""

import csv
import hashlib
import io
import json
import unicodedata
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.game.constants import CATEGORIES, DIFFICULTY_MAX, DIFFICULTY_MIN
from app.models import Question
from app.models.question import PROMPT_MAX_LENGTH, STATUSES

# Las claves del formato, en el orden del encabezado de §13.1.
COLUMNS = (
    "category",
    "difficulty",
    "prompt",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct",
    "explanation",
    "source",
    "tags",
)
OPTION_KEYS = ("option_a", "option_b", "option_c", "option_d")
REQUIRED = ("category", "difficulty", "prompt", *OPTION_KEYS, "correct")
CORRECT_LETTERS = {"A": 0, "B": 1, "C": 2, "D": 3}


class ImportFormatError(Exception):
    """El archivo entero no se puede leer (no es una fila mala: es el formato)."""


class RowError(Exception):
    """Una fila no pasa la validación; el mensaje es el motivo que se informa."""


@dataclass(frozen=True)
class RawRow:
    """Una fila cruda, todavía sin validar. `position` es la línea del CSV (el
    encabezado es la 1) o el índice dentro del array de JSON (desde 1)."""

    position: int
    values: dict[str, Any]


@dataclass(frozen=True)
class ParsedRow:
    """Una fila ya validada, lista para entrar a la base."""

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


def normalize_prompt(prompt: str) -> str:
    """El enunciado en una forma comparable: sin tildes, sin signos, en
    minúsculas y con los espacios de adentro colapsados.

    Se pliegan los acentos (NFKD y se tiran los diacríticos) para que "¿Cuál es
    el río?" y "Cual es el rio?" sean la misma pregunta. Es solo para comparar:
    lo que se guarda es el enunciado tal como lo escribió el autor.
    """
    descompuesto = unicodedata.normalize("NFKD", prompt)
    sin_tildes = "".join(
        c for c in descompuesto if not unicodedata.combining(c)
    ).lower()
    sin_signos = "".join(c if c.isalnum() else " " for c in sin_tildes)
    return " ".join(sin_signos.split())


def content_hash(prompt: str) -> str:
    """SHA-256 del enunciado normalizado: es la clave del `UNIQUE` de la tabla."""
    return hashlib.sha256(normalize_prompt(prompt).encode("utf-8")).hexdigest()


def _text(raw: Any) -> str:
    return "" if raw is None else str(raw).strip()


def _is_number(raw: str) -> bool:
    return raw.lstrip("+-").isdigit()


def validate_row(values: dict[str, Any]) -> ParsedRow:
    """Convierte una fila cruda en `ParsedRow` o levanta `RowError` con el motivo."""
    category = _text(values.get("category"))
    if not category:
        raise RowError("falta la categoría")
    if category not in CATEGORIES:
        raise RowError(f"categoría desconocida: {category!r}")

    dificultad_texto = _text(values.get("difficulty"))
    if not dificultad_texto:
        raise RowError("falta la dificultad")
    if not _is_number(dificultad_texto):
        raise RowError(f"la dificultad {dificultad_texto!r} no es un número")
    difficulty = int(dificultad_texto)
    if not DIFFICULTY_MIN <= difficulty <= DIFFICULTY_MAX:
        raise RowError(
            f"la dificultad {difficulty} está fuera de {DIFFICULTY_MIN}-{DIFFICULTY_MAX}"
        )

    prompt = _text(values.get("prompt"))
    if not prompt:
        raise RowError("el enunciado está vacío")
    if len(prompt) > PROMPT_MAX_LENGTH:
        raise RowError(
            f"el enunciado tiene {len(prompt)} caracteres (máximo {PROMPT_MAX_LENGTH})"
        )

    options = []
    for clave in OPTION_KEYS:
        opcion = _text(values.get(clave))
        if not opcion:
            raise RowError(f"la opción {clave[-1].upper()} está vacía")
        options.append(opcion)
    # casefold: "París" y "parís" son la misma opción para quien juega.
    if len({o.casefold() for o in options}) < len(options):
        raise RowError("hay opciones repetidas")

    correct = _text(values.get("correct")).upper()
    if correct not in CORRECT_LETTERS:
        raise RowError("la respuesta correcta debe ser A, B, C o D")

    return ParsedRow(
        category=category,
        difficulty=difficulty,
        prompt=prompt,
        options=options,
        correct_index=CORRECT_LETTERS[correct],
        explanation=_text(values.get("explanation")) or None,
        source=_text(values.get("source")) or None,
        tags=_tags(values.get("tags")),
        content_hash=content_hash(prompt),
    )


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


def read_file(path: Path, *, fmt: str | None = None) -> list[RawRow]:
    """Lee el archivo y devuelve las filas crudas. Sin tocar la base.

    `utf-8-sig` y no `utf-8`: un CSV exportado de Excel arranca con BOM y sin esto
    la primera clave del encabezado llegaría con un carácter invisible adelante.
    """
    formato = fmt or detect_format(path)
    text = path.read_text(encoding="utf-8-sig")
    return parse_csv(text) if formato == "csv" else parse_json(text)


async def import_rows(
    session: AsyncSession, rows: list[RawRow], *, status: str = "draft"
) -> ImportReport:
    """Valida e inserta. Las filas con `content_hash` ya presente se omiten.

    El `ON CONFLICT DO NOTHING` deja que la base decida el duplicado contra lo ya
    cargado; el duplicado *dentro del mismo archivo* lo frena el diccionario de
    hashes, porque dos filas iguales en un mismo INSERT no las cubre el conflicto.
    """
    if status not in STATUSES:
        raise ValueError(f"estado desconocido: {status!r}")

    validas: list[ParsedRow] = []
    rechazadas: list[RejectedRow] = []
    duplicadas = 0
    primera_por_hash: dict[str, int] = {}

    for row in rows:
        try:
            fila = validate_row(row.values)
        except RowError as exc:
            rechazadas.append(RejectedRow(row.position, str(exc)))
            continue
        anterior = primera_por_hash.get(fila.content_hash)
        if anterior is not None:
            duplicadas += 1
            continue
        primera_por_hash[fila.content_hash] = row.position
        validas.append(fila)

    insertadas = await _insert(session, validas, status)
    duplicadas += len(validas) - insertadas
    return ImportReport(imported=insertadas, duplicated=duplicadas, rejected=rechazadas)


async def _insert(session: AsyncSession, filas: list[ParsedRow], status: str) -> int:
    """Inserta las filas y devuelve cuántas entraron de verdad."""
    if not filas:
        return 0
    valores = [
        {
            "id": uuid.uuid4(),
            "category": fila.category,
            "difficulty": fila.difficulty,
            "prompt": fila.prompt,
            "options": fila.options,
            "correct_index": fila.correct_index,
            "explanation": fila.explanation,
            "source": fila.source,
            "status": status,
            "content_hash": fila.content_hash,
            "tags": fila.tags,
        }
        for fila in filas
    ]
    resultado = await session.execute(
        pg_insert(Question)
        .values(valores)
        .on_conflict_do_nothing(index_elements=["content_hash"])
        .returning(Question.id)
    )
    return len(resultado.all())


async def import_file(
    session: AsyncSession,
    path: Path,
    *,
    status: str = "draft",
    fmt: str | None = None,
) -> ImportReport:
    return await import_rows(session, read_file(path, fmt=fmt), status=status)
