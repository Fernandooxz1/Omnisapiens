import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import errors
from app.api.routers import auth, health, me, rooms
from app.config import settings
from app.db import engine, session_factory
from app.logging_config import configure_logging
from app.redis import redis_client
from app.runtime.room_manager import room_store
from app.services.reaper import sweep
from app.ws import room_ws

logger = logging.getLogger(__name__)


async def _sweep_on_startup() -> None:
    """Cierra lo que quedó abierto de una corrida anterior.

    Best-effort: si la base no contesta, la API arranca igual y el barrido se
    reintenta en el próximo arranque.
    """
    try:
        async with session_factory() as session:
            resultado = await sweep(session)
    except Exception:
        logger.exception("el barrido inicial falló")
    else:
        logger.info(
            "barrido inicial: %d salas expiradas, %d partidas anuladas",
            resultado.expired_rooms,
            resultado.voided_matches,
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    await _sweep_on_startup()
    yield
    # El estado de las salas vive en memoria: al apagar hay que cortar sus tareas
    # de vencimiento o quedan colgadas.
    await room_store.close()
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(title="Omnisapiens API", version="0.1", lifespan=lifespan)

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
app.include_router(health.router)
app.include_router(me.router)
app.include_router(rooms.router)
app.include_router(room_ws.router)


@app.get("/")
def init() -> dict[str, str]:
    return {
        "name": "OMNIAPI",
        "version": "0.1",
        "description": "Prueba del metodo GET en localhost:8000/",
    }
