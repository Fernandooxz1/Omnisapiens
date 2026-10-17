from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import health
from app.db import engine
from app.redis import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(title="Omnisapiens API", version="0.1", lifespan=lifespan)

app.include_router(health.router)


@app.get("/")
def init():
    return {
        "name": "OMNIAPI",
        "version": "0.1",
        "description": "Prueba que de que el metodo GET para localhost:8000/ si funciona",
    }
