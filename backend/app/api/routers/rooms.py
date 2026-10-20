"""Salas: crear y consultar una por código."""

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUserDep, SessionDep
from app.api.errors import ApiError
from app.api.rate_limit import room_rate_limit
from app.models import User
from app.runtime.session_store import session_store
from app.schemas.rooms import RoomCreate, RoomOut, RoomPreview
from app.services.rooms import create_room, get_by_code, room_is_available

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("", status_code=201)
async def new_room(
    body: RoomCreate, usuario: CurrentUserDep, session: SessionDep
) -> RoomOut:
    sala = await create_room(session, usuario, rounds=body.rounds, seconds=body.seconds)
    # El endpoint que escribe commitea: la respuesta no puede salir antes de que
    # la fila esté guardada (el commit del borde del pedido corre después).
    await session.commit()
    return RoomOut(code=sala.code, config=sala.config)


@router.get("/{code}", dependencies=[Depends(room_rate_limit)])
async def room_preview(code: str, session: SessionDep) -> RoomPreview:
    sala = await get_by_code(session, code)
    if sala is None or not room_is_available(sala):
        raise ApiError(404, "ROOM_NOT_FOUND", "No hay una sala con ese código.")
    host = await session.get(User, sala.host_user_id)
    return RoomPreview(
        code=sala.code,
        status=sala.status,
        config=sala.config,
        host_nick=host.nick if host is not None else None,
        expires_at=sala.expires_at,
        players=session_store.player_count(sala.code),
    )
