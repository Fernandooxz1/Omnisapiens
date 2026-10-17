# Estado — Omnisapiens

> Memoria de sesión. Corto a propósito: se poda. El agente lo lee al empezar y lo actualiza al avanzar.

## Dónde estamos
Fase 0 (esqueleto). La API arranca y lee configuración; falta conectarla a Postgres y Redis.

## Hecho
- [x] Repo + config base (`.gitignore`, `.editorconfig`, `AGENTS.md`)
- [x] `docker-compose.yml` (Postgres 16 + Redis 7) levantando
- [x] `backend/.env.example` + `.env` real
- [x] Proyecto Python con uv (`pyproject.toml` + `.venv`, CPython 3.12)
- [x] `backend/app/main.py`: app FastAPI con `GET /` (probada en `/docs`)
- [x] `backend/app/config.py`: `settings` con las 9 variables tipadas
- [x] `backend/app/db.py`: engine async + session factory (probado con `select 1`)
- [x] `backend/app/redis.py`: cliente async (`decode_responses`)
- [x] `Makefile`: `up/down/api/migrate/test/lint/fmt`
- [x] `make lint` en verde (ruff + mypy), `app/__init__.py` agregado
- [x] `lifespan` en `main.py` + `GET /health` con router propio (probado con Redis caído)
- [x] `app/game/`: motor puro con invariantes (`answers`, `scoring`, `arcade_engine`, `match_engine`)
- [x] `tests/` del motor: 100 tests en verde; `make lint` limpio

## Próximos pasos (en orden)
- [ ] `app/game/protocols.py`: dataclasses de los mensajes WS
- [ ] `app/services/questions.py`: selección con `RNG` inyectado y sin repetición
- [ ] `models/` + Alembic: tablas del plan, migración inicial
- [ ] `api/deps.py` con `get_session`
- [ ] `POST /auth/guest` + JWT de invitado
- [ ] Importador de preguntas CSV/JSON (`services/importer.py` + `cli.py`)
- [ ] `runtime/` de salas + `ws/room_ws.py`
- [ ] Arcade sobre WS + ranking en Redis
- [ ] `README.md` + CI + commit de Fase 0

## Después (fases del plan)
- Fase 1: auth invitado + importador de preguntas + admin + 60 preguntas
- Fase 2: salas y presencia
- Fase 3: partida 1v1 completa
- Fase 4: arcade y ranking

## Notas
- El frontend lo hará otra persona: acá solo se toca `backend/`.
- Cada paso se prueba (curl o navegador) antes de seguir.
- Comentarios con criterio senior (regla 13) y no leer `mvp-plan.md` entero.
- El motor (`app/game/`) no depende de FastAPI, Postgres ni Redis: se escribe y se prueba antes que las capas de arriba.
- ruff 0.17 trae un preset estricto (814 reglas); el lock fija la versión, así que CI se comporta igual.
