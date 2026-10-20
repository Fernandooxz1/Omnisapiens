"""El validador de semillas: lo que bloquea antes de importar."""

import csv
from pathlib import Path

from tools.check_seeds import main

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


def _row(
    prompt: str = "¿Cuál es la capital de Francia?",
    *,
    answer: str = "París",
    category: str = "geography",
    difficulty: str = "2",
) -> dict[str, str]:
    return {
        "category": category,
        "difficulty": difficulty,
        "prompt": prompt,
        "option_a": answer,
        "option_b": "Lyon",
        "option_c": "Niza",
        "option_d": "Marsella",
        "correct": "A",
        "explanation": "París es la capital.",
        "source": "llm",
        "tags": "capitales",
    }


def _write(path: Path, *filas: dict[str, str]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(filas)
    return path


def test_a_clean_file_passes(tmp_path: Path, capsys: object) -> None:
    archivo = _write(
        tmp_path / "ok.csv",
        _row(),
        _row("¿Cuál es la capital de Italia?", answer="Roma"),
    )

    assert main([str(archivo)]) == 0


def test_an_exact_duplicate_is_rejected(tmp_path: Path) -> None:
    archivo = _write(tmp_path / "dup.csv", _row(), _row())

    assert main([str(archivo)]) == 1


def test_an_invalid_row_is_rejected(tmp_path: Path) -> None:
    archivo = _write(tmp_path / "mala.csv", _row(difficulty="9"))

    assert main([str(archivo)]) == 1


def test_a_missing_column_is_rejected(tmp_path: Path) -> None:
    archivo = _write(tmp_path / "columnas.csv", _row())
    texto = archivo.read_text(encoding="utf-8").replace("tags\n", "\n")
    archivo.write_text(texto, encoding="utf-8")

    assert main([str(archivo)]) == 1


def test_a_reworded_prompt_with_the_same_answer_is_flagged(tmp_path: Path) -> None:
    archivo = _write(
        tmp_path / "sim.csv",
        _row("¿Cuál es la capital oficial de Francia?"),
        _row("¿Cuál es la capital de Francia?"),
    )

    assert main([str(archivo)]) == 1
    assert main([str(archivo), "--allow-similar"]) == 0


def test_two_templated_questions_with_different_answers_pass(tmp_path: Path) -> None:
    archivo = _write(
        tmp_path / "planilla.csv",
        _row("¿Cuál es la capital oficial de Francia?"),
        _row("¿Cuál es la capital oficial de Italia?", answer="Roma"),
    )

    assert main([str(archivo)]) == 0
