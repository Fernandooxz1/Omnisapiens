# Estado — Omnisapiens

> Memoria de sesión. Corto a propósito: se poda. El agente lo lee al empezar y lo actualiza al avanzar.

## Dónde estamos
Motor de juego y selector de preguntas hechos y testeados (117 tests). Falta **toda la capa de datos**: modelos, Alembic y repositorios.

Diseño acordado: **`/home/fernando/.opencode/plan/omnisapiens-capa-de-datos.md`**. Fija el esquema, las decisiones irreversibles y el orden de implementación. Los 3 puntos ⚠️ quedaron **confirmados**: fila de `matches` al arrancar (3.2), desempate del ranking por quién alcanzó antes el puntaje (decisión 7) y `UNIQUE` parcial de `nick` (decisión 6).

## Hecho
- [x] Repo, `.gitignore`, `.editorconfig`, `AGENTS.md`, `docker-compose.yml` (Postgres 16 + Redis 7)
- [x] Proyecto uv con CPython 3.12: `pyproject.toml`, `.venv`, `.env.example` + `.env` real
- [x] `app/config.py`, `app/db.py`, `app/redis.py` y `/health` con lifespan y router (probado con Redis caído)
- [x] `Makefile`: `up/down/api/migrate/test/lint/fmt`; ruff y mypy en verde
- [x] `app/game/`: motor puro con invariantes (`answers`, `scoring`, `arcade_engine`, `match_engine`)
- [x] `app/services/questions.py`: selector puro, `Random` inyectado, estrategia observable
- [x] Commits `8eebea9` (motor y base) y `fe77e4c` (selector)
- [x] `models/base.py` (`MetaData` con convención de nombres), `models/user.py`, `models/question.py`; commit `e6756cb`
- [x] `users` y `questions` verificadas contra el Postgres real: 11 + 24 sondas de constraints, 0 fallas

## Próximos pasos (en orden, según el plan de capa de datos)
- [x] Confirmar los 3 puntos ⚠️ del plan
- [ ] `models/room.py`: `code` único con CHECK del alfabeto y `config` jsonb
- [ ] `models/match.py` + `models/match_round.py`: FKs, único `(match_id, round_index)`
- [ ] `models/arcade_run.py` + `models/arcade_answer.py`: los índices parciales del ranking
- [ ] Alembic async + migración inicial; `alembic check` limpio
- [ ] Fixtures de test contra Postgres real, con rollback por test
- [ ] `api/deps.py` (`get_session`) + `POST /auth/guest` con JWT y filtro de nicks
- [ ] Repositorio de preguntas (`RoundQuestion`, sin la respuesta correcta) + vistos en Redis
- [ ] Importador CSV/JSON + `cli.py` + 60 preguntas semilla
- [ ] `game/protocols.py` + `RoomStore` en memoria con lock por sala
- [ ] `ws/room_ws.py`: lobby, rondas, desempate, gracia de 20 s, revancha
- [ ] Arcade sobre WS + ranking + corte semanal en `America/Argentina/Buenos_Aires`

## Después (fases del plan)
- Fase 1: admin de preguntas y CI
- Fases 2-4: salas, partida 1v1 completa, arcade y ranking
- Fase 6: PWA, e2e y documentación

## Notas
- El frontend lo hará otra persona: acá solo se toca `backend/`.
- Cada paso se prueba (test, curl o navegador) antes de seguir.
- Comentarios con criterio senior (regla 13). No leer `docs/mvp-plan.md` entero: consultarlo por fragmento.
- El motor (`app/game/`) no depende de FastAPI, Postgres ni Redis, y no pregunta la hora: el tiempo y el azar se inyectan.
- Molde de modelo fijado en `models/user.py`: `Mapped[X]` decide el NOT NULL, `uuid4` en Python, `DateTime(timezone=True)` + `server_default=now()`, checks con nombre propio y único parcial para el borrado lógico.
- ruff 0.17 trae un preset estricto (814 reglas); el lock fija la versión, así que CI se comporta igual.
