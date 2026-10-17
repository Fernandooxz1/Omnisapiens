"""El pase firmado del invitado: el servidor no guarda sesiones, guarda la firma.

HS256 es HMAC sobre el payload con `JWT_SECRET`. Si el cliente edita el payload
(el id, el nick, la fecha de vencimiento), la firma deja de cerrar. Lo que el
token **no** da es revocación: no hay lista de pases anulados, así que un token
robado sirve hasta que vence (decisión aceptada en el plan, §12).
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from app.config import settings

ALGORITHM = "HS256"


@dataclass(frozen=True)
class GuestIdentity:
    user_id: uuid.UUID
    nick: str


class InvalidToken(Exception):
    """Firma rota, token vencido, o payload con una forma que no esperábamos."""


def create_guest_token(
    user_id: uuid.UUID, nick: str, *, now: datetime | None = None
) -> str:
    """El `now` es para los tests: la expiración se decide acá y en ningún otro lado."""
    emitido = now or datetime.now(UTC)
    payload = {
        # `sub` va como texto: el RFC dice string y PyJWT lo valida.
        "sub": str(user_id),
        "nick": nick,
        "guest": True,
        "iat": emitido,
        "exp": emitido + timedelta(days=settings.jwt_ttl_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def read_guest_token(token: str) -> GuestIdentity:
    """Verifica y devuelve la identidad. Cualquier problema es `InvalidToken`."""
    try:
        # `algorithms` explícito: sin la lista, un token con `"alg": "none"` o con
        # otro algoritmo pasaría por válido (el ataque clásico de JWT).
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        return GuestIdentity(user_id=uuid.UUID(payload["sub"]), nick=payload["nick"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError) as exc:
        # Un solo error hacia afuera: quien llama no tiene por qué distinguir
        # "vencido" de "firmado con otra clave" de "no era un uuid". `PyJWTError`
        # y no `InvalidTokenError`: la familia incluye fallas de clave y de
        # algoritmo, y ninguna de esas debería llegar como 500.
        raise InvalidToken(str(exc)) from exc
