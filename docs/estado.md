# Estado — Omnisapiens

> Memoria de sesión: el agente la lee al empezar. Corta a propósito, se poda.

## Dónde estamos

Backend en `backend/` (proyecto uv con CPython 3.12; FastAPI, Postgres 16 y Redis 7 por `docker compose`). Motor de juego, selector de preguntas, banco de preguntas (Postgres + Redis), capa de datos, la capa HTTP (`/auth/guest`, `/me`, `/rooms`) y el importador están hechos y testeados: 7 modelos, migraciones `0001`–`0003`, **351 tests en ~16 s** contra Postgres y Redis reales.

**Todavía no hay WebSocket.** La identidad y las salas ya andan por HTTP: `/me` (perfil, nick, baja) y `/rooms` (crear + vista previa). Lo que sigue es el WS: `game/protocols.py` + `RoomStore` en memoria.

**Pausa acá:** `/rooms` quedó cerrado y verificado (351 tests, ruff/format/mypy en verde). `/me` ya está commiteado; los archivos de este paso (`routers/rooms.py`, `services/rooms.py`, `schemas/rooms.py`, `main.py`, `tests/test_rooms_api.py`) están sin commitear.

> Pendiente en `/rooms`: la vista previa devuelve `host_nick` y no "cuántos jugadores hay", porque la presencia vive en el WS (aún sin hacer). Se suma cuando exista `RoomStore`.

Diseño acordado, leer antes de tocar datos o auth: **`docs/capa-de-datos.md`**. Los 4 puntos ⚠️ están **confirmados** y aplicados: fila de `matches` al arrancar, desempate del ranking por quién alcanzó antes el puntaje, `UNIQUE` parcial de `nick` y host de la sala (`rooms.host_user_id`).

## Hecho

- [x] Base del repo: `.gitignore`, `.editorconfig`, `AGENTS.md`, `docker-compose.yml`, `Makefile`, `/health` con lifespan
- [x] `app/game/` (motor puro) + `app/services/questions.py` (selección sin repetición)
- [x] `models/`: las 7 tablas (nombres propios, enums por `CHECK`, único parcial de `nick`) y Alembic async con `0001`–`0003` sobre base limpia; `make check-schema` en verde
- [x] Tests contra Postgres real (`trivia_test` recreada por sesión, rollback por test con SAVEPOINT): constraints con motivo exigido, guardia de schema y harness, cada uno validado con sabotaje
- [x] Host de la sala = quien la crea (`rooms.host_user_id`); nick único sin distinguir mayúsculas (`lower(nick)`, parcial). `alembic check` resultó **ciego a los `CHECK`** (ve tablas, columnas, tipos, defaults, índices, unique y FK)
- [x] Capa HTTP de entrada: `security/tokens.py` (JWT HS256) + `security/nicks.py` (limpieza, 1–16, prohibidas), `api/deps.py`, `api/errors.py`, `POST /auth/guest` y CORS
- [x] Banco de preguntas (`services/question_bank.py`): candidatas publicadas de Postgres, `RoundQuestion` sin la respuesta correcta, y las vistas del arcade en Redis (tope 50, 24 h) con degradación si Redis no contesta
- [x] Importador (`services/importer.py`): parseo CSV/JSON + validación puros (un motivo por fila) y carga a Postgres con `ON CONFLICT (content_hash) DO NOTHING`; informe de importadas/duplicadas/rechazadas
- [x] `app/cli.py` (`import-questions`, `seed`) + `make seed` / `make import FILE=...` + 60 semilla publicadas (`seeds/questions.csv`, 10 por categoría) + `test_importer.py`
- [x] `docs/mvp-plan.md` alineado: §5.4, §8 (tablas), §12 (auth y códigos de error), §14 (desempate), §6 (árbol), §13 (import/semilla) y §18 (tests)
- [x] `GET /me` (perfil + pisa `last_seen_at`), `PATCH /me` (nick, reemite token) y `DELETE /me` (baja lógica) con `get_current_user`; `UserOut`/`AuthOut`/`NickUpdate` en `schemas/users.py`
- [x] `POST /rooms` (código de 6 sin ambiguos vía `secrets`, config por `field_validator` contra constants, host = creador, expira a `ROOM_IDLE_TIMEOUT_SECONDS`) + `GET /rooms/{code}` (preview, normaliza a mayúsculas, `ROOM_NOT_FOUND`)

## Próximos pasos

- [ ] `game/protocols.py` y `RoomStore` en memoria con lock por sala
- [ ] `ws/room_ws.py`: lobby, rondas, desempate, gracia de 20 s, revancha
- [ ] Barrendero de salas/matches viejas al arrancar (hoy `expires_at` se escribe pero nadie la marca `expired`)
- [ ] Arcade sobre WS + ranking + corte semanal en `America/Argentina/Buenos_Aires`
- [ ] `GET /me`: sumar mejor marca y últimas partidas cuando exista el ranking (Fase 4)
- [ ] `GET /rooms/{code}`: sumar `players` (presencia) cuando exista `RoomStore`
- [ ] Pendiente de Fase 0: `README.md` con los cinco comandos de la sección 23
- [ ] Página mínima para probar dos pestañas (la API sola ya se prueba con el smoke test de `/tmp`, fuera del repo)

## Después

- Fase 1: admin de preguntas y CI. Fases 2-4: partida completa y ranking. Fase 6: PWA, e2e, documentación.

## Decisiones tomadas y trampas (no re-descubrir)

