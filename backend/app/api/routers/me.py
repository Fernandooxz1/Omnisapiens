"""El perfil: leerlo, cambiar el nick y darse de baja."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Response

from app.api.deps import CurrentUserDep, SessionDep
from app.api.errors import ApiError
from app.schemas.users import (
    ArcadeRunOut,
    AuthOut,
    BestMarksOut,
    MatchSummaryOut,
    NickUpdate,
    ProfileOut,
    UserOut,
)
from app.security.nicks import NickRejected
from app.security.tokens import create_guest_token
from app.services import profile
from app.services.users import NickTaken, rename_user, soft_delete_user

router = APIRouter(prefix="/me", tags=["me"])


@router.get("")
async def me(usuario: CurrentUserDep, session: SessionDep) -> ProfileOut:
    ahora = datetime.now(UTC)
    # Una escritura por cada GET es demasiado si el frontend consulta seguido: se
    # refresca como mucho una vez por minuto (H-23).
    if usuario.last_seen_at <= ahora - timedelta(minutes=1):
        usuario.last_seen_at = ahora
        await session.commit()

    marcas = await profile.best_marks(session, user_id=usuario.id)
    corridas = await profile.recent_runs(session, user_id=usuario.id)
    partidas = await profile.recent_matches(session, user_id=usuario.id)
    return ProfileOut(
        **UserOut.model_validate(usuario).model_dump(),
        best=BestMarksOut(all_time=marcas.all_time, week=marcas.week),
        arcade_runs=[ArcadeRunOut.model_validate(corrida) for corrida in corridas],
        matches=[
            MatchSummaryOut(
                id=partida.id,
                ended_at=partida.ended_at,
                opponent_nick=partida.opponent_nick,
                my_score=partida.my_score,
                opponent_score=partida.opponent_score,
                result=partida.result,
            )
            for partida in partidas
        ],
    )


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

    await session.commit()
    # El pase viejo lleva el nick viejo adentro: se emite uno fresco para que no mienta.
    return AuthOut(
        user=UserOut.model_validate(usuario),
        token=create_guest_token(usuario.id, usuario.nick),
    )


@router.delete("", status_code=204)
async def delete_me(usuario: CurrentUserDep, session: SessionDep) -> Response:
    await soft_delete_user(session, usuario)
    await session.commit()
    return Response(status_code=204)
