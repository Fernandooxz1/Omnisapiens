"""Valida los CSV de semilla antes de que entren a la base.

Corre sin base ni API: es el guardarraíl previo a `make import`. Reusa la
validación del `ContentKind` de quiz (`QUIZ.parse_row`), así el script no puede
aceptar algo que el importador después rechace, y agrega lo que la base no ve:

- encabezado exacto y columnas completas;
- opciones no vacías y distintas, categoría y dificultad válidas;
- enunciados duplicados, comparados sin tildes ni signos;
- pares sospechosos de ser la misma pregunta reescrita: misma respuesta y
  vocabulario casi igual, o enunciados casi idénticos letra por letra.

La similitud es léxica, no embeddings: alcanza para duplicados y reescrituras
parecidas, no para paráfrasis que no comparten palabras. Un par sospechoso falla
por defecto; `--allow-similar` lo deja como aviso para revisarlo a mano.

Uso (desde `backend/`, como el resto de los comandos):
    uv run python -m tools.check_seeds                     # seeds/*.csv
    uv run python -m tools.check_seeds lote.csv --threshold 0.92
"""

import argparse
import csv
import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from app.game.modes.quiz import QUIZ
from app.game.modes.quiz.content import (
    COLUMNS,
    RowError,
    content_hash,
    normalize_prompt,
)

# Por debajo de esto, dos enunciados con la misma respuesta no se parecen.
JACCARD_FLOOR = 0.4
# Dos enunciados casi iguales letra por letra son sospechosos aunque la respuesta
# no coincida (una errata en la opción correcta también es un duplicado).
RATIO_FLOOR = 0.96

# Palabras de la pregunta que no distinguen un tema de otro. Se aplican sobre el
# enunciado ya normalizado (sin tildes ni signos).
STOPWORDS = frozenset(
    {
        "a",
        "al",
        "algo",
        "como",
        "con",
        "cual",
        "cuales",
        "cuando",
        "de",
        "del",
        "el",
        "ella",
        "ellas",
        "ellos",
        "en",
        "entre",
        "era",
        "es",
        "esa",
        "ese",
        "eso",
        "esta",
        "este",
        "esto",
        "fue",
        "ha",
        "hasta",
        "la",
        "las",
        "lo",
        "los",
        "mas",
        "me",
        "mi",
        "mis",
        "mucho",
        "muy",
        "no",
        "nos",
        "o",
        "para",
        "pero",
        "por",
        "que",
        "se",
        "ser",
        "si",
        "sin",
        "sobre",
        "su",
        "sus",
        "te",
        "tu",
        "un",
        "una",
        "uno",
        "unos",
        "unas",
        "y",
        "ya",
    }
)


@dataclass(frozen=True)
class Prompt:
    file: Path
    line: int
    text: str
    answer: str
    normalized: str
    words: frozenset[str]
    difficulty: int
    category: str


def _read(path: Path, errores: list[str]) -> list[Prompt]:
    try:
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                errores.append(f"{path}: el CSV está vacío")
                return []
            encabezado = {campo.strip() for campo in reader.fieldnames}
            if encabezado != set(COLUMNS):
                faltan = sorted(set(COLUMNS) - encabezado)
                sobran = sorted(encabezado - set(COLUMNS))
                partes = []
                if faltan:
                    partes.append(f"faltan {', '.join(faltan)}")
                if sobran:
                    partes.append(f"sobran {', '.join(sobran)}")
                errores.append(f"{path}: encabezado inesperado ({'; '.join(partes)})")
                return []
            prompts = []
            for crudo in reader:
                fila = {clave.strip(): valor for clave, valor in crudo.items()}
                try:
                    borrador = QUIZ.parse_row(fila)
                except RowError as exc:
                    errores.append(f"{path}:{reader.line_num}: {exc}")
                    continue
                texto = str(fila["prompt"]).strip()
                correcta = f"option_{str(fila['correct']).strip().lower()}"
                prompts.append(
                    Prompt(
                        file=path,
                        line=reader.line_num,
                        text=texto,
                        answer=str(fila[correcta]).strip(),
                        normalized=normalize_prompt(texto),
                        words=frozenset(normalize_prompt(texto).split()) - STOPWORDS,
                        difficulty=borrador.difficulty,
                        category=borrador.categories[0],
                    )
                )
            return prompts
    except OSError as exc:
        errores.append(f"{path}: no se pudo leer ({exc.strerror})")
        return []


