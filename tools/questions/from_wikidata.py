#!/usr/bin/env python3
"""Genera un CSV de preguntas de capitales a partir de Wikidata (CC0).

Pensado para producir **borradores**: la calidad de los distractores y la
dificultad son heurísticas, así que conviene revisarlas antes de publicarlas.
El CSV resultante entra por el importador normal (`/admin` o `make import`).

Uso:
    python3 tools/questions/from_wikidata.py --limit 25 --out capitales.csv

Solo usa la biblioteca estándar. La consulta pide etiquetas en español.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "Omnisapiens/0.1 (https://github.com/; importador de contenido)"

# Estados soberanos actuales, con su capital y población (si la tienen).
QUERY = """
SELECT ?country ?countryLabel ?capital ?capitalLabel (MAX(?pop) AS ?population) WHERE {
  ?country wdt:P31 wd:Q3624078;
           wdt:P36 ?capital.
  FILTER NOT EXISTS { ?country wdt:P576 ?end. }
  OPTIONAL { ?country wdt:P1082 ?pop. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
}
GROUP BY ?country ?countryLabel ?capital ?capitalLabel
"""

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

LETTERS = "ABCD"


@dataclass(frozen=True)
class Country:
    id: str
    name: str
    capital: str
    population: int


def fetch() -> list[Country]:
    url = f"{ENDPOINT}?{urllib.parse.urlencode({'query': QUERY, 'format': 'json'})}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)

    # Un país puede tener varias capitales (Sudáfrica): la pregunta quedaría
    # ambigua, así que se descartan todos sus registros.
    grouped: dict[str, list[Country]] = {}
    for binding in payload["results"]["bindings"]:
        def value(key: str) -> str:
            return binding.get(key, {}).get("value", "").strip()

        country = Country(
            id=value("country").rsplit("/", 1)[-1],
            name=value("countryLabel"),
            capital=value("capitalLabel"),
            population=int(float(value("population") or 0)),
        )
        if country.name and country.capital and country.name != country.capital:
            grouped.setdefault(country.id, []).append(country)

    countries = []
    for rows in grouped.values():
        if len(rows) == 1:
            countries.append(rows[0])
    return countries


def difficulty(population: int) -> int:
    """Más población suele ser un país más reconocible: 1 fácil, 4 difícil."""
    if population >= 50_000_000:
        return 1
    if population >= 5_000_000:
        return 2
    if population >= 500_000:
        return 3
    return 4


def distractors(origin: Country, pool: list[Country], rng: random.Random) -> list[str]:
    """Capitales de países con población parecida: opciones plausibles."""
    others = [one for one in pool if one.id != origin.id]
    if not others:
        return []

    origin_weight = math.log10(origin.population + 1)
    others.sort(key=lambda one: abs(math.log10(one.population + 1) - origin_weight))
    candidates = others[:30]
    chosen = rng.sample(candidates, k=min(3, len(candidates)))
    return [one.capital for one in chosen]


def rows(countries: list[Country], limit: int, seed: int) -> list[dict[str, str]]:
    rng = random.Random(seed)
    selected = list(countries)
    rng.shuffle(selected)
    selected = selected[:limit]

    result = []
    for country in selected:
        options = distractors(country, countries, rng)
        if len(options) < 3:
            continue

        options.append(country.capital)
        rng.shuffle(options)
        result.append(
            {
                "category": "geography",
                "difficulty": str(difficulty(country.population)),
                "prompt": f"¿Cuál es la capital de {country.name}?",
                "option_a": options[0],
                "option_b": options[1],
                "option_c": options[2],
                "option_d": options[3],
                "correct": LETTERS[options.index(country.capital)],
                "explanation": f"{country.capital} es la capital de {country.name}.",
                "source": "wikidata",
                "tags": "capitales;geografía;wikidata",
            }
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=30, help="cuántas preguntas generar")
    parser.add_argument("--out", type=Path, help="archivo de salida (default: stdout)")
    parser.add_argument("--seed", type=int, default=7, help="semilla de los distractores")
    args = parser.parse_args()

    countries = fetch()
    generated = rows(countries, args.limit, args.seed)
    if not generated:
        print("sin filas para escribir", file=sys.stderr)
        return 1

    if args.out:
        handle = args.out.open("w", encoding="utf-8", newline="")
    else:
        handle = sys.stdout
    try:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(generated)
    finally:
        if args.out:
            handle.close()

    print(f"{len(generated)} preguntas generadas", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
