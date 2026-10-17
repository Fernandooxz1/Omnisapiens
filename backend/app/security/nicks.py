"""Nick: cómo se limpia, qué se rechaza y cuál se inventa cuando no hay ninguno.

Acá vive el único criterio de "nick aceptable": lo usa el alta de invitado hoy y
lo va a usar el `PATCH /me` mañana. Nada de esto importa FastAPI ni la base.
"""

import unicodedata
from random import randint

NICK_MAX_LENGTH = 16

# Lista corta y a mano: alcanza para el MVP y para un test que la recorre entera.
# No pretende moderar de verdad: no ve leet ("put0") ni homoglifos (cirílico).
# Cada palabra se elige para que no sea pedazo de una palabra común: "culo"
# quedaría afuera porque "circulo" o "vehiculo" la contienen, y el filtro
# empezaría a rechazar nicks inocentes.
FORBIDDEN_WORDS = (
    "bitch",
    "fuck",
    "mierda",
    "nigga",
    "pija",
    "poronga",
    "puta",
    "puto",
    "verga",
)


class NickRejected(Exception):
    """El nick no cumple una regla. `code` es el código que sale por la API."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def normalize(raw: str) -> str:
    """Saca espacios de sobra (afuera y adentro).

    El `CHECK` de la base exige `nick = btrim(nick)`: limpiar acá y no en la base
    deja el rechazo en la puerta y no en el INSERT.
    """
    return " ".join(raw.split())


def _fold(text: str) -> str:
    """Solo a-z0-9: mayúsculas, acentos y separadores no esconden una palabra."""
    descompuesto = unicodedata.normalize("NFKD", text.casefold())
    sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return "".join(c for c in sin_acentos if c.isascii() and c.isalnum())


def clean_nick(raw: str) -> str:
    """Normaliza y valida. Devuelve el nick listo para guardar, o levanta."""
    nick = normalize(raw)
    if not nick:
        raise NickRejected("NICK_LENGTH", "El nick no puede quedar vacío.")
    if len(nick) > NICK_MAX_LENGTH:
        raise NickRejected(
            "NICK_LENGTH", f"El nick no puede pasar de {NICK_MAX_LENGTH} caracteres."
        )

    plegado = _fold(nick)
    if any(palabra in plegado for palabra in FORBIDDEN_WORDS):
        raise NickRejected("NICK_FORBIDDEN", "Ese nick no está permitido.")
    return nick


def random_nick() -> str:
    """El que se lleva quien no eligió ninguno: `Jugador4821`."""
    return f"Jugador{randint(1000, 9999)}"
