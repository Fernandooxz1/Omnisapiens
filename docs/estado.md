# Estado — Omnisapiens

> Memoria de sesión. Corto a propósito: se poda. El agente lo lee al empezar y lo actualiza al avanzar.

## Dónde estamos
Fase 0 (esqueleto). Repo e infra listos; el backend todavía no tiene código.

## Hecho
- [x] Repo git + `.gitignore` + `.editorconfig`
- [x] `AGENTS.md` con reglas de trabajo
- [x] `docker-compose.yml` (Postgres 16 + Redis 7) levantando
- [x] Plan copiado y actualizado a `backend/` y `frontend/`

## Próximos pasos (en orden)
- [ ] `backend/.env.example` con las variables de la sección 7 del plan
- [ ] Proyecto Python en `backend/` con uv (`pyproject.toml`, Python 3.12)
- [ ] `backend/app/main.py`: app FastAPI mínima
- [ ] `backend/app/config.py`: leer variables de entorno
- [ ] `backend/app/db.py`: conexión a Postgres
- [ ] `backend/app/redis.py`: conexión a Redis
- [ ] `GET /health` que chequea Postgres y Redis
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
