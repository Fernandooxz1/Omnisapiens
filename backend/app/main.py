import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import errors
from app.api.limits import BodySizeLimitMiddleware
from app.api.routers import admin, auth, health, leaderboard, me, rooms
from app.config import settings
from app.db import engine, session_factory
from app.logging_config import configure_logging
from app.redis import redis_client
from app.runtime.live import Live, live_arcade_runs
from app.runtime.room_manager import InMemoryRoomStore, room_store
from app.runtime.session_store import session_store
from app.services.reaper import sweep
from app.ws import arcade_ws, room_ws

logger = logging.getLogger(__name__)


def _check_process_scope() -> None:
    """Fuera de `local`, el despliegue tiene que declarar un solo proceso (H-07).

    Con `--workers 2` cada worker tendría su propio `room_store` y su propio
    registro de corridas vivas: dos verdades para el mismo código de sala, y dos
    jugadores que se ven como si el otro no hubiera llegado. Desde adentro del
    proceso no hay forma de contar los workers, así que el guard exige que quien
    despliega lo declare; el día que exista el `RoomStore` sobre Redis esta
    comprobación se cae sola, porque el store deja de ser el en memoria.
    """
    if settings.env == "local" or settings.single_process:
        return
    if isinstance(room_store, InMemoryRoomStore):
        raise RuntimeError(
            "ENV != local con el estado vivo en memoria: corré un solo worker "
            "(--workers 1) y declaralo con SINGLE_PROCESS=1, o implementá el "
            "RoomStore sobre Redis (H-07 en docs/archive/backend/observaciones.md)."
        )


async def _sweep_once(*, startup: bool = False) -> None:
    """Un barrido con lo que este proceso tiene vivo en este instante.

    Al arrancar no hay salas ni corridas en memoria, así que `live` queda vacío y
    toda fila abierta es de un proceso anterior; en régimen, `live` protege lo
    que está jugándose.
    """
    live = Live(
        rooms=room_store.live(),
        arcade_runs=live_arcade_runs.ids(),
        sessions=session_store.live(),
    )
    async with session_factory() as session:
        resultado = await sweep(session, live=live)

    if startup or (
        resultado.expired_rooms
        or resultado.voided_matches
        or resultado.invalidated_runs
        or resultado.invalidated_sessions
    ):
        logger.info(
            "%s: %d salas expiradas, %d partidas anuladas, %d corridas "
            "invalidadas, %d sesiones invalidadas",
            "barrido inicial" if startup else "barrido periódico",
            resultado.expired_rooms,
            resultado.voided_matches,
            resultado.invalidated_runs,
            resultado.invalidated_sessions,
        )


async def _sweep_on_startup() -> None:
    """Cierra lo que quedó abierto de una corrida anterior.

    Best-effort: si la base no contesta, la API arranca igual y el barrido
    periódico lo reintenta.
    """
    try:
        await _sweep_once(startup=True)
    except Exception:
        logger.exception("el barrido inicial falló")


async def _reap_forever(interval_s: float) -> None:
    """Repite el barrido hasta que el lifespan cancele la task.

    `asyncio.CancelledError` no es `Exception`: la cancelación del shutdown
    atraviesa el `except` y la task termina limpia.
    """
    while True:
        await asyncio.sleep(interval_s)
        try:
            await _sweep_once()
        except Exception:
            logger.exception("el barrido periódico falló")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Primero el guard, antes de configurar nada: una configuración que da dos
    # verdades por sala no debería ni llegar a arrancar el barrido.
    _check_process_scope()
    configure_logging()
    await _sweep_on_startup()
    reaper = asyncio.create_task(
        _reap_forever(settings.reaper_interval_seconds), name="reaper"
    )
    yield
    reaper.cancel()
    with suppress(asyncio.CancelledError):
        await reaper
    # El estado de las salas vive en memoria: al apagar hay que cortar sus tareas
    # de vencimiento o quedan colgadas.
    await room_store.close()
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(title="Omnisapiens API", version="0.1", lifespan=lifespan)

# Un cuerpo enorme se corta en la puerta, antes de que lo parsee ningún modelo.
app.add_middleware(BodySizeLimitMiddleware)

# El frontend vive en otro puerto (5173), así que el navegador exige CORS: sin
# esto el `POST /auth/guest` ni sale del browser. Los orígenes salen de `.env`.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

errors.install(app)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(health.router)
app.include_router(leaderboard.router)
app.include_router(me.router)
app.include_router(rooms.router)
app.include_router(room_ws.router)
app.include_router(arcade_ws.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "Omnisapiens API", "version": "0.1"}