- Molde de modelo: `Mapped[X]` decide el NOT NULL; `uuid4` en Python; `DateTime(timezone=True)` + `server_default=now()`; todo constraint con nombre propio; único parcial para el borrado lógico.
- Los valores permitidos de cada `CHECK` salen de `game/constants.py` y de los enums de `game/*_engine.py`: motor y base no pueden divergir sin que la migración lo delate.
- Un `CHECK` que evalúa a `NULL` **no viola nada**: para claves ausentes de un `jsonb`, `IS NOT DISTINCT FROM`, nunca `=`.
- Sin `relationship()` en los modelos, el ORM no deduce el orden de los INSERT: en los tests lo ordena `acepta()` (un flush por tabla); el día que el repositorio inserte filas relacionadas, va a tener el mismo problema.
- Alembic **nunca compara `CHECK`**: esas migraciones se escriben a mano y por eso existe la guardia de schema. Las FK sí las detecta, y un cambio en la **expresión de un índice** también (`remove_index` + `add_index`, con el `postgresql_where` intacto).
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
- El único de `nick` es funcional sobre `lower(nick)` y parcial: `Ana` y `ana` son el mismo nombre, y borrar una fila lógica lo libera. La guardia de schema compara texto de Postgres contra texto de Postgres (aplica el DDL de los modelos en un schema descartable y lo relee), así que un índice funcional no la rompe.
- El Redis de los tests es el de desarrollo **en otra base** (`:6379/1` contra `/0`), igual que `trivia_test`: un `FLUSHDB` de los tests no toca el juego en curso. Por eso `pytest` ahora necesita Redis levantado, no solo Postgres.
- `RoundQuestion` (lo que va al cliente) **no tiene** `correct_index` a propósito: la respuesta vive en `LoadedQuestion`, del lado del servidor. Un `hasattr` en el test lo vigila; si el campo vuelve al tipo, el test falla.
- El historial de vistas del arcade degrada: si Redis no contesta se juega igual, sin historial, y la advertencia queda en el log. La sala no usa Redis para eso: el estado de la partida en memoria ya evita repetir, y duplicarlo sería una segunda verdad.
- `JWT_SECRET` de dev tiene 18 bytes y PyJWT avisa (`InsecureKeyLengthWarning`): en prod tiene que tener 32 o más. Candidato a validación en `config.py` cuando exista `env != "local"`.
- Todo lo de frontend es de otra persona: acá solo se toca `backend/`.
- `docs/mvp-plan.md` se mantiene alineado con el código en el mismo paso: el plan es lo que lee la próxima sesión.
- La URL de la base **no** está en `alembic.ini`: sale de `.env` por `app.config.settings`. Un solo lugar donde se configura.
- El `content_hash` (clave del `UNIQUE` de `questions`) se calcula sobre el enunciado **normalizado**: NFKD sin diacríticos, minúsculas, sin signos, espacios colapsados. "¿Cuál es el río?" y "Cual es el rio" son la misma pregunta, así que el importador no puede cargar dos.
- El default del import es `draft` (§13.2); las 60 semilla entran `published` por flag (`make seed`), si no `candidates()` no las ve y no hay nada que jugar.
- `import_rows` frena el duplicado **dentro del mismo archivo** en Python (diccionario de hashes): dos filas iguales en un solo `INSERT` no las cubre el `ON CONFLICT`, que solo ve lo ya cargado.
- La CLI commitea a mano: `session_factory` no tiene el commit automático de `get_session` ("el borde del pedido es el borde de la transacción", pero acá no hay pedido).
- El importador repite en Python los `CHECK` (categoría, dificultad, 1–300) y suma las reglas que la base no puede expresar (opciones no vacías y distintas, comparadas con `casefold`): así el informe trae la fila y el motivo, en vez de reventar con un `IntegrityError` sin contexto.
- `get_current_user` **envuelve** a `get_optional_user` en vez de repetir la lectura del token: un solo camino de auth, y `POST /auth/guest` sigue usando la opcional.
- `rename_user` NO hace un SELECT previo: el único parcial de `users` es el árbitro, y entre chequear y escribir hay una carrera. Atrapa `IntegrityError` y hace `rollback` (mismo patrón que `create_guest`); el costo es que en los tests eso descarta lo escrito en la transacción del test, así que un PATCH rechazado se verifica por status, no por fila.
- `PATCH /me` reemite el token: el pase lleva el `nick` adentro y dejarlo viejo sería entregarle al cliente un pase que miente (aunque hoy la identidad se resuelva por `sub` contra la base).
- `DELETE /me` es baja lógica (`deleted_at`) y responde 204: el mismo dep que lee el token rechaza al usuario borrado (401) y el único parcial libera el nick sin borrar la fila.
- `GET /me` pisa `last_seen_at`: hasta este paso la columna se escribía una sola vez al crear el usuario y nunca más.
- El perfil y el pase viven en `schemas/users.py` (`UserOut`, `AuthOut`, `NickUpdate`); `auth.py` los reimporta para que `/me` no dependa de un módulo de alta.
- El código de sala se genera con `secrets` (no `random`): es la llave de la sala, tiene que ser impredecible. La colisión la arbitra el único de `code` con reintento, mismo patrón que el nick.
- La config de `POST /rooms` se valida en el schema con `field_validator` contra `ONLINE_ROUNDS_OPTIONS`/`ONLINE_SECONDS_OPTIONS`: el valor malo sale 422 `VALIDATION_ERROR` (mismo formato que el resto) y no un `IntegrityError` del `CHECK`.
- El `server_default="waiting"` de `rooms.status` no puebla el atributo en Python tras el `flush` (sin `eager_defaults`): por eso el POST devuelve solo `code`/`config` y el status se lee en el GET, que trae la fila desde la base.
