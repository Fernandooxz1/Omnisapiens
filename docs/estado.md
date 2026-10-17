# Estado — Omnisapiens

> Memoria de sesión: el agente la lee al empezar. Corta a propósito, se poda.

## Dónde estamos

Backend en `backend/` (proyecto uv con CPython 3.12; FastAPI, Postgres 16 y Redis 7 por `docker compose`). Motor de juego, selector de preguntas, capa de datos **y la primera capa HTTP** están hechos y testeados: 7 modelos, migraciones `0001`/`0002`, **279 tests en ~3 s** contra Postgres real.

**Todavía no hay WebSocket.** Lo que sigue es el repositorio de preguntas (paso 5 del plan de capa de datos) y, de Fase 1, `GET /me` + `PATCH /me` para que el token sirva de algo.

Diseño acordado, leer antes de tocar datos o auth: **`/home/fernando/.opencode/plan/omnisapiens-capa-de-datos.md`**. Los 4 puntos ⚠️ están **confirmados** y aplicados: fila de `matches` al arrancar, desempate del ranking por quién alcanzó antes el puntaje, `UNIQUE` parcial de `nick` y host de la sala (`rooms.host_user_id`).

## Hecho

- [x] Repo, `.gitignore`, `.editorconfig`, `AGENTS.md`, `docker-compose.yml`, `Makefile`, `/health` con lifespan
- [x] `app/game/` (motor puro) + `app/services/questions.py` (selección sin repetición)
- [x] `models/`: las 7 tablas, con `MetaData` de nombres propios, enums por `CHECK` y único parcial de `nick`
- [x] Alembic async y migraciones `0001` + `0002`: `upgrade`/`downgrade`/`upgrade` sobre base limpia, DDL migrado idéntico al de los modelos y `make check-schema`
- [x] Tests contra Postgres real (`trivia_test` recreada por sesión, rollback por test con SAVEPOINT): constraints con motivo exigido, guardia de schema y harness, cada uno validado con sabotaje
- [x] Alcance real de `alembic check` medido: ve tablas, columnas, tipos, defaults, índices, unique y **FK**; es **ciego a los `CHECK`** en las 4 formas
- [x] Host de la sala: es **quien la crea**, en `rooms.host_user_id` (FK a `users` + índice), migración `0002`
- [x] Capa HTTP de entrada: `security/tokens.py` (JWT HS256) + `security/nicks.py` (limpieza, 1–16, lista de prohibidas), `api/deps.py`, `api/errors.py`, `POST /auth/guest` y CORS
- [x] `docs/mvp-plan.md` alineado: §5.4, §8 (tablas), §12 (auth y códigos de error), §14 (desempate), §6 (árbol) y §18 (tests)

## Próximos pasos

- [ ] Decidir si el nick es único **sin distinguir mayúsculas**: hoy `Ana` y `ana` son dos usuarios distintos (el índice es sobre `nick`). Ver "Trampas"
- [ ] Repositorio de preguntas (`RoundQuestion`, sin la respuesta correcta) + vistos en Redis con degradación
- [ ] Importador CSV/JSON + `cli.py` + 60 preguntas semilla
- [ ] `GET /me` y `PATCH /me` (con `get_current_user`, la versión obligatoria de la dependencia) y `DELETE /me` (borrado lógico)
- [ ] Pendiente de Fase 0: `README.md` con los cinco comandos de la sección 23
- [ ] `game/protocols.py` y `RoomStore` en memoria con lock por sala
- [ ] `ws/room_ws.py`: lobby, rondas, desempate, gracia de 20 s, revancha
- [ ] Arcade sobre WS + ranking + corte semanal en `America/Argentina/Buenos_Aires`
- [ ] `POST /rooms` + `GET /rooms/{code}` (el host ya tiene dónde guardarse)

## Después

- Fase 1: admin de preguntas y CI. Fases 2-4: partida completa y ranking. Fase 6: PWA, e2e, documentación.

## Decisiones tomadas y trampas (no re-descubrir)

- Molde de modelo: `Mapped[X]` decide el NOT NULL; `uuid4` en Python; `DateTime(timezone=True)` + `server_default=now()`; todo constraint con nombre propio; único parcial para el borrado lógico.
- Los valores permitidos de cada `CHECK` salen de `game/constants.py` y de los enums de `game/*_engine.py`: motor y base no pueden divergir sin que la migración lo delate.
- Un `CHECK` que evalúa a `NULL` **no viola nada**: para claves ausentes de un `jsonb`, `IS NOT DISTINCT FROM`, nunca `=`.
- Sin `relationship()` en los modelos, el ORM no deduce el orden de los INSERT: en los tests lo ordena `acepta()` (un flush por tabla); el día que el repositorio inserte filas relacionadas, va a tener el mismo problema.
- Alembic **nunca compara `CHECK`**: esas migraciones se escriben a mano y por eso existe la guardia de schema. Las FK sí las detecta.
- La verificación de una migración no es "mirar el archivo": se comparan inventarios de `pg_constraint`/`pg_indexes` de la base migrada contra el DDL de los modelos.
- Un test que pasa no dice nada por sí solo: lo que prueba es el sabotaje.
- Ojo con los tests que rompen dos reglas a la vez: el error que llega puede ser el de la otra. Aislar la fila inválida en vez de aflojar el `motivo`.
- El host de la sala es **el creador** (`rooms.host_user_id`), no "el primero que entra": la fila vive más que las conexiones. En los tests, `room()` pide el id de un host ya insertado (como `match()` pide sus dos jugadores).
- Una migración que agrega una columna `NOT NULL` sin default sobre una tabla con filas falla a propósito: en `0002` no hay host que inventarle a una sala vieja.
- `get_session` commitea al final del pedido y hace rollback si algo revienta: los endpoints **no** commitean. El borde del pedido es el borde de la transacción.
- El token se lee con `algorithms=[ALGORITHM]` explícito (sin eso, el `alg: none` clásico pasaría) y se atrapa `jwt.PyJWTError` entero: `InvalidTokenError` no cubre las fallas de clave o de algoritmo, que saldrían como 500.
- Sin `Authorization` el usuario es `None`, pero con un token **roto** es 401 y no un usuario nuevo: ignorarlo le entregaría al cliente una identidad distinta sin avisarle. La identidad la manda el token, no el body.
- Los tests de API usan la fixture `client` con `ASGITransport` y reemplazan `get_session` por la sesión del test: el pedido entra en la misma transacción y el rollback final lo deshace (sin eso, los tests de API ensuciarían la base y dependerían del orden).
- El formato de error es `{"error": {"code", "message"}}` para todo lo que tenga código propio **y** para el 422 de validación. El 404 de ruta desconocida sigue siendo el de FastAPI: nadie le pega a una ruta que no existe.
- **Trampa abierta**: el único de `nick` no distingue mayúsculas (`Ana` y `ana` conviven). Decisión pendiente: índice único funcional sobre `lower(nick)`, con migración `0003`.
- `JWT_SECRET` de dev tiene 18 bytes y PyJWT avisa (`InsecureKeyLengthWarning`): en prod tiene que tener 32 o más. Candidato a validación en `config.py` cuando exista `env != "local"`.
- Todo lo de frontend es de otra persona: acá solo se toca `backend/`.
- `docs/mvp-plan.md` se mantiene alineado con el código en el mismo paso: el plan es lo que lee la próxima sesión.
- La URL de la base **no** está en `alembic.ini`: sale de `.env` por `app.config.settings`. Un solo lugar donde se configura.
