"""Comandos de administración, fuera de la API HTTP.

Se corren desde `backend/` con `uv run python -m app.cli <comando>` (o por los
atajos del Makefile). A diferencia de los endpoints, acá la sesión **no** commitea
sola: `session_factory` no tiene el commit automático de `get_session`, así que el
comando cierra la transacción a mano.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from app.db import engine, session_factory
from app.game.modes.quiz import CONTENT_KINDS, QUIZ, get_content_kind
from app.models.content import STATUSES
from app.services import importer

# Las semilla viven en el repo, en el mismo formato que importa `import-questions`:
# así `seed` es el importador apuntado a un archivo fijo, con un solo camino probado.
SEED_FILE = Path(__file__).resolve().parent.parent / "seeds" / "questions.csv"


def _add_import_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("file", type=Path)
    parser.add_argument("--format", choices=("csv", "json"), default=None)
    parser.add_argument("--status", choices=STATUSES, default="draft")
    parser.add_argument("--kind", choices=tuple(CONTENT_KINDS), default=QUIZ.code)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.cli", description="Admin de Omnisapiens."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    importar = sub.add_parser(
        "import-content", help="Importa un CSV o JSON de contenido."
    )
    _add_import_args(importar)

    # Alias del comando anterior: el mismo importador, con `--kind quiz`.
    preguntas = sub.add_parser(
        "import-questions", help="Alias de import-content --kind quiz."
    )
    _add_import_args(preguntas)

    # Las semilla entran publicadas: son curadas a mano, no salidas de un generador
    # que haya que revisar antes de que `candidates()` las vea.
    sub.add_parser("seed", help="Carga las preguntas semilla del repo.").add_argument(
        "--status", choices=STATUSES, default="published"
    )

    return parser


async def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "seed":
        archivo, formato, kind = SEED_FILE, None, QUIZ
    else:
        archivo, formato = args.file, args.format
        kind = get_content_kind(args.kind)

    try:
        async with session_factory() as session:
            report = await importer.import_file(
                session, archivo, kind=kind, status=args.status, fmt=formato
            )
            await session.commit()
    except importer.ImportFormatError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    _print_report(archivo, report)
    return 0


def _print_report(archivo: Path, report: importer.ImportReport) -> None:
    print(f"{archivo}: {report.total} filas")
    print(f"  importadas: {report.imported}")
    print(f"  duplicadas: {report.duplicated}")
    print(f"  rechazadas: {len(report.rejected)}")
    for fila in report.rejected:
        print(f"    fila {fila.row}: {fila.reason}")


async def _run(args: argparse.Namespace) -> int:
    try:
        return await _dispatch(args)
    finally:
        # El proceso es corto: sin esto quedan conexiones del pool abiertas
        # cuando el loop se cierra.
        await engine.dispose()


def main() -> None:
    args = _build_parser().parse_args()
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
