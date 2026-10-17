.PHONY: up down api migrate seed import check-schema test lint fmt

up:
	docker compose up -d --wait

down:
	docker compose down

api:
	cd backend && uv run uvicorn app.main:app --reload

migrate:
	cd backend && uv run alembic upgrade head

# Carga las 60 preguntas semilla (ya publicadas) desde backend/seeds/.
seed:
	cd backend && uv run python -m app.cli seed

# Carga un archivo propio: make import FILE=mis-preguntas.csv
import:
	cd backend && uv run python -m app.cli import-questions $(FILE)

# Guardarraíl: falla si los modelos y las migraciones se desincronizaron.
check-schema:
	cd backend && uv run alembic check

test:
	cd backend && uv run pytest

lint:
	cd backend && uv run ruff check . && uv run mypy app

fmt:
	cd backend && uv run ruff format .
