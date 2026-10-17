"""Salas: crear y consultar una por código."""

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUserDep, SessionDep
from app.api.errors import ApiError
from app.models import Room, User
from app.runtime.room_manager import room_store
from app.schemas.rooms import RoomCreate, RoomOut, RoomPreview
from app.services.rooms import create_room

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("", status_code=201)
async def crear_sala(
    body: RoomCreate, usuario: CurrentUserDep, session: SessionDep
) -> RoomOut:
    sala = await create_room(session, usuario, rounds=body.rounds, seconds=body.seconds)
    # El endpoint que escribe commitea: la respuesta no puede salir antes de que
    # la fila esté guardada (el commit del borde del pedido corre después).
    await session.commit()
    return RoomOut(code=sala.code, config=sala.config)


@router.get("/{code}")
async def vista_previa(code: str, session: SessionDep) -> RoomPreview:
    codigo = code.strip().upper()
    sala = await session.scalar(select(Room).where(Room.code == codigo))
    if sala is None:
        raise ApiError(404, "ROOM_NOT_FOUND", "No hay una sala con ese código.")
    host = await session.get(User, sala.host_user_id)
    return RoomPreview(
        code=sala.code,
        status=sala.status,
        config=sala.config,
        host_nick=host.nick if host is not None else None,
        expires_at=sala.expires_at,
        players=room_store.player_count(sala.code),
    )
