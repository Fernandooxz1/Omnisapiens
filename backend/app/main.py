from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import errors
from app.api.routers import auth, health, me, rooms
from app.config import settings
from app.db import engine
from app.redis import redis_client
from app.runtime.room_manager import room_store
from app.ws import room_ws


@asynccontextmanager
async def lifespan(app: FastAPI):
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
def init():
    return {
        "name": "OMNIAPI",
        "version": "0.1",
        "description": "Prueba que de que el metodo GET para localhost:8000/ si funciona",
    }
