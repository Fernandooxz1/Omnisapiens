# Estado — Omnisapiens

> Memoria de sesión: el agente la lee al empezar. Corta a propósito, se poda.

## Dónde estamos

Backend en `backend/` (proyecto uv con CPython 3.12; FastAPI, Postgres 16 y Redis 7 por `docker compose`). El motor de juego (`app/game/`) y el selector de preguntas están hechos y testeados (117 tests), **los 7 modelos de la base están escritos y verificados** y **la migración inicial ya aplica** (`alembic upgrade head` + `alembic check` limpio).

El schema ya no vive en un schema de prueba: existe por migración. Todavía **no hay tests contra la base**: la red de seguridad se construye en el paso que sigue.

Diseño acordado, leer antes de tocar la capa de datos: **`/home/fernando/.opencode/plan/omnisapiens-capa-de-datos.md`**. Los 3 puntos ⚠️ están **confirmados**: fila de `matches` al arrancar (3.2), desempate del ranking por quién alcanzó antes el puntaje (decisión 7) y `UNIQUE` parcial de `nick` (decisión 6).

## Hecho

- [x] Repo, `.gitignore`, `.editorconfig`, `AGENTS.md`, `docker-compose.yml`, `Makefile`, `/health` con lifespan
- [x] `app/game/` (motor puro: `answers`, `scoring`, `arcade_engine`, `match_engine`) + `app/services/questions.py`
- [x] `models/base.py` (convención de nombres) y `models/checks.py` (listas para los `CHECK`)
- [x] `models/`: `user.py`, `question.py`, `match.py` (`rooms`, `matches`, `match_rounds`), `arcade.py` (`arcade_runs`, `arcade_answers`)
- [x] 108 sondas de constraints contra el Postgres real, 0 fallas; commits `96f3b2e`, `a33e08c`, `b03e1f3` pusheados
- [x] `alembic.ini` + `env.py` async (URL desde `.env`, `compare_type` y `compare_server_default`) y migración `0001`
- [x] Verificación de la migración: `upgrade`/`downgrade`/`upgrade` sobre base limpia, `alembic check` limpio, y DDL migrado idéntico al de los modelos (79 columnas, 65 constraints, 23 índices); `make check-schema`
- [x] Alcance real de `alembic check` medido: ve tablas, columnas, tipos, defaults, índices, unique y **FK** (probe con `ondelete`); es **ciego a los `CHECK`** en las 4 formas (agregar, cambiar, renombrar, borrar)
- [x] `tests/conftest.py`: base real `trivia_test` (se recrea y migra una vez por sesión) y rollback por test con SAVEPOINT; 121 tests en ~1,5 s
- [x] Test de guardia `tests/test_schema_matches_models.py`: crea un schema descartable con el DDL de los modelos y compara inventario de constraints e índices contra la base migrada; probado con dos sabotajes (cambiar un `CHECK` y borrarlo) y 122 tests verdes

## Próximos pasos (orden del plan de capa de datos, §6)

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
- Alembic **nunca compara `CHECK`**: en la migración inicial salieron porque la tabla era nueva (se emite el `CREATE TABLE` completo del metadata), no porque los compare. Cambiar, renombrar, agregar o borrar un `CHECK` en un modelo produce "No new upgrade operations detected". Esas migraciones se escriben a mano (`drop_constraint` + `create_check_constraint`) y por eso hace falta el test de guardia de schema.
- Las FK sí se detectan, incluso un cambio de `ondelete` (aparece como `remove_fk` + `add_fk` y `alembic check` sale con 255).
- La verificación de la migración no es "mirar el archivo": se comparan inventarios del `pg_constraint`/`pg_indexes` del schema migrado contra el DDL de los modelos. Es el control que va a repetirse cuando haya cambios de schema.
- Los tests usan `trivia_test`, no SQLite, y cada uno corre en una transacción que se revierte (SAVEPOINT para los `commit()` del código bajo prueba). Antes de confiar en un fixture de aislamiento, sabotearlo (`rollback` → `commit`) y ver que el test que lo delata falle de verdad.
- `trivia_test` se **recrea** al empezar cada sesión de pytest: si alguien edita la base a mano para probar algo, el próximo `pytest` lo borra. Se ve bien, pero sorprende al principio.
- Un test que pasa no dice nada por sí solo: los dos sabotajes del test de guardia (cambiar un `CHECK` en el modelo y borrarlo en la base) son parte de la verificación, no un extra.
- La URL de la base **no** está en `alembic.ini`: sale de `.env` por `app.config.settings`. Un solo lugar donde se configura.
- `docs/mvp-plan.md` es referencia: no leerlo entero, consultarlo por fragmento.
