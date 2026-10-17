# Estado — Omnisapiens

> Memoria de sesión: el agente la lee al empezar. Corta a propósito, se poda.

## Dónde estamos

Backend en `backend/` (proyecto uv con CPython 3.12; FastAPI, Postgres 16 y Redis 7 por `docker compose`). El motor de juego (`app/game/`) y el selector de preguntas están hechos y testeados (117 tests), y **los 7 modelos de la base están escritos y verificados**.

**Todavía no hay migración de Alembic ni tests**: las tablas solo existen en un schema de prueba. La red de seguridad se construye en el paso que sigue.

Diseño acordado, leer antes de tocar la capa de datos: **`/home/fernando/.opencode/plan/omnisapiens-capa-de-datos.md`**. Los 3 puntos ⚠️ están **confirmados**: fila de `matches` al arrancar (3.2), desempate del ranking por quién alcanzó antes el puntaje (decisión 7) y `UNIQUE` parcial de `nick` (decisión 6).

## Hecho

- [x] Repo, `.gitignore`, `.editorconfig`, `AGENTS.md`, `docker-compose.yml`, `Makefile`, `/health` con lifespan
- [x] `app/game/` (motor puro: `answers`, `scoring`, `arcade_engine`, `match_engine`) + `app/services/questions.py`
- [x] `models/base.py` (convención de nombres) y `models/checks.py` (listas para los `CHECK`)
- [x] `models/`: `user.py`, `question.py`, `match.py` (`rooms`, `matches`, `match_rounds`), `arcade.py` (`arcade_runs`, `arcade_answers`)
- [x] 108 sondas de constraints contra el Postgres real, 0 fallas; commits `96f3b2e`, `a33e08c`, `b03e1f3` pusheados

## Próximos pasos (orden del plan de capa de datos, §6)

- [ ] Alembic async + migración inicial revisada a mano; `alembic check` limpio
- [ ] Probar si `alembic check` **detecta un `CHECK` cambiado** (Alembic es flojo comparando checks)
- [ ] Fixtures con Postgres real (`trivia_test`): migraciones una vez por sesión, rollback por test
- [ ] Las 108 sondas se convierten en tests de pytest, uno por constraint
- [ ] `api/deps.py` (`get_session`) + `POST /auth/guest` con JWT y filtro de nicks
- [ ] Repositorio de preguntas (`RoundQuestion`, sin la respuesta correcta) + vistos en Redis
- [ ] Importador CSV/JSON + `cli.py` + 60 preguntas semilla
- [ ] `game/protocols.py` y `RoomStore` en memoria con lock por sala
- [ ] `ws/room_ws.py`: lobby, rondas, desempate, gracia de 20 s, revancha
- [ ] Arcade sobre WS + ranking + corte semanal en `America/Argentina/Buenos_Aires`

## Después

- Fase 1: admin de preguntas y CI. Fases 2-4: partida completa y ranking. Fase 6: PWA, e2e, documentación.

## Decisiones tomadas y trampas (no re-descubrir)

- Molde de modelo: `Mapped[X]` decide el NOT NULL; `uuid4` en Python; `DateTime(timezone=True)` + `server_default=now()`; todo constraint con nombre propio; único parcial para el borrado lógico.
- Los valores permitidos de cada `CHECK` salen de `game/constants.py` y de los enums de `game/*_engine.py`: motor y base no pueden divergir sin que la migración lo delate.
- Un `CHECK` que evalúa a `NULL` **no viola nada** (SQL trata "desconocido" como válido): para claves ausentes de un `jsonb`, `IS NOT DISTINCT FROM`, nunca `=`.
- El `uuid` de PK lo genera Python, así que un `INSERT` crudo por `psql` tiene que mandar el `id` a mano; el ORM lo hace solo.
- Las columnas de las rondas espejan `RoundRecord` de cada motor: los nombres no se traducen.
- Arcade: `ms` es obligatorio (mide la ventana agotada) y el estado `invalid` es el que saca una corrida del ranking.
- Los riesgos al escalar están anotados en el chat, no en el código: purgar salas y corridas viejas, GIN para `tags`, único en `email`, `TABLESAMPLE` para elegir preguntas. Nada urgente.
- Todo lo de frontend es de otra persona: acá solo se toca `backend/`.
- `docs/mvp-plan.md` es referencia: no leerlo entero, consultarlo por fragmento.
