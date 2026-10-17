"""El token de invitado: lo que se firma se puede leer, y lo tocado no."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.config import settings
from app.security.tokens import (
    ALGORITHM,
    InvalidToken,
    create_guest_token,
    read_guest_token,
)


def test_a_fresh_token_round_trips() -> None:
    user_id = uuid.uuid4()

    identidad = read_guest_token(create_guest_token(user_id, "ana"))

    assert identidad.user_id == user_id
    assert identidad.nick == "ana"


def test_an_expired_token_is_rejected() -> None:
    vencido = datetime.now(UTC) - timedelta(days=settings.jwt_ttl_days, seconds=1)

    token = create_guest_token(uuid.uuid4(), "ana", now=vencido)

    with pytest.raises(InvalidToken):
        read_guest_token(token)


def test_a_token_signed_with_another_secret_is_rejected() -> None:
    ajeno = jwt.encode(
        {"sub": str(uuid.uuid4()), "nick": "ana"}, "otro-secreto", algorithm=ALGORITHM
    )

    with pytest.raises(InvalidToken):
        read_guest_token(ajeno)


def test_a_token_with_alg_none_is_rejected() -> None:
    # El ataque clásico: borrar la firma y pedir que no se verifique.
    crudo = jwt.encode(
        {"sub": str(uuid.uuid4()), "nick": "ana"}, key=None, algorithm="none"
    )

    with pytest.raises(InvalidToken):
        read_guest_token(crudo)


def test_a_token_whose_subject_is_not_a_uuid_is_rejected() -> None:
    raro = jwt.encode(
        {"sub": "1", "nick": "ana"}, settings.jwt_secret, algorithm=ALGORITHM
    )

    with pytest.raises(InvalidToken):
        read_guest_token(raro)


def test_a_token_without_a_nick_is_rejected() -> None:
    incompleto = jwt.encode(
        {"sub": str(uuid.uuid4())}, settings.jwt_secret, algorithm=ALGORITHM
    )

    with pytest.raises(InvalidToken):
        read_guest_token(incompleto)
