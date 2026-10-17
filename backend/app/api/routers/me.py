"""El perfil: leerlo, cambiar el nick y darse de baja."""

from datetime import UTC, datetime

from fastapi import APIRouter, Response

from app.api.deps import CurrentUserDep, SessionDep
from app.api.errors import ApiError
from app.schemas.users import AuthOut, NickUpdate, UserOut
from app.security.nicks import NickRejected
from app.security.tokens import create_guest_token
from app.services.users import NickTaken, rename_user, soft_delete_user

router = APIRouter(prefix="/me", tags=["me"])


@router.get("")
async def me(usuario: CurrentUserDep, session: SessionDep) -> UserOut:
    usuario.last_seen_at = datetime.now(UTC)
    await session.flush()
    return UserOut.model_validate(usuario)


@router.patch("")
async def update_me(
    body: NickUpdate, usuario: CurrentUserDep, session: SessionDep
) -> AuthOut:
    try:
        usuario = await rename_user(session, usuario, body.nick)
    except NickRejected as rechazo:
        raise ApiError(400, rechazo.code, rechazo.message) from None
    except NickTaken:
        raise ApiError(409, "NICK_TAKEN", "Ese nick ya está en uso.") from None

    # El pase viejo lleva el nick viejo adentro: se emite uno fresco para que no mienta.
    return AuthOut(
        user=UserOut.model_validate(usuario),
        token=create_guest_token(usuario.id, usuario.nick),
    )


@router.delete("", status_code=204)
async def delete_me(usuario: CurrentUserDep, session: SessionDep) -> Response:
    await soft_delete_user(session, usuario)
    return Response(status_code=204)
