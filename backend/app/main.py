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
from app.runtime.room_manager import room_store
from app.services.reaper import sweep
from app.ws import arcade_ws, room_ws

logger = logging.getLogger(__name__)


async def _sweep_once(*, startup: bool = False) -> None:
    """Un barrido con lo que este proceso tiene vivo en este instante.

    Al arrancar no hay salas ni corridas en memoria, así que `live` queda vacío y
    toda fila abierta es de un proceso anterior; en régimen, `live` protege lo
    que está jugándose.
    """
    live = Live(rooms=room_store.live(), arcade_runs=live_arcade_runs.ids())
    async with session_factory() as session:
        resultado = await sweep(session, live=live)

    if startup or (
        resultado.expired_rooms
        or resultado.voided_matches
        or resultado.invalidated_runs
    ):
        logger.info(
            "%s: %d salas expiradas, %d partidas anuladas, %d corridas invalidadas",
            "barrido inicial" if startup else "barrido periódico",
            resultado.expired_rooms,
            resultado.voided_matches,
            resultado.invalidated_runs,
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
