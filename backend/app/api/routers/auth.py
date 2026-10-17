"""La puerta de entrada: el invitado pide un nick y se lleva su pase."""

from fastapi import APIRouter, Depends

from app.api.deps import OptionalUserDep, SessionDep
from app.api.errors import ApiError
from app.api.rate_limit import guest_rate_limit
from app.schemas.auth import GuestRequest
from app.schemas.users import AuthOut, UserOut
from app.security.nicks import NickRejected
from app.security.tokens import create_guest_token
from app.services.users import NickTaken, create_guest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/guest", status_code=201, dependencies=[Depends(guest_rate_limit)])
async def guest(
    body: GuestRequest, session: SessionDep, usuario: OptionalUserDep
) -> AuthOut:
    """Alta de invitado.

    Con un token válido no da de alta a nadie: devuelve el mismo usuario con un
    token fresco (el "crea o reutiliza" del plan) e ignora el nick del body, porque
    la identidad la manda el token.
    """
    if usuario is None:
        try:
            usuario = await create_guest(session, body.nick)
        except NickRejected as rechazo:
            raise ApiError(400, rechazo.code, rechazo.message) from None
        except NickTaken:
            raise ApiError(409, "NICK_TAKEN", "Ese nick ya está en uso.") from None
        # Alta de verdad: se commitea antes de responder (ver `get_session`).
        await session.commit()

    return AuthOut(
        user=UserOut.model_validate(usuario),
        token=create_guest_token(usuario.id, usuario.nick),
    )
