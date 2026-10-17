# Estado — Omnisapiens

> Memoria de sesión. Corto a propósito: se poda. El agente lo lee al empezar y lo actualiza al avanzar.

## Dónde estamos
Fase 0 (esqueleto). Repo, infra y proyecto Python con uv listos; todavía no hay código de app en `backend/`.

## Hecho
- [x] Repo + config base (`.gitignore`, `.editorconfig`, `AGENTS.md`)
- [x] `docker-compose.yml` (Postgres 16 + Redis 7) levantando
- [x] `backend/.env.example` (plantilla de configuración)
- [x] Proyecto Python con uv (`pyproject.toml` + `.venv`, CPython 3.12)

## Próximos pasos (en orden)
- [ ] `backend/app/main.py`: app FastAPI mínima
- [ ] `backend/app/config.py`: leer variables de entorno (pydantic-settings)
- [ ] `backend/app/db.py`: conexión a Postgres (engine async)
- [ ] `backend/app/redis.py`: conexión a Redis
- [ ] `GET /health` que chequea Postgres y Redis
- [ ] Crear el `backend/.env` real (copiar de `.env.example`)
- [ ] Alembic configurado (migración inicial vacía)
- [ ] Test de humo de `/health`
- [ ] `Makefile` con `up/down/api/migrate/test`
- [ ] `README.md` con los comandos para levantar todo
- [ ] CI con ruff + mypy + pytest

## Después (fases del plan)
- Fase 1: auth invitado + importador de preguntas + admin + 60 preguntas
- Fase 2: salas y presencia
- Fase 3: partida 1v1 completa
- Fase 4: arcade y ranking

## Notas
- El frontend lo hará otra persona: acá solo se toca `backend/`.
- Cada paso se prueba (curl o navegador) antes de seguir.
- Comentarios con criterio senior (regla 13) y no leer `mvp-plan.md` entero.
