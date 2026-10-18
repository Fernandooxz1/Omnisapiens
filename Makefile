.PHONY: up down api web migrate seed import check-schema test cov lint fmt

up:
	docker compose up -d --wait

down:
	docker compose down

api:
	cd backend && uv run uvicorn app.main:app --reload

# Página de prueba en :5173 (el API sigue en :8000). Sin build ni dependencias.
web:
	cd backend && uv run python -m http.server 5173 --bind 127.0.0.1 --directory ../frontend/dev

# SPA real en :5173 (el API sigue en :8000).
front:
	cd frontend && npm run dev

migrate:
	cd backend && uv run alembic upgrade head

# Carga las 120 preguntas semilla (ya publicadas) desde backend/seeds/.
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

# El gate de calidad: tests con cobertura mínima. `test` queda rápido y sin
# umbral para poder correr un archivo suelto mientras se trabaja.
cov:
	cd backend && uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=85

lint:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app

fmt:
	cd backend && uv run ruff format .
