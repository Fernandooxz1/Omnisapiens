# Estado — Omnisapiens

> Memoria de sesión: el agente la lee al empezar. Corta a propósito, se poda.

## Dónde estamos

Backend en `backend/` (proyecto uv con CPython 3.12; FastAPI, Postgres 16 y Redis 7 por `docker compose`). El motor de juego (`app/game/`), el selector de preguntas y la capa de datos están hechos y testeados: los 7 modelos, la migración `0001` aplicada y **235 tests en ~4 s** contra Postgres real.

**Todavía no hay endpoints ni WebSocket**: lo que sigue es la capa HTTP (auth de invitado) y el repositorio de preguntas.

Diseño acordado, leer antes de tocar la capa de datos: **`/home/fernando/.opencode/plan/omnisapiens-capa-de-datos.md`**. Los 3 puntos ⚠️ están **confirmados**: fila de `matches` al arrancar (3.2), desempate del ranking por quién alcanzó antes el puntaje (decisión 7) y `UNIQUE` parcial de `nick` (decisión 6).

## Hecho

- [x] Repo, `.gitignore`, `.editorconfig`, `AGENTS.md`, `docker-compose.yml`, `Makefile`, `/health` con lifespan
- [x] `app/game/` (motor puro: `answers`, `scoring`, `arcade_engine`, `match_engine`) + `app/services/questions.py`
- [x] `models/`: las 7 tablas, con `MetaData` de nombres propios, enums por `CHECK` y único parcial de `nick`
- [x] 108 sondas de constraints contra el Postgres real, 0 fallas (commits `96f3b2e`, `a33e08c`, `b03e1f3`)
- [x] Alembic async + migración `0001`: `upgrade`/`downgrade`/`upgrade` sobre base limpia, DDL migrado idéntico al de los modelos (79 columnas, 65 constraints, 23 índices) y `make check-schema`
- [x] Alcance real de `alembic check` medido: ve tablas, columnas, tipos, defaults, índices, unique y **FK**; es **ciego a los `CHECK`** en las 4 formas
- [x] Tests contra Postgres real (`trivia_test` recreada por sesión, rollback por test con SAVEPOINT) y test de guardia de schema, validado con dos sabotajes
- [x] `tests/factories.py` + `tests/constraints.py`: las 108 sondas convertidas en 114 tests con nombre propio; validado dropeando los 70 `CHECK` (fallan esos 70 y ningún otro)

## Próximos pasos (orden del plan de capa de datos, §6)

- [ ] Reflejar en `docs/mvp-plan.md` (§8 y §14) las tres decisiones ⚠️ ya confirmadas: fila de `matches` al arrancar, desempate por quién alcanzó antes el puntaje, `UNIQUE` parcial de `nick`; ahí sigue el `char(6)` y el `ORDER BY MAX(ended_at) ASC` viejos
- [ ] `ROOMS.host_user_id` del plan no existe en el modelo: decidir si el host es "el que creó la sala" (hace falta la columna) o "el primero que entra" (no hace falta)
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
- **Sin `relationship()` en los modelos, el ORM no deduce el orden de los INSERT**: si una partida y sus jugadores van en el mismo flush, el INSERT de `matches` sale primero y la FK lo rechaza. En los tests lo ordena `acepta()` (un flush por tabla, en orden de `metadata.sorted_tables`); el día que el repositorio inserte filas relacionadas, va a tener el mismo problema.
- Técnica para validar todo el suite de constraints de una vez: dropear los `ck_%` de la base y correrlo. Deben fallar exactamente los tests que exigen un `CHECK` y ninguno más; si falla otro, ese test no medía lo que decía.
- `docs/mvp-plan.md` todavía describe el esquema viejo (§8) y el desempate viejo (§14): es deuda de documentación, el código va adelante.
- Ojo con los tests que rompen dos reglas a la vez: el error que llega puede ser el de la otra regla. Cuando pasa, aislar la fila inválida (`seconds=0, ms=0`) en vez de aflojar el `motivo`.
- La URL de la base **no** está en `alembic.ini`: sale de `.env` por `app.config.settings`. Un solo lugar donde se configura.
- `docs/mvp-plan.md` es referencia: no leerlo entero, consultarlo por fragmento.
