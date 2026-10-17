"""El filtro de nicks: lo que se limpia, lo que se rechaza y lo que se inventa."""

import re

import pytest

from app.security.nicks import (
    FORBIDDEN_WORDS,
    NICK_MAX_LENGTH,
    NickRejected,
    clean_nick,
    random_nick,
)


@pytest.mark.parametrize("palabra", FORBIDDEN_WORDS)
def test_every_word_of_the_list_is_rejected(palabra: str) -> None:
    # La lista entera y no un ejemplo: si mañana se agrega una palabra, este test
    # ya la cubre sin que nadie se acuerde de escribir el caso.
    with pytest.raises(NickRejected) as rechazo:
        clean_nick(palabra)

    assert rechazo.value.code == "NICK_FORBIDDEN"


@pytest.mark.parametrize(
    "crudo",
    ["P.U.T.O", "putó", "pu to", "XxPutoXx", "fácking mierda"],
)
def test_punctuation_accents_and_case_do_not_hide_a_word(crudo: str) -> None:
    with pytest.raises(NickRejected):
        clean_nick(crudo)


@pytest.mark.parametrize("crudo", ["circulo", "vehiculo", "articulada"])
def test_a_nick_that_merely_contains_letters_of_a_word_is_accepted(crudo: str) -> None:
    # Documenta el criterio de la lista: ninguna palabra prohibida puede ser pedazo
    # de una palabra común, o el filtro empieza a rechazar nicks inocentes.
    assert clean_nick(crudo) == crudo


def test_spaces_are_cleaned_inside_and_outside() -> None:
    assert clean_nick("  ana   maría  ") == "ana maría"


@pytest.mark.parametrize("crudo", ["", "   ", "\t\n"])
def test_a_nick_without_visible_characters_is_rejected(crudo: str) -> None:
    with pytest.raises(NickRejected) as rechazo:
        clean_nick(crudo)

    assert rechazo.value.code == "NICK_LENGTH"


def test_a_nick_of_the_max_length_is_accepted() -> None:
    assert clean_nick("a" * NICK_MAX_LENGTH) == "a" * NICK_MAX_LENGTH


def test_a_nick_one_character_longer_is_rejected() -> None:
    with pytest.raises(NickRejected) as rechazo:
        clean_nick("a" * (NICK_MAX_LENGTH + 1))

    assert rechazo.value.code == "NICK_LENGTH"


def test_a_generated_nick_has_the_documented_shape() -> None:
    generado = random_nick()

    assert re.fullmatch(r"Jugador\d{4}", generado)
    assert len(generado) <= NICK_MAX_LENGTH
