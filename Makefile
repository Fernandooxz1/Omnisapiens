.PHONY: up down api migrate test lint fmt

up:
	docker compose up -d --wait

down:
	docker compose down

api:
	cd backend && uv run uvicorn app.main:app --reload

migrate:
	cd backend && uv run alembic upgrade head

test:
	cd backend && uv run pytest

lint:
	cd backend && uv run ruff check . && uv run mypy app

fmt:
	cd backend && uv run ruff format .
