from fastapi import FastAPI

app = FastAPI(title="Omnisapiens API", version="0.1")


@app.get("/")
def init():
    return {"name": "OMNIAPI", "version": "0.1", "description": "Prueba que de que el metodo GET para localhost:8000/ si funciona"}