def _duplicates(prompts: list[Prompt], errores: list[str]) -> None:
    """Mismo enunciado normalizado: la base lo rechazaría por `content_hash`."""
    por_hash: dict[str, Prompt] = {}
    for prompt in prompts:
        clave = content_hash(prompt.text)
        previo = por_hash.get(clave)
        if previo is None:
            por_hash[clave] = prompt
            continue
        errores.append(
            f"{prompt.file}:{prompt.line}: duplicado exacto de "
            f"{previo.file}:{previo.line} ({prompt.text[:70]!r})"
        )


def _similar_pairs(
    prompts: list[Prompt], threshold: float
) -> list[tuple[float, float, bool, Prompt, Prompt]]:
    """Pares sospechosos: misma respuesta y vocabulario parecido, o texto casi igual.

    Devuelve `(ratio, jaccard, misma_respuesta, previo, actual)`. Los duplicados
    exactos ya se informaron, así que se saltean.
    """
    pares = []
    for i, actual in enumerate(prompts):
        for previo in prompts[:i]:
            if actual.normalized == previo.normalized:
                continue
            ratio = SequenceMatcher(None, previo.normalized, actual.normalized).ratio()
            union = previo.words | actual.words
            jaccard = len(previo.words & actual.words) / len(union) if union else 0.0
            misma_respuesta = normalize_prompt(previo.answer) == normalize_prompt(
                actual.answer
            )
            if ratio >= threshold or (misma_respuesta and jaccard >= JACCARD_FLOOR):
                pares.append((ratio, jaccard, misma_respuesta, previo, actual))
    return sorted(pares, key=lambda par: par[0], reverse=True)


def _distribution(prompts: list[Prompt]) -> str:
    dificultad = {n: 0 for n in range(1, 6)}
    categoria: dict[str, int] = {}
    for prompt in prompts:
        dificultad[prompt.difficulty] += 1
        categoria[prompt.category] = categoria.get(prompt.category, 0) + 1
    niveles = " ".join(f"{n}:{total}" for n, total in dificultad.items())
    categorias = " ".join(f"{c}:{total}" for c, total in sorted(categoria.items()))
    return f"dificultad {niveles}\ncategorías {categorias}"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="check-seeds", description="Valida los CSV de semilla del quiz."
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="archivos a validar (por defecto seeds/*.csv)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=RATIO_FLOOR,
        help="similitud de texto que ya se considera sospechosa (0-1, "
        f"por defecto {RATIO_FLOOR})",
    )
    parser.add_argument(
        "--allow-similar",
        action="store_true",
        help="trata los pares sospechosos como aviso en vez de error",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    archivos = args.files or sorted(Path("seeds").glob("*.csv"))
    if not archivos:
        print("error: no hay archivos para validar", file=sys.stderr)
        return 1

    errores: list[str] = []
    avisos: list[str] = []
    prompts: list[Prompt] = []
    for archivo in archivos:
        leidos = _read(archivo, errores)
        prompts.extend(leidos)
        print(f"{archivo}: {len(leidos)} preguntas")

    _duplicates(prompts, errores)
    parecidos = _similar_pairs(prompts, args.threshold)

    print(f"total: {len(prompts)} preguntas")
    print(_distribution(prompts))

    for ratio, jaccard, misma_respuesta, previo, actual in parecidos:
        detalle = [
            f"texto {ratio:.0%}",
            f"vocabulario {jaccard:.0%}",
            "misma respuesta" if misma_respuesta else "respuesta distinta",
        ]
        mensaje = (
            f"posible duplicado semántico ({', '.join(detalle)}): "
            f"{previo.file}:{previo.line} y {actual.file}:{actual.line}\n"
            f"  - {previo.text}\n  - {actual.text}"
        )
        (avisos if args.allow_similar else errores).append(mensaje)

    for aviso in avisos:
        print(f"aviso: {aviso}")

    if errores:
        print(f"\n{len(errores)} problemas:", file=sys.stderr)
        for error in errores:
            print(f"  {error}", file=sys.stderr)
        return 1

    print(f"\nOK: {len(prompts)} preguntas sin duplicados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
