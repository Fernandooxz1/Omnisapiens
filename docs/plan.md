# Omnisapiens

Trivia online. Backend: FastAPI + Python (proyecto `uv`, CPython 3.12), PostgreSQL 16 +
Redis 7 por `docker compose`, WebSocket. Frontend: SvelteKit + TypeScript (lo hace otra
persona; acá solo se toca `backend/`).

> **Documento único.** Arriba, el **estado de sesión**: se lee al empezar y se poda en
> cada paso. Después, el **plan de implementación del MVP**; y al final, como
> **Anexo A**, el diseño de la **capa de datos y servicios**. El plan se consulta por
> fragmento (grep o `read` con `offset`/`limit`): no hace falta leerlo entero.

## Estado de sesión

### Dónde estamos

Backend en `backend/` (proyecto uv con CPython 3.12; FastAPI, Postgres 16 y Redis 7 por `docker compose`). Motor de juego, selector de preguntas, banco de preguntas (Postgres + Redis), capa de datos, la capa HTTP (`/auth/guest`, `/me`, `/rooms`), el importador, **el estado vivo de las salas**, **el WebSocket de sala** y **el barrendero** están hechos y testeados: 7 modelos, migraciones `0001`–`0003`, **448 tests en ~12 s** contra Postgres y Redis reales.

El canal en vivo de la sala está cerrado: `WS /ws/room/{code}?token=...` traduce §10.1 al `RoomStore` (auth por query, `hello`/`start`/`answer`/`rematch`/`ping`, corte por inactividad y cierre limpio). La vista previa de `/rooms/{code}` ya muestra `players` (presencia viva del `RoomStore`) y el barrendero cierra al arrancar lo que quedó abierto. Las opciones se barajan al servir (H-25), el token no se escribe en los logs (H-08) y el desempate tiene tope (H-24). El **corte 2 del arcade** (`ws/arcade_ws.py`) está cerrado: `WS /ws/arcade` con `start`/`answer`/`ping`, reloj de vencimiento, selección con historial de Redis y un solo escritor. Sigue la **persistencia** (corte 3).

**Pausa acá:** **auditoría cerrada (H-01..H-25), `README.md` escrito** y calidad con CI. Queda el **arcade: persistencia y ranking** (cortes 3–4).

Diseño acordado, leer antes de tocar datos o auth: **Anexo A** de este documento. Los 4 puntos ⚠️ están **confirmados** y aplicados: fila de `matches` al arrancar, desempate del ranking por quién alcanzó antes el puntaje, `UNIQUE` parcial de `nick` y host de la sala (`rooms.host_user_id`).

### Hecho

- [x] Base del repo, `models/` (7 tablas), Alembic `0001`–`0003` y guardia de schema
- [x] Capa HTTP: JWT, `/auth/guest`, `/me`, `/rooms`, CORS y errores con código
- [x] Banco de preguntas + importador + CLI + 60 semilla (`make seed` / `make import`)
- [x] Motores puros (`match_engine`, `arcade_engine`, `scoring`, `answers`, `questions`) y `runtime/room.py`
- [x] `runtime/arcade_session.py`: máquina pura de la corrida (start/serve/answer/expire) con protocolo §10.2 y tests
- [x] `ws/arcade_ws.py`: `WS /ws/arcade` con reloj, selección, historial de Redis y un solo escritor; tests con `ws_client.py`
- [x] `runtime/room_manager.py` + `ws/room_ws.py`: salas vivas, outbox, reloj, gracia, revancha y WS
- [x] Barrendero (`services/reaper.py`) y desalojo de salas muertas (H-03/H-04)
- [x] Auditoría P0/P1: H-01, H-02, H-05 y H-06 cerrados con tests y sabotajes
- [x] Calidad: `ruff select`, `mypy strict`, cobertura 92 % en `make cov` y CI (H-11)
- [x] Seguridad/observabilidad: logging y token fuera de logs (H-08/H-12), rate limit (H-09), salas vencidas (H-10), outbox y límites (H-13/H-15), 422 con campo (H-14), secretos largos (H-21)
- [x] Juego: opciones barajadas al servir (H-25) y tope del desempate (H-24)
- [x] P3 varios (H-16..H-20, H-23) y `README.md`

### Próximos pasos

> Auditoría **cerrada** al 2026-10-17 (`docs/observaciones.md`, H-01..H-25), con
> `README.md` y CI. Solo queda el arcade. Flujo: §9.3 · Protocolo: §10.2 ·
> API: §11 · Ranking y desempate: §14 + Anexo A (`arcade_runs`/`arcade_answers`).

**Arcade en 4 cortes** — cada uno con tests, no arrancar el siguiente sin cerrar el anterior:

- [x] **1. `runtime/arcade_session.py`**: máquina de estados **pura** por conexión sobre `game/arcade_engine`, con `now_ms`/`rng` inyectados y los mensajes de §10.2. Espejo de `runtime/room.py`: sin sockets, sin DB.
- [x] **2. `ws/arcade_ws.py`**: `WS /ws/arcade?token=...` (`start`/`answer`/`ping`, y `arcade_end` al terminar). Un solo escritor + `outbox` acotado + idle timeout, reusando `authenticate` y el patrón de `room_ws.py`; tests con `tests/ws_client.py`.
- [ ] **3. Persistencia**: fila `arcade_runs` al **arrancar** (`playing`, así `void` es alcanzable si el proceso muere) y `arcade_answers` + cierre al terminar. La base es de afuera: si falla, no matar la corrida en silencio (mismo criterio que el reloj de la sala).
- [ ] **4. Ranking**: sorted sets en Redis (global y semanal), desempate por **quién alcanzó antes ese puntaje** (§14, decisión A7), corte semanal en `America/Argentina/Buenos_Aires`; `GET /leaderboard/arcade?period=all|week` y `/leaderboard/arcade/me`; si Redis no contesta, el arcade juega igual sin ranking.

**Después del arcade:**

- [ ] `GET /me`: mejor marca y últimas partidas (depende del ranking).
- [ ] Barrendero periódico (no solo al arrancar): el mismo `sweep` en una task con intervalo. **Coordinar con el `RoomStore`**: una sala `waiting` con jugadores conectados no se puede marcar `expired` en la base.
- [ ] Página mínima para probar dos pestañas (la API sola ya se prueba con el smoke test de `/tmp`, fuera del repo).

### Después

- Fase 1: **admin de preguntas** (faltan los dos endpoints y devolver `X-Admin-Token` a la config). Fase 4: arcade y ranking (los 4 cortes de arriba). Fase 6: PWA, e2e y documentación. El CI ya está.

### Decisiones tomadas y trampas (no re-descubrir)

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
- **H-05**: `get_session` commitea al final del pedido, pero FastAPI cierra el `yield` **después** de emitir la respuesta: no protege al cliente. Los 4 endpoints de escritura (`/auth/guest`, `POST /rooms`, `PATCH`/`DELETE /me`) commitean ellos antes de responder; lo de `get_session` queda como red de seguridad para lo que se escriba sin commit explícito. El principio viejo ("el borde del pedido es el borde de la transacción") era falso.
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
- Este documento se mantiene alineado con el código en el mismo paso: el plan es lo que lee la próxima sesión.
- La URL de la base **no** está en `alembic.ini`: sale de `.env` por `app.config.settings`. Un solo lugar donde se configura.
- El `content_hash` (clave del `UNIQUE` de `questions`) se calcula sobre el enunciado **normalizado**: NFKD sin diacríticos, minúsculas, sin signos, espacios colapsados, así "¿Cuál es el río?" y "Cual es el rio" son la misma pregunta. El default del import es `draft` (§13.2) y las 60 semilla entran `published` por flag (`make seed`), si no `candidates()` no ve nada que jugar. `import_rows` frena el duplicado **dentro del mismo archivo** en Python (diccionario de hashes): el `ON CONFLICT` solo ve lo ya cargado. El importador repite en Python los `CHECK` y las reglas que la base no expresa (opciones no vacías y distintas con `casefold`), para que el informe traiga la fila y el motivo en vez de un `IntegrityError` sin contexto.
- La CLI commitea a mano: `session_factory` no tiene el commit automático de `get_session` ("el borde del pedido es el borde de la transacción", pero acá no hay pedido).
- `get_current_user` **envuelve** a `get_optional_user` en vez de repetir la lectura del token: un solo camino de auth, y `POST /auth/guest` sigue usando la opcional.
- `rename_user` NO hace un SELECT previo: el único parcial de `users` es el árbitro, y entre chequear y escribir hay una carrera. Atrapa `IntegrityError` y hace `rollback` (mismo patrón que `create_guest`); el costo es que en los tests eso descarta lo escrito en la transacción del test, así que un PATCH rechazado se verifica por status, no por fila.
- `PATCH /me` reemite el token: el pase lleva el `nick` adentro y dejarlo viejo sería entregarle al cliente un pase que miente (aunque hoy la identidad se resuelva por `sub` contra la base).
- `DELETE /me` es baja lógica (`deleted_at`) y responde 204: el mismo dep que lee el token rechaza al usuario borrado (401) y el único parcial libera el nick sin borrar la fila.
- `GET /me` refresca `last_seen_at` **como mucho una vez por minuto**: escribir en cada lectura era gratis en un test y caro con el frontend consultando seguido (H-23).
- El perfil y el pase viven en `schemas/users.py` (`UserOut`, `AuthOut`, `NickUpdate`); `auth.py` los reimporta para que `/me` no dependa de un módulo de alta.
- El código de sala se genera con `secrets` (no `random`): es la llave de la sala, tiene que ser impredecible. La colisión la arbitra el único de `code` con reintento, mismo patrón que el nick.
- La config de `POST /rooms` se valida en el schema con `field_validator` contra `ONLINE_ROUNDS_OPTIONS`/`ONLINE_SECONDS_OPTIONS`: el valor malo sale 422 `VALIDATION_ERROR` (mismo formato que el resto) y no un `IntegrityError` del `CHECK`.
- El `server_default="waiting"` de `rooms.status` no puebla el atributo en Python tras el `flush` (sin `eager_defaults`): por eso el POST devuelve solo `code`/`config` y el status se lee en el GET, que trae la fila desde la base.
- La sala viva (`runtime/room.py`) es **estado inmutable + transiciones puras**: recibe `now_ms` y lo ya cargado (la `LoadedQuestion`, el `match_id`), y devuelve estado nuevo + mensajes. La base, los sockets, el reloj y el lock son de afuera: se testea sin nada levantado.
- Los mensajes salen **por jugador** (`dict[user_id, mensajes]`), no como broadcast: `room_state` lleva `you` y `round_result`/`match_end` cambian de lado según quién mira. El error de un no sentado también viaja así.
- El host se sienta siempre en `A` (calza con `rooms.host_user_id` / `matches.player_a_id`); el invitado en `B`. Un tercero recibe `ROOM_FULL`.
- Al reanudar una ronda pausada se corre **todo** (arranque y respuestas ya dadas) por el hueco de la pausa: el tiempo medido de quien ya contestó no cambia y el reloj no gasta pausa. La gracia la fija el primer ausente.
- Repetir una respuesta es idempotente (no cambia nada): al reconectar, el cliente puede reenviarla.
- La última ronda de la partida emite `round_result` **y** `match_end` juntos: el resumen no necesita que el cliente recuerde la última revelación.
- El `RoomStore` es un `Protocol` y no una clase base (A3.6): el handler del WebSocket dependerá de la interfaz, así multi-instancia = otra implementación y el handler no se toca. El estado vivo es **uno por proceso** (`room_store`, mismo patrón que `engine` y `redis_client`) y se apaga en el lifespan, o sus tasks de vencimiento quedan colgadas.
- La partida se escribe en dos momentos y el manager **commitea a mano**: no corre dentro de un pedido, así que no hereda el commit de `get_session` (mismo criterio que la CLI). Si la escritura falla, el estado en memoria vuelve atrás: todavía nadie vio nada.
- La revancha la arranca el **segundo** pedido, y `_persist` escribe la fila nueva porque mira "la partida pasó a `playing`" en vez de "arrancó de cero": el rematch reusa el mismo bloque que `start`.
- El pool de preguntas se recorta al tramo de dificultad de la ronda **antes** de elegir: `next_round` revienta si la pregunta no entra en el tramo y `select` puede devolver una fuera de rango por sus fallbacks. Sin pregunta en el tramo, los dos reciben `NO_QUESTIONS` y la sala queda en `playing`: la fila abierta la cierra el barrendero, no el vacío.
- Los vencimientos son una task por sala que duerme hasta el próximo plazo (ronda o gracia) y se despierta con un `Event` cuando el estado cambia. Bajo el lock vuelve a chequear el plazo: entre despertar y tomar el lock, otra acción pudo resolver la ronda o servir la siguiente.
- El reloj **no muere con el primer error de base**: reintenta con backoff y, agotados `MAX_EXPIRY_FAILURES`, avisa `ROOM_CLOCK_DOWN` a los sentados y se rinde (una sala sin reloj tiene que cortar, no quedarse muda). `_tick` aísla *una* vuelta del reloj para que el `except` del loop envuelva exactamente una y el `else` resetee el contador. Reintentar es seguro porque `_step` ya dejó el estado en memoria coherente con Postgres. Si una transición queda **debiendo** la ronda siguiente (la consulta de `_pick` falló), `retry_serve` la hace servir en la vuelta siguiente: no alcanza con mirar `needs_next_round`, porque `NO_QUESTIONS` también lo deja en `True` y ahí hay que esperar, no girar en vacío.
- `room.start` sólo se acepta desde `WAITING` (H-06): con la sala `finished`, el único camino a otra partida es la revancha acordada; un `start` ahí la arrancaba salteando el acuerdo. Como `disconnect` devuelve la sala a `WAITING`, el flujo "se fue uno, entra otro, arrancamos" sigue andando.
- `GET /rooms/{code}` informa `players` desde el `RoomStore` (presencia viva), no desde la base: la fila de `rooms` no sabe de conexiones. Por eso el store global es el mismo objeto que usa el WebSocket.
- **La barra de calidad es un gate, no un adorno**: `ruff` con `select` (incluye `ASYNC`, `B`, `SIM`, `PT`), `mypy strict` y **92 % de cobertura** contra un umbral de 85 %. La cobertura **no** va en `addopts` a propósito: si estuviera, `pytest tests/test_room.py` fallaría por la cobertura global; `make test` corre rápido y `make cov` es el gate que usa el CI. `N818` queda ignorado: `NickTaken`/`InvalidTransition` se leen mejor sin el sufijo `Error`.
- El token del WS viaja en `?token=` (el navegador no deja headers en `new WebSocket`), y uvicorn loguea el handshake con la URL completa en `uvicorn.error`. `logging_config._HideWebSocketTokens` descarta los registros cuyos argumentos son `/ws/...` o contienen `?token=`; el resto de `uvicorn.error` (arranque, errores) sigue visible. El filtro va por logger, no por handler, porque uvicorn escribe esos renglones directamente en `uvicorn.access`/`uvicorn.error`.
- Las opciones se barajan **al servir** (`shuffle_options`) y `correct_index` se remapea en la misma copia: `RoundStart` y `match_rounds` ven el índice nuevo, y la pregunta guardada no se toca. Se barajan **índices**, no textos, para que un banco con opciones repetidas no desplace la respuesta. El `RoomStore` acepta `shuffle_served_options=False` para los tests que necesitan predecir la letra; producción lo deja en `True`.
- El desempate tiene tope (`MAX_TIEBREAK_ROUNDS = 3`): si tras tres rondas extra siguen empatados, la partida termina **en empate** (`FINISHED`, `winner=None`). `MatchState` sólo acepta un terminado sin ganador si `round_index >= config.rounds + MAX_TIEBREAK_ROUNDS`; antes del tope sigue siendo inválido. `MatchEnd` ya traducía `winner=None` a `"tie"`.
- **Rate limiting** (`api/rate_limit.py`): ventana fija de 60 s por IP y bucket en Redis (`INCR` + `EXPIRE`). Aplica al alta de invitado, a la vista previa y al WS. Si Redis no contesta se deja pasar y se loguea: el juego degrada, no se cae. En tests, un fixture autouse lo apunta al Redis de test con límites altos; los tests del corte lo bajan a mano (si no, toda la suite comparte el contador de la misma IP).
- Una sala **vencida no se revive** (`room_is_available`): `expired`, o `waiting` con `expires_at` pasado, dan 404 en la vista previa y `ROOM_NOT_FOUND` en el WS. `playing` y `finished` siguen abiertas para reconectar o pedir revancha.
- El **`outbox`** está acotado (`OUTBOX_MAX = 64`); si el cliente deja de leer, se descarta el mensaje más viejo en vez de bloquear la sala o crecer sin techo. El timeout de inactividad termina cortando esa conexión.
- Los bordes tienen tope de tamaño: cuerpo HTTP de 1 MB (`BodySizeLimitMiddleware`), `max_length` generoso en el schema del nick (el límite real de 16 sigue en `clean_nick`) y el importador inserta en lotes de 500. El 422 de validación incluye el campo (`loc[1:]`) para que el cliente sepa qué corregir.
- El reloj y el `sleep` se inyectan: el `FakeClock` de los tests no duerme, espera a que el test mueva la hora. Así una partida entera por vencimientos corre en milisegundos, sin esperar los 10–20 s reales de cada ronda.
- Los tests del `room_manager` pasan la **sesión del test** como factory (su `commit` se vuelve SAVEPOINT): igual que la fixture `client`, sin ensuciar `trivia_test`.
- La entrega es un `outbox` (cola) por jugador y no un callback: el vencimiento tiene que entregar sin que haya nadie esperando del otro lado, y el timer no conoce sockets. `disconnect` suelta esa cola: mensajes para un socket que ya no está no le sirven a nadie y se acumularían.
- `disconnect` recibe el `outbox` de **su** conexión y no toca la silla si esa cola ya no es la vigente (H-01): un corte silencioso deja al socket viejo vivo hasta el timeout, y cuando por fin cierra no puede desmontar al jugador que ya reconectó. El `outbox` es único por conexión (`asyncio.Queue` nueva por handler), así que la comparación por identidad alcanza: no hace falta un contador de generación.
- En los tests, `drain()` vacía la cola: dos `drain` seguidos para pedir dos tipos distintos descartan el que no se miró (un `uno(...)` que devuelve vacío). Un solo `drain` por tanda.
- El **barrendero** (`services/reaper.py`) corre al arrancar y cierra lo que nadie más cierra: una sala `playing` sin preguntas o un proceso que muere a mitad de partida dejan la fila abierta a propósito (§5.4). Son dos `UPDATE` con `returning` y un solo commit: salas `waiting` vencidas → `expired` y partidas `playing` más viejas que `STALE_MATCH_MINUTES` (15) → `void` con `ended_at`. Es idempotente y best-effort: si la base no contesta, la API arranca y el barrido se reintenta en el próximo arranque.
- **H-04 es un filtro, no un detalle**: el barrido de salas filtra `status='waiting'`; una sala `playing` puede tener `expires_at` viejo. Para que el filtro signifique algo, `rooms.status` se sincroniza con la sala viva: `playing` al arrancar/revancha, `finished` al cerrar, `waiting` cuando se va alguien de una sala terminada. Al arrancar la partida también se refresca `expires_at` con `rounds × (seconds + gracia) + 60 s`, así la vista previa no sigue mostrando el vencimiento del lobby.
- **H-03 se desaloja en `open`, no con otra tarea**: antes de crear una sala, `RoomStore` descarta las que no tienen `outbox`, no están `playing` y llevan más de `ROOM_IDLE_TIMEOUT_SECONDS` sin actividad (`last_activity_ms` se actualiza en cada transición). Como el mapa crece con las altas, una barrida por alta alcanza para que no crezca sin techo. Una entrada `expired` que se reabre se reemplaza por una sala fresca.
- `authenticate` (`api/deps.py`) es la **única puerta de auth**: la usan el header `Authorization` de HTTP y el `?token=` del WebSocket (el navegador no deja headers en `new WebSocket`). Dos transportes, una regla.
- El WS **acepta antes de autenticar**: un token malo tiene que poder recibir su `error` `AUTH_REQUIRED` por el socket (§12); si se cortara sin aceptar, el cliente no tendría por dónde enterarse. El rechazo de entrada (token, sala, sala llena) cierra con **1008**.
- El handler hace `join` **al conectar**, no al `hello`: la presencia tiene que existir cuando el navegador abre la sala (Fase 2). `hello` → `sync` repinta el estado completo y, de paso, la ronda en curso con su `ends_at` original (§10.3).
- `RoomStore.seated` existe por el tercero: el store le deja su `ROOM_FULL` en el `outbox` y el handler lo manda y **corta** la conexión. Sin esa consulta, una conexión sin silla queda viva sin tener a quién entregarle nada.
- El socket lo escribe **una sola corrutina** en régimen (la que drena el `outbox`); el lector pasa por el mismo lock para el `pong` y los errores que responde por su cuenta. Dos `send` en paralelo sobre el mismo socket no son seguros.
- Un corte de red silencioso no genera `disconnect`: lo detecta el **timeout de inactividad** (`ws_idle_timeout_seconds`, 45 s = 3 heartbeats del cliente) y recién ahí arranca la gracia. El handler cierra el socket al salir, así el cliente ve un cierre limpio y no un 1006.
- Códigos nuevos del WS: `BAD_MESSAGE` (sobre o `answer` mal formados) y `UNKNOWN_MESSAGE` (tipo que no conocemos). No se reusa `VALIDATION_ERROR`, que es del cuerpo HTTP.
- Los tests de WS **no usan `starlette.testclient`**: levanta la app en otro hilo y otro event loop y la sesión de asyncpg del test no cruza de loop (el rollback dejaría de ver lo escrito). `tests/ws_client.py` maneja el `scope: "websocket"` a mano en el loop del test, igual que `ASGITransport` con HTTP: mismo aislamiento (sesión y reloj falso) que el resto. Un `until(t)` saltea los mensajes que ya llegaron; el test pide por tipo, no por orden exacto.
- El arcade resuelve **en la primera respuesta**, no espera a nadie: `answer` devuelve `arcade_result` y deja la sesión pidiendo la próxima pregunta. Una respuesta repetida de la misma ronda llega cuando la ronda ya no está en vuelo y se rechaza con `ROUND_MISMATCH`.
- La transición del arcade devuelve `(state, effects, record)` y **no** acumula `RoundRecord` en el estado: el motor los entrega justamente para que el borde los guarde y el estado quede chico. `ArcadeEnd` sale con las posiciones en `None`: el ranking (corte 4) es quien las completa.
- El `seen` del arcade vive en el estado de la sesión: es lo que evita repetir pregunta dentro de una corrida, porque el motor no guarda historial a propósito. `serve(..., allow_repeat=True)` es la excepción de §9.4: con el pool agotado se repite y se sigue, con la advertencia en el log del llamador.
- El **WebSocket del arcade no tiene store global**: una conexión es una corrida, así que el estado vive en el handler. El único escritor es la corrutina que drena el `outbox`, y la cola lleva `(mensaje, id)`: hasta el `pong` pasa por ahí y conserva su correlación sin lock de escritura.
- El reloj y el `Random` del arcade entran por `ArcadeRuntime` (dependencia inyectable). El `sleep` del `FakeClock` calcula el vencimiento al llamarlo y resuelve un registro que nace vencido: cubre la carrera entre el `advance` del test y la tarea que recién se agenda. Está en `tests/clock.py`, compartido con la sala.
- La sesión SQL del WS del arcade es la del pedido (`SessionDep`) y se usa serializada por el lock de la corrida. La selección recorta el pool a la dificultad objetivo ±1 y solo abre todo el banco si no alcanza; la repetición queda como último recurso.
- El `start` del arcade es **una vez por conexión**: para otra corrida se reconecta. No hay `restart` en §10.2.

---

# Plan de implementación del MVP

> Pensado para que un agente o un desarrollador pueda empezar a construir sin preguntar nada más. La **capa de datos y servicios** está detallada en el Anexo A, al final.
> Idioma de la interfaz: **español**. Idioma del código, nombres de tablas, endpoints y variables: **inglés**.
> Todo el MVP corre **local** en la máquina del dueño. No hay presupuesto de infraestructura.

---

## 0. Resumen ejecutivo

Es un juego de trivia online de preguntas con 4 opciones. Tiene **dos modos**:

1. **Sala privada 1v1 por código.** Dos personas se conectan, se ve una pregunta a la vez, ambos responden de forma simultánea, y gana el que más puntos junta.
2. **Arcade (flash).** Un jugador solo responde preguntas cada vez más difíciles, con cada vez menos tiempo, hasta quedarse sin vidas. Genera un puntaje que compite contra un ranking global y uno semanal.

El backend es **autoritativo**: la respuesta correcta nunca se envía al navegador antes de que el jugador conteste. El transporte en tiempo real es **WebSocket**. La estética apunta a un juego de mesa/plástico: colores planos, bordes gruesos y sombras duras. Nada de gradientes decorativos, nada de emojis, nada de componentes genéricos.

---

## 1. Objetivos

- Tener un MVP jugable y divertido de trivia con dos modos: sala privada 1v1 y arcade.
- Que el código esté separado en capas de forma que agregar después "adiviná la canción" o "adiviná la película" no obligue a reescribir nada: el modelo de preguntas ya contempla media (imagen/audio) aunque el MVP no la use.
- Que el sistema sea escalable en el diseño pero simple en la ejecución: una sola instancia del backend alcanza para el MVP, y está preparado para escalar horizontalmente vía Redis Pub/Sub sin cambiar el modelo.
- Aprender. El proyecto es de aprendizaje personal: la prioridad es que sea claro, testeable y divertido. No hay objetivo de monetización.

## 2. Fuera de alcance del MVP

- Matchmaking público, salas abiertas o partidas con desconocidos.
- Salas de más de 2 jugadores.
- Modo por turnos con ruleta y coronas.
- Preguntas con imagen, audio o video (solo se dejan los campos preparados).
- Cuentas reales con login social o email.
- Chat de sala, amigos, invitaciones, notificaciones.
- Bots de relleno.
- Anuncios, pagos o cosméticos.
- Despliegue en la nube y dominio propio. Se deja todo listo para hacerlo, pero el MVP corre en local.
- Panel de administración completo de preguntas.

---

## 3. Decisiones cerradas

| Área | Decisión |
|---|---|
| Backend | Python 3.12 + FastAPI |
| Frontend | SvelteKit + TypeScript |
| Transporte en tiempo real | WebSocket propio con mensajes JSON |
| Autoridad del juego | Servidor autoritativo (nunca se manda la respuesta correcta antes de contestar) |
| Base de datos | PostgreSQL |
| Caché y estado de salas | Redis |
| Salas | 1v1, privadas, entrada por código de 6 caracteres |
| Bucle del modo online | Rondas simultáneas (ambos responden la misma pregunta a la vez) |
| Estructura de partida online | Configurable por el host: 3, 5 o 7 preguntas y 10, 20 o 30 segundos por pregunta |
| Arcade | 3 vidas, dificultad y tiempo progresivos |
| Categorías | 6 categorías clásicas, sorteadas al azar por pregunta |
| Banco de preguntas | Propias, generadas con asistencia de IA y curadas a mano; import por CSV/JSON |
| Acceso | Invitado primero, sin registro. Cuenta opcional queda para más adelante |
| Ranking arcade | Global histórico + semanal + mejor marca personal |
| i18n | Solo español, pero con todas las cadenas en un archivo de traducción desde el día uno |
| Abandono | El jugador desconectado tiene 20 segundos de gracia. Si no vuelve, la partida termina y gana el que quedó |
| Revancha | Incluida: botón que arranca una partida nueva en la misma sala |
| Chat | No hay, en ninguna forma |
| Bots | No hay |
| Sonido | Efectos cortos sí (acierto, error, tic tac, revelación, victoria, derrota). Música no |
| Monorepo | Sí, un solo repositorio |
| Assets | Dentro del repositorio, en `frontend/static/assets/` |
| Monetización | Ninguna en el MVP. Como muchísimo, publicidad mucho más adelante |
| Escala objetivo | Baja: dimensionado para no más de 100–200 jugadores concurrentes. Sin sobre-ingeniería |
| CI/CD | GitHub Actions. El dueño tiene cuenta de GitHub |
| Observabilidad | Logs estructurados en el MVP. Sentry queda preparado pero desactivado |
| Hosting | Fuera de alcance. Contenedores listos para desplegar cuando se decida |

---

## 4. Supuestos por defecto

Estos puntos no fueron definidos explícitamente y se resuelven así. Si el dueño del proyecto dice lo contrario, se cambia el plan.

1. **PostgreSQL y Redis corren en Docker Compose local.** Nada de servicios en la nube en el MVP.
2. **Entornos:** solo `local` ahora. La configuración se escribe desde el día uno con variables de entorno para que `staging` y `prod` funcionen después sin tocar código.
3. **Región futura de despliegue:** São Paulo (`GRU`) por latencia desde Argentina. Irrelevante en el MVP.
4. **Reconexión:** 20 segundos de gracia, con la partida congelada y un aviso visible al rival.
5. **Reacciones rápidas:** no se implementan. Si más adelante se quieren, se agregan como mensajes de WebSocket nuevos.
6. **Nick:** máximo 16 caracteres, se limpia y se filtra contra una lista corta de palabras prohibidas.
7. **Legal:** se incluyen páginas de términos y privacidad mínimas, más un endpoint de borrado de datos.
8. **Testing:** `pytest` para el motor de juego y la API, Playwright para una partida completa end-to-end.
9. **Escala:** se diseña para 100–200 conexiones concurrentes. No se hace particionado, ni sharding, ni colas distribuidas.
10. **Admin de preguntas:** comando de import por línea de comandos más una pantalla de listado protegida por token. No hay editor visual.
11. **Fuentes:** se autoalojan en `frontend/static/fonts/` para no depender de Google Fonts en tiempo de ejecución.
12. **Zona horaria del ranking semanal:** `America/Argentina/Buenos_Aires`, semana que empieza el lunes a las 00:00.

---

## 5. Arquitectura

```
┌──────────────────────────────────────────────────────────────┐
│  Navegador (SvelteKit + TypeScript, PWA)                     │
│  - Pantallas, estado de UI, animaciones, sonido              │
│  - No conoce ninguna respuesta correcta antes de contestar   │
└───────────────┬──────────────────────────┬───────────────────┘
                │ HTTP (JSON)              │ WebSocket (JSON)
                ▼                          ▼
┌──────────────────────────────────────────────────────────────┐
│  API — FastAPI (una o más instancias)                        │
│  - REST: sesión, salas, ranking, contenido, admin            │
│  - WS: /ws/room/{code} y /ws/arcade                          │
│  - Motor de juego en memoria, autoritativo                   │
│  - Temporizadores con el reloj del servidor                  │
└───────────────┬──────────────────────────┬───────────────────┘
                │                          │
                ▼                          ▼
┌────────────────────────┐   ┌─────────────────────────────────┐
│  PostgreSQL            │   │  Redis                          │
│  - usuarios            │   │  - estado de sala y presencia   │
│  - preguntas           │   │  - Pub/Sub entre instancias     │
│  - partidas y rondas   │   │  - ranking (sorted sets)        │
│  - corridas de arcade  │   │  - rate limiting                │
│  - mejor marca         │   │  - historial de preguntas vistas│
└────────────────────────┘   └─────────────────────────────────┘
```

### Principios

1. **El servidor decide todo.** El cliente pide, el servidor resuelve y notifica. El cliente nunca calcula puntajes ni decide si una respuesta es correcta.
2. **El motor de juego es código puro.** Las reglas viven en funciones sin acceso a base de datos, Redis ni red. Eso las hace testeables al 100% y reusables por los dos modos.
3. **Un modo, un flujo.** Online y arcade comparten el motor pero tienen flujos separados.
4. **Nada de estado de partida en la base de datos mientras la partida ocurre.** El estado vivo está en memoria y en Redis. De la partida se escribe solo el historial, y en dos momentos: la fila de `matches` **al arrancar** (con `status = playing`, para que `void` sea alcanzable si el proceso muere en el medio) y, al terminar, el `UPDATE` de esa fila más sus rondas en bloque. Cero escrituras por ronda.
5. **Escalado por Pub/Sub.** Cada instancia del backend atiende sus conexiones y publica los cambios de sala en Redis. Cualquier instancia puede reconstruir una sala desde Redis. Con una sola instancia todo funciona igual.

---

## 6. Estructura del monorepo

```
trivia/
├── README.md
├── .editorconfig
├── .gitignore
├── docker-compose.yml
├── Makefile
├── .github/
│   └── workflows/
│       └── ci.yml
├── backend/                          # Backend FastAPI
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── main.py               # app FastAPI, CORS, routers, lifespan
│   │   ├── config.py             # pydantic-settings, todo por variables de entorno
│   │   ├── db.py                 # engine async, session factory
│   │   ├── redis.py              # pool de Redis
│   │   ├── cli.py                # comandos: import-questions, seed, create-admin
│   │   ├── models/               # SQLAlchemy 2.0
│   │   │   ├── base.py           # MetaData con convención de nombres
│   │   │   ├── user.py
│   │   │   ├── question.py
│   │   │   ├── match.py          # rooms + matches + match_rounds (comparten el config)
│   │   │   └── arcade.py
│   │   ├── schemas/              # Pydantic v2 de entrada y salida
│   │   ├── security/
│   │   │   ├── tokens.py         # JWT de invitado
│   │   │   └── nicks.py          # normalización y filtro
│   │   ├── game/                 # MOTOR PURO, sin I/O
│   │   │   ├── constants.py
│   │   │   ├── match_engine.py
│   │   │   ├── arcade_engine.py
│   │   │   ├── scoring.py
│   │   │   ├── timers.py
│   │   │   └── protocols.py      # dataclasses de los mensajes
│   │   ├── runtime/              # ESTADO VIVO
│   │   │   ├── room.py
│   │   │   ├── room_manager.py
│   │   │   ├── arcade_session.py
│   │   │   └── pubsub.py
│   │   ├── services/
│   │   │   ├── questions.py      # selección, sin repetición (puro)
│   │   │   ├── question_bank.py  # candidatas de Postgres y vistas en Redis
│   │   │   ├── users.py          # alta del invitado
│   │   │   ├── leaderboard.py
│   │   │   ├── rooms.py
│   │   │   ├── reaper.py         # barrendero: vencidos al arrancar
│   │   │   └── importer.py       # CSV/JSON
│   │   ├── api/
│   │   │   ├── deps.py           # dependencias: sesión, usuario, admin
│   │   │   └── routers/
│   │   │       ├── auth.py
│   │   │       ├── me.py
│   │   │       ├── rooms.py
│   │   │       ├── leaderboard.py
│   │   │       ├── admin.py
│   │   │       └── health.py
│   │   ├── ws/
│   │   │   ├── room_ws.py
│   │   │   ├── arcade_ws.py
│   │   │   └── connection.py     # conexión con heartbeat y cierre limpio
│   │   └── i18n/
│   │       └── es.json
│   └── tests/
│       ├── conftest.py           # Postgres real (trivia_test) y rollback por test
│       ├── factories.py          # una fila válida por tabla, con overrides
│       ├── constraints.py        # acepta() / rechaza(motivo)
│       ├── test_match_engine.py
│       ├── test_arcade_engine.py
│       ├── test_scoring.py
│       ├── test_questions_service.py
│       ├── test_constraints_users.py
│       ├── test_constraints_questions.py
│       ├── test_constraints_match.py
│       ├── test_constraints_arcade.py
│       ├── test_schema_matches_models.py
│       ├── test_rooms_api.py
│       ├── test_room_ws.py
│       └── test_arcade_ws.py
├── frontend/                         # Frontend SvelteKit
│   ├── package.json
│   ├── svelte.config.js
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── Dockerfile
│   ├── static/
│   │   ├── manifest.webmanifest
│   │   ├── fonts/
│   │   ├── assets/
│   │   │   ├── icons/           # SVG propios: logo, 6 categorías, vidas, reloj, trofeo
│   │   │   └── sfx/             # efectos cortos
│   │   └── favicon
│   ├── e2e/
│   │   └── match.spec.ts
│   └── src/
│       ├── app.html
│       ├── app.css              # tokens + reset + utilidades
│       ├── routes/
│       │   ├── +layout.svelte
│       │   ├── +page.svelte               # inicio: elegir modo
│       │   ├── play/+page.svelte          # crear o unirse a sala
│       │   ├── room/[code]/+page.svelte   # lobby + partida online
│       │   ├── arcade/+page.svelte        # partida individual
│       │   ├── ranking/+page.svelte       # global + semanal
│       │   └── admin/preguntas/+page.svelte
│       └── lib/
│           ├── api/client.ts              # fetch tipado al backend
│           ├── api/ws.ts                  # cliente WebSocket con reconexión
│           ├── game/types.ts              # tipos de los mensajes
│           ├── stores/session.ts
│           ├── stores/match.ts
│           ├── stores/arcade.ts
│           ├── i18n/es.ts
│           ├── i18n/index.ts
│           ├── audio/sfx.ts
│           ├── components/
│           │   ├── Button.svelte
│           │   ├── AnswerTile.svelte
│           │   ├── CategoryBadge.svelte
│           │   ├── TimerRing.svelte
│           │   ├── PlayerPanel.svelte
│           │   ├── Scoreboard.svelte
│           │   ├── CodeInput.svelte
│           │   ├── NickInput.svelte
│           │   ├── Modal.svelte
│           │   ├── Toast.svelte
│           │   └── LifeStrip.svelte
│           └── design/tokens.ts
└── docs/
    └── plan.md
```

---

## 7. Entorno local

### `docker-compose.yml`

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: trivia
      POSTGRES_PASSWORD: trivia
      POSTGRES_DB: trivia
    ports:
      - "5432:5432"
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trivia"]
      interval: 5s
      timeout: 3s
      retries: 10

  cache:
    image: redis:7-alpine
    command: ["redis-server", "--appendonly", "yes"]
    ports:
      - "6379:6379"
    volumes:
      - cache_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  db_data:
  cache_data:
```

### Variables de entorno (`backend/.env`)

```
ENV=local
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://trivia:trivia@localhost:5432/trivia
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=dev-secret-de-32-bytes-o-mas-cambiar
JWT_TTL_DAYS=30
CORS_ORIGINS=http://localhost:5173
RECONNECT_GRACE_SECONDS=20
ROOM_IDLE_TIMEOUT_SECONDS=600
STALE_MATCH_MINUTES=15
WS_IDLE_TIMEOUT_SECONDS=45
RATE_LIMIT_GUEST_PER_MINUTE=10
RATE_LIMIT_ROOM_PER_MINUTE=60
```

### Comandos

```
make up            # levanta postgres y redis
make down          # los baja
make api           # uvicorn con reload en :8000
make web           # vite dev en :5173
make migrate       # alembic upgrade head
make seed          # carga preguntas de ejemplo
make import FILE=...   # importa un CSV de preguntas
make test          # pytest
make e2e           # playwright
make lint          # ruff + mypy + svelte-check
```

### Dependencias del backend (`pyproject.toml`)

- `fastapi`
- `uvicorn[standard]`
- `sqlalchemy[asyncio]`
- `asyncpg`
- `alembic`
- `pydantic` y `pydantic-settings`
- `redis` (cliente con soporte asyncio)
- `pyjwt`
- `python-multipart`
- `orjson`
- Desarrollo: `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `mypy`

### Dependencias del frontend

- `svelte` 5, `@sveltejs/kit` 2, `vite`, `typescript`
- `@vite-pwa/sveltekit` para el manifest y el service worker
- `@playwright/test` en desarrollo
- **No se usa ninguna librería de componentes de UI.** Los componentes se escriben a mano con CSS propio y variables de diseño. Tampoco se usa Tailwind: Svelte ya tiene CSS con alcance por componente.

---

## 8. Modelo de datos

PostgreSQL. Todo `snake_case`. UUID como clave primaria. Timestamps `timestamptz` en UTC.

La letra chica —constraints con nombre propio, índices parciales, `CHECK` que replican las reglas del motor— está en el **Anexo A**. Acá queda el mapa de las tablas; cuando el plan y el anexo difieran, manda el anexo.

### `users`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `nick` | varchar(16) | único **entre vivos y sin distinguir mayúsculas**: el índice es funcional sobre `lower(nick)` y parcial (`WHERE deleted_at IS NULL`). Con mayúsculas, `Ana` y `ana` convivían como dos usuarios y en una sala el nick es la única identificación; parcial, un usuario borrado lógico libera su nick |
| `is_guest` | boolean | default `true` |
| `email` | varchar(255) | nulo en MVP |
| `provider` | varchar(32) | nulo en MVP |
| `created_at` | timestamptz | |
| `last_seen_at` | timestamptz | |
| `deleted_at` | timestamptz | borrado lógico para el endpoint de borrado |

### `questions`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `category` | varchar(24) | `geography`, `history`, `science`, `art`, `entertainment`, `sports` |
| `difficulty` | smallint | 1 a 5 |
| `language` | varchar(8) | `es` |
| `prompt` | text | el enunciado |
| `options` | jsonb | array de exactamente 4 strings |
| `correct_index` | smallint | 0 a 3 |
| `explanation` | text | opcional, se muestra al revelar |
| `source` | text | procedencia, útil si se generó con IA |
| `status` | varchar(16) | `draft`, `published`, `archived` |
| `content_hash` | varchar(64) | hash normalizado del enunciado, para detectar duplicados |
| `media_type` | varchar(16) | **preparado para el futuro**: `none`, `image`, `audio` |
| `media_url` | text | **preparado para el futuro** |
| `tags` | text[] | |
| `created_at`, `updated_at` | timestamptz | |

Índices: `(status, category, difficulty)`, único en `content_hash`.

### `rooms`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `host_user_id` | uuid FK | quien creó la sala. El host es el creador, no "el primero que entra": la fila vive más que las conexiones, así que una reconexión no cambia de dueño la sala. Índice de FK |
| `code` | varchar(6) | único, sin caracteres ambiguos (sin `0`, `1`, `I`, `O`). varchar y no char: char rellena con espacios y vuelve sutiles las comparaciones |
| `config` | jsonb | `{"rounds": 5, "seconds": 20}`, con `CHECK` de forma y de valores permitidos |
| `status` | varchar(16) | `waiting`, `playing`, `finished`, `expired` |
| `created_at`, `expires_at` | timestamptz | |

El host es el único que elige la config y manda `start`, así que su identidad tiene que sobrevivir a la conexión: por eso está en la fila y no en la memoria del proceso. El `POST /rooms` la escribe en el mismo momento en que nace el código de sala.

### `matches`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `room_id` | uuid FK | nulo si la sala se purgó (`ON DELETE SET NULL`): el historial sobrevive |
| `player_a_id`, `player_b_id` | uuid FK | |
| `config` | jsonb | copia de la configuración usada, validada igual que la de `rooms` |
| `status` | varchar(16) | `playing`, `finished`, `abandoned`, `void` |
| `winner_id` | uuid | nulo en empate o anulada; si no, tiene que ser uno de los dos jugadores |
| `score_a`, `score_b` | integer | copia derivada del historial de rondas; las escribe solo el motor |
| `started_at`, `ended_at` | timestamptz | |

La fila se crea **al arrancar** la partida con `status = playing` y sin `ended_at`. Un barrendero al arrancar la API marca como `void` toda partida que siga en `playing` más vieja que N minutos.

### `match_rounds`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `match_id` | uuid FK | `ON DELETE CASCADE`: las rondas no tienen vida propia |
| `round_index` | smallint | 0-based; único junto con `match_id` |
| `question_id` | uuid FK | nulo si la pregunta se purgó (`ON DELETE SET NULL`) |
| `correct_index`, `difficulty`, `seconds` | smallint | copia de lo que se mostró: con estos tres la fila se puede auditar y recalcular años después |
| `a_choice`, `b_choice` | smallint | nulo si no contestó a tiempo |
| `a_ms`, `b_ms` | integer | milisegundos desde que se abrió la ronda; nulo si no hubo elección |
| `a_correct`, `b_correct` | boolean | no se derivan de `(choice, correct_index)`: fuera de la ventana hasta el acierto cuenta mal |
| `a_points`, `b_points` | integer | |
| `a_rejected`, `b_rejected` | varchar(24) | motivo del descarte (`outside_window`) o nulo |

Los nombres espejan `RoundRecord` del motor, sin traducir.

### `arcade_runs`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `user_id` | uuid FK | |
| `score` | integer | |
| `correct_count` | integer | |
| `max_difficulty` | smallint | |
| `longest_streak` | integer | nunca mayor que `correct_count` |
| `status` | varchar(16) | `playing`, `finished`, `invalid`. `invalid` es el estado que saca una corrida del ranking |
| `started_at`, `ended_at` | timestamptz | `ended_at` es nulo si y solo si está `playing` |

Índices: los tres del ranking (`(user_id, score desc)`, `(score desc)`, `(ended_at)`) son **parciales**, todos con `WHERE status = 'finished'`: una corrida en curso o dudosa no ocupa lugar en el índice.

### `arcade_answers`

Una fila por ronda, `ON DELETE CASCADE` desde la corrida y único `(run_id, round_index)`: `question_id` (nulo si se purgó), `difficulty`, `seconds`, `correct_index`, `chosen_index` (nulo si no contestó), `is_correct`, `ms` (nunca nulo: mide la ventana agotada), `points` y `rejected` (nulo o `outside_window`).

### Migraciones

Alembic con una migración inicial que crea todo. Nada de `create_all` en código de aplicación.

---

## 9. Reglas del juego

### 9.1 Constantes

```
CATEGORIES = geography, history, science, art, entertainment, sports
DIFFICULTY_MIN = 1
DIFFICULTY_MAX = 5

ONLINE_ROUNDS_OPTIONS = [3, 5, 7]      # default 5
ONLINE_SECONDS_OPTIONS = [10, 20, 30]  # default 20
ONLINE_BASE_POINTS = 100
ONLINE_TIME_BONUS_MAX = 50

ARCADE_LIVES = 3
ARCADE_SECONDS_START = 20
ARCADE_SECONDS_FLOOR = 5
ARCADE_SECONDS_STEP_EVERY = 3          # cada 3 aciertos, un segundo menos
ARCADE_DIFFICULTY_TIERS = [0, 4, 10, 18, 28]  # aciertos necesarios para dificultad 1..5
ARCADE_STREAK_BONUS_STEP = 10
ARCADE_STREAK_BONUS_MAX = 50

RECONNECT_GRACE_SECONDS = 20
ROOM_IDLE_TIMEOUT_SECONDS = 600
ROOM_CODE_LENGTH = 6
ROOM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # sin O, 0, I, 1
```

### 9.2 Modo online (sala privada 1v1)

**Lobby**

1. El host crea la sala desde `POST /rooms` y recibe un código de 6 caracteres. La sala queda en estado `waiting`.
2. El host comparte el código. El invitado entra y ambos abren `WS /ws/room/{code}`.
3. Cuando los dos están conectados, el host puede arrancar. El invitado también ve el estado de "esperando al host".
4. Si la sala queda `waiting` más de 10 minutos sin arrancar, expira.

**Ronda**

1. El servidor elige una pregunta publicada que no haya salido en la partida, de categoría aleatoria entre las 6, y de dificultad cercana al promedio que va subiendo con el índice de ronda. Tabla de dificultad por ronda: rondas 0–1 → dificultad 1–2, rondas 2–3 → 2–3, rondas 4–5 → 3–4, ronda 6+ → 4–5.
2. Envía a ambos jugadores, al mismo tiempo, un mensaje `round_start` con el índice de ronda, el enunciado, las 4 opciones, la categoría, la dificultad, el número de ronda y `ends_at` (instante de finalización según el reloj del servidor).
3. Cada jugador envía `answer` con el índice elegido. El servidor registra el tiempo usando su propio reloj, no el del cliente.
4. La ronda se resuelve cuando **los dos** contestaron, o cuando vence `ends_at`. Lo que ocurra primero.
5. Al resolver, el servidor calcula puntos y envía `round_result` a los dos con: la opción correcta, qué eligió cada uno, si acertó, los milisegundos, los puntos de la ronda, la explicación si existe, y el marcador acumulado.
6. Si un jugador no contesta, se cuenta como incorrecta y no suma.

**Puntaje de ronda**

```
ratio = clamp(1 - ms / (seconds * 1000), 0, 1)
puntos = BASE + round(TIME_BONUS_MAX * ratio)   # solo si acertó
```

Ejemplo con 20 segundos: acertar en 1 segundo da 148 puntos; acertar al límite da 100.

**Fin de la partida**

- Terminadas todas las rondas, gana el que más puntos tiene.
- Si hay empate, se juega **una ronda de desempate** con la mitad del tiempo configurado y una pregunta de dificultad 4 o 5. Se repite hasta que haya un ganador o hasta agotar `MAX_TIEBREAK_ROUNDS = 3`; agotado el tope, la partida termina en **empate** (`winner_id` nulo).
- El servidor envía `match_end` con el ganador, los puntajes, y el resumen ronda por ronda.

**Abandono y desconexión**

- Si un jugador se desconecta durante la partida, el otro ve un aviso claro: "Tu rival se desconectó, esperando reconexión".
- El reloj de la ronda se pausa. Arranca una ventana de 20 segundos.
- Si vuelve dentro de la ventana, la partida continúa desde el mismo estado.
- Si no vuelve, la partida termina con el jugador presente como ganador y la partida queda registrada como `abandoned`.
- Si se desconectan los dos, la partida queda como `void` y no cuenta para nadie.

**Revancha**

- Al terminar, ambos ven un botón de revancha. Cuando los dos lo aprietan, el servidor crea una partida nueva con la misma configuración en la misma sala y reparte preguntas nuevas.
- Si uno no aprieta, la sala vuelve a `waiting` y el host puede volver a jugar con el mismo código.

### 9.3 Modo arcade

**Corrida**

1. El jugador arranca desde `WS /ws/arcade`. El servidor crea una corrida en `playing`.
2. Arranca con 3 vidas, dificultad 1, racha 0, puntaje 0 y 20 segundos por pregunta.
3. Se envía `arcade_question` con el enunciado, las opciones, la categoría, la dificultad, los segundos disponibles, el número de aciertos y las vidas restantes.

**Progresión**

| Aciertos acumulados | Dificultad de la siguiente pregunta |
|---|---|
| 0 – 3 | 1 |
| 4 – 9 | 2 |
| 10 – 17 | 3 |
| 18 – 27 | 4 |
| 28+ | 5 |

| Segundos por pregunta | Condición |
|---|---|
| 20 | inicio |
| 19 | 3 aciertos |
| 18 | 6 aciertos |
| … | cada 3 aciertos baja 1 segundo |
| 5 | piso, no baja más |

**Puntaje**

```
puntos = BASE + round(TIME_BONUS_MAX * ratio) + min(STREAK_BONUS_STEP * streak, STREAK_BONUS_MAX)
```

donde `streak` es la cantidad de aciertos consecutivos **antes** de esta pregunta.

**Fin**

- Un error descuenta una vida. Si quedan vidas, sigue. Si llega a 0, la corrida termina.
- Una pregunta sin contestar se cuenta como error.
- Al terminar, el servidor guarda el puntaje y envía `arcade_end` con puntaje, aciertos, dificultad máxima, mejor racha, y la posición en el ranking global y semanal.
- El anti-trampa mínimo: los puntajes por pregunta se calculan siempre en el servidor con el reloj del servidor, y una corrida con tiempos imposibles (por ejemplo, respuestas de 0 ms repetidas) se marca como `invalid` y no entra al ranking.

### 9.4 Selección de preguntas (`services/questions.py`)

Reglas comunes:

- Solo se usan preguntas con `status = 'published'` y `language = 'es'`.
- Nunca se repite una pregunta dentro de la misma partida o corrida.
- En el arcade, además se evita repetir las últimas 50 preguntas que vio ese usuario, en un conjunto ordenado de Redis (`arcade:seen:{user_id}`, ordenado por cuándo se vieron, con caducidad de 24 horas). La sala no necesita esa memoria: el estado de la partida ya sabe qué preguntas salieron.
- **Si Redis no contesta, la partida sigue sin historial.** Se registra la advertencia y lo peor que pasa es repetir una pregunta: una caché caída no puede tumbar una partida que se podría jugar.
- **La respuesta correcta no viaja con la pregunta.** `RoundQuestion` (lo que se manda al cliente) no tiene campo `correct_index`: el índice se carga aparte, en `LoadedQuestion`, y solo lo ve el servidor.
- Estrategia de selección: se busca por categoría y dificultad en la base, se descartan las usadas en esta partida, y se elige al azar. Si el resultado queda vacío, se amplía el rango de dificultad en ±1 y, si sigue vacío, se ignora la categoría.
- **Si no hay preguntas suficientes, la partida no debe romperse.** Se permite repetir como último recurso y se registra una advertencia en los logs.

---

## 10. Protocolo WebSocket

Un solo formato de sobre para todo:

```json
{ "t": "tipo_de_mensaje", "id": "opcional-para-correlacionar", "d": { } }
```

- `t`: tipo de mensaje.
- `id`: opcional, para emparejar pedido y respuesta.
- `d`: datos.

Todos los tiempos absolutos se expresan como **milisegundos desde epoch en UTC**, y siempre los genera el servidor.

### 10.1 Salas: `WS /ws/room/{code}?token=...`

**Cliente → Servidor**

| `t` | `d` | Descripción |
|---|---|---|
| `hello` | `{}` | Handshake inicial. El servidor responde con `room_state`. |
| `start` | `{}` | Solo el host. Arranca la partida si hay 2 jugadores. |
| `answer` | `{"round": 0, "choice": 2}` | Respuesta del jugador. |
| `rematch` | `{}` | Pide revancha. |
| `ping` | `{}` | Heartbeat. |

**Servidor → Cliente**

| `t` | `d` | Descripción |
|---|---|---|
| `room_state` | `{"code","status","config","you":{"id","nick"},"players":[...],"match_id"}` | Estado completo de la sala. Se manda al entrar y cada vez que cambia. |
| `match_start` | `{"match_id","config","rounds_total"}` | Arranca la partida. |
| `round_start` | `{"round","question_id","prompt","options":["a","b","c","d"],"category","difficulty","ends_at","total_seconds"}` | **Sin la respuesta correcta.** |
| `opponent_answered` | `{"round"}` | El rival ya contestó. No revela qué eligió. |
| `round_result` | `{"round","correct_index","explanation","you":{"choice","ms","points","correct"},"opponent":{"choice","ms","points","correct"},"scores":{"you","opponent"}}` | Revelación. |
| `reconnect_pending` | `{"seconds_left"}` | El rival se desconectó. |
| `opponent_returned` | `{}` | El rival volvió. |
| `match_end` | `{"winner":"you\|opponent\|tie","scores":{...},"rounds":[...],"reason":"completed\|abandoned"}` | Fin de partida. |
| `rematch_waiting` | `{}` | El rival ya pidió revancha. |
| `error` | `{"code","message"}` | Errores. |
| `pong` | `{}` | Respuesta al ping. |

### 10.2 Arcade: `WS /ws/arcade?token=...`

**Cliente → Servidor**

| `t` | `d` |
|---|---|
| `start` | `{}` |
| `answer` | `{"round": 3, "choice": 1}` |
| `ping` | `{}` |

**Servidor → Cliente**

| `t` | `d` |
|---|---|
| `arcade_start` | `{"run_id","lives","seconds"}` |
| `arcade_question` | `{"round","prompt","options","category","difficulty","seconds","ends_at","score","lives","streak","correct_count"}` |
| `arcade_result` | `{"round","correct_index","explanation","you":{"choice","ms","points","correct"},"score","lives","streak","correct_count"}` |
| `arcade_end` | `{"run_id","score","correct_count","max_difficulty","longest_streak","rank_global","rank_weekly","personal_best","is_new_best"}` |
| `error` | `{"code","message"}` |
| `pong` | `{}` |

### 10.3 Comportamiento del cliente WebSocket

- Reconexión automática con retroceso exponencial: 0.5s, 1s, 2s, 4s, hasta 10s máximo.
- Al reconectar dentro de la ventana de gracia, manda `hello` y el servidor devuelve el estado completo, incluyendo la ronda en curso con su `ends_at` original.
- El cliente **nunca** decide el resultado de una ronda. Solo dibuja lo que el servidor manda.
- Heartbeat cada 15 segundos con `ping`/`pong`. Si no llega `pong` en 10 segundos, se considera caída la conexión.

---

## 11. API HTTP

Todas las respuestas en JSON. Los errores siguen el formato `{"error": {"code": "...", "message": "..."}}`.

### Sesión

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/auth/guest` | Body `{"nick": "opcional"}`. Crea o reutiliza un usuario invitado y devuelve `{"user": {...}, "token": "..."}`. |
| `GET` | `/me` | Usuario actual, su mejor marca y sus últimas partidas. |
| `PATCH` | `/me` | Cambiar el nick. |
| `DELETE` | `/me` | Borrado lógico de datos. |

### Salas

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/rooms` | Crea la sala. Body `{"rounds": 5, "seconds": 20}`. Devuelve `{"code": "K7M2QP", "config": {...}}`. |
| `GET` | `/rooms/{code}` | Vista previa: devuelve `code`, `config`, `status`, `host_nick` y `expires_at` (normaliza el código a mayúsculas). La cantidad de jugadores se suma cuando exista la presencia por WebSocket. |

### Ranking

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/leaderboard/arcade?period=all\|week&limit=50` | Lista con posición, nick, puntaje y fecha. |
| `GET` | `/leaderboard/arcade/me` | Posición y mejor marca del usuario actual, en ambos períodos. |

### Contenido y admin

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/admin/questions?status=&category=&difficulty=&q=&page=` | Listado paginado. Requiere `X-Admin-Token`. |
| `POST` | `/admin/questions/import` | Importa un CSV o JSON y devuelve un informe. Requiere `X-Admin-Token`. |
| `GET` | `/health` | Estado de la API, la base y Redis. |

### WebSocket

| Ruta | Descripción |
|---|---|
| `/ws/room/{code}?token=...` | Sala privada. |
| `/ws/arcade?token=...` | Arcade. |

---

## 12. Autenticación

- **Invitado primero.** `POST /auth/guest` crea un `users` con `is_guest = true` y un nick generado si no se manda uno (por ejemplo `Jugador4821`). Con un token válido en el header **no** da de alta a nadie: devuelve el mismo usuario con un token fresco, e ignora el nick que venga en el body (la identidad la manda el token).
- **Códigos de error** que devuelve hoy: `AUTH_REQUIRED` (401), `NICK_TAKEN` (409), `NICK_FORBIDDEN` y `NICK_LENGTH` (400), `ROOM_NOT_FOUND` (404), `VALIDATION_ERROR` (422, forma del body). El formato es el de §11: `{"error": {"code", "message"}}`.
- **El nick se limpia y se valida** en `security/nicks.py` (espacios de sobra, 1–16 caracteres, lista corta de palabras prohibidas que no ve leet ni homoglifos). El mismo módulo sirve para el `PATCH /me`.
- **`/me`**: `GET` devuelve el perfil y refresca `last_seen_at` como mucho una vez por minuto; `PATCH` cambia el nick (mismos códigos `NICK_*`) y devuelve un token fresco (el viejo lleva el nick viejo); `DELETE` es baja lógica (204) y a partir de ahí el token da 401 y el nick queda libre.
- **CORS:** los orígenes salen de `CORS_ORIGINS` y el frontend corre en otro puerto (`5173`), así que el navegador exige el middleware para poder llamar a la API.
- El token es un **JWT HS256** con `sub` (id del usuario), `nick`, `guest: true`, `iat` y `exp` a 30 días. Se firma con `JWT_SECRET`.
- El cliente lo guarda en `localStorage` y lo manda en el header `Authorization: Bearer ...`, o como query param `?token=` en los WebSocket (el navegador no permite headers en `new WebSocket`).
- No hay contraseñas, ni refresh tokens, ni sesiones en base de datos.
- El token vencido o inválido en una sala devuelve `error` con código `AUTH_REQUIRED` y el cliente manda al usuario al inicio.
- La cuenta opcional (Google, email) queda fuera, pero el modelo `users` ya tiene `email` y `provider` para cuando se agregue.

---

## 13. Banco de preguntas

### 13.1 Formato de importación (CSV)

Primera línea de encabezado, exactamente estas columnas:

```
category,difficulty,prompt,option_a,option_b,option_c,option_d,correct,explanation,source,tags
geography,2,¿Cuál es el río más largo de Sudamérica?,Paraná,Amazonas,Orinoco,Magdalena,B,El Amazonas recorre unos 6.400 km,manual,mundo;ríos
```

Reglas de validación:

- `category` debe ser una de las 6.
- `difficulty` entre 1 y 5.
- `prompt` no vacío, máximo 300 caracteres.
- Las 4 opciones no vacías y distintas entre sí.
- `correct` en `A`, `B`, `C` o `D`.
- `content_hash` calculado como SHA-256 del enunciado normalizado (minúsculas, sin signos, sin espacios repetidos).
- Filas con `content_hash` ya existente se omiten y se informan como duplicadas.
- El informe final dice: cuántas se importaron, cuántas se omitieron y por qué.

El import por JSON acepta un array de objetos con las mismas claves.

`make seed` carga `backend/seeds/questions.csv` (60 preguntas, 10 por categoría) y las deja **`published`**: son curadas a mano, no la salida de un generador que haya que revisar. El importador en sí usa `draft` por defecto, como pide §13.2; `make import FILE=...` acepta `--status` para cambiarlo.

### 13.2 Curación

- Las preguntas generadas con IA entran como `draft`.
- Un humano las revisa y las pasa a `published`.
- Para el MVP se recomienda un mínimo de **20 preguntas por categoría y por dificultad**, es decir 6 × 5 × 20 = 600 preguntas. Se puede arrancar con menos y escalar por tramos: primero dificultad 1 a 3, después 4 y 5.
- El campo `source` guarda la procedencia, y `explanation` se muestra al revelar la respuesta.

### 13.3 Preparado para el futuro

Cuando se agregue "adiviná la canción" o "adiviná la película", el cambio es:

- Nueva categoría de contenido y nuevos tipos de pregunta, cosa que ya soportan `media_type` y `media_url`.
- El motor de juego no cambia: sigue siendo elegir 1 de 4 opciones.
- Lo único que se agrega es subir archivos a `static/assets/media/` o a un bucket, y que la tarjeta de pregunta sepa renderizar un reproductor de audio o una imagen.

---

## 14. Ranking

- **Global histórico:** por cada usuario, su mejor `score` de todas las corridas válidas. Ordenado descendente. El empate se resuelve por **el momento más temprano en que ese jugador alcanzó ese puntaje**: quien llegó antes al mismo número va primero. (No por `MAX(ended_at)`, que significa "el que jugó por última vez hace más tiempo va primero": arbitrario y se mueve solo.)
- **Semanal:** mismo criterio pero solo corridas terminadas desde el lunes 00:00 en `America/Argentina/Buenos_Aires`. Se puede materializar en un sorted set de Redis, pero para el MVP un `SELECT` alcanza y es más simple de entender.
- **Mejor marca personal:** máximo de las corridas del usuario.
- El ranking se refresca al abrir la pantalla. No hay push en vivo en el MVP.

Consulta base. El `DISTINCT ON` elige, por usuario, su corrida de mayor puntaje y, entre las que empatan, la más temprana; después reordena esa lista:

```sql
SELECT * FROM (
  SELECT DISTINCT ON (u.id)
         u.id, u.nick, r.score AS best, r.ended_at AS achieved_at
  FROM arcade_runs r
  JOIN users u ON u.id = r.user_id
  WHERE r.status = 'finished'
    AND u.deleted_at IS NULL
    -- AND r.ended_at >= :since   -- solo en el ranking semanal
  ORDER BY u.id, r.score DESC, r.ended_at ASC
) AS mejor
ORDER BY best DESC, achieved_at ASC
LIMIT :limit;
```

---

## 15. Sistema de diseño

### 15.1 Reglas duras

Estas reglas no se negocian. Son lo que separa el juego de "una app genérica generada por IA".

1. **Cero gradientes decorativos.** Ningún `linear-gradient` ni `radial-gradient` en fondos, botones o tarjetas. Solo colores planos.
2. **Cero emojis en la interfaz.** Todos los íconos son SVG propios.
3. **Sombras duras.** `box-shadow: 4px 4px 0 0 var(--ink)`, sin desenfoque. Se prohibe `blur`.
4. **Bordes gruesos.** `border: 2.5px solid var(--ink)` en todo elemento interactivo.
5. **Toda superficie interactiva se puede presionar.** Al hacer clic se desplaza 3 px hacia abajo y a la derecha, y su sombra se reduce a 1 px. Eso da la sensación de chapa plástica.
6. **Nada de `border-radius` de 20 px en todo.** Radios contenidos: 10 px en botones, 14 px en tarjetas, y `999px` solamente en los badges de categoría.
7. **La tipografía se elige, no se hereda.** Nada de la fuente por defecto del sistema.
8. **El color de categoría manda.** El badge y el acierto usan el color de la categoría para que el ojo lo lea de un golpe.
9. **Cero animaciones de entrada por scroll.** La animación se usa para feedback de acción, no para decorar.
10. **Accesibilidad mínima obligatoria.** Foco visible con contorno del color de marca, contraste AA en texto, y todo jugable con teclado: números `1` a `4` para responder y `Enter` para confirmar.

### 15.2 Tokens

```css
:root {
  /* Tinta y papel */
  --ink:        #101828;
  --ink-2:      #344054;
  --ink-3:      #667085;
  --paper:      #FCF8F0;
  --paper-2:    #F2EADF;
  --white:      #FFFFFF;

  /* Semánticos */
  --correct:      #2FA36B;
  --correct-dark: #1E7A4D;
  --wrong:        #E14B4B;
  --wrong-dark:   #A32F2F;
  --brand:        #2F6BFF;
  --brand-dark:   #1E4FD1;
  --gold:         #D99B1C;

  /* Categorías: un color plano saturado por cada una */
  --cat-geography:     #2E9E5B;
  --cat-history:       #C77B2E;
  --cat-science:       #2A6FD6;
  --cat-art:           #8A4FD3;
  --cat-entertainment: #E0498F;
  --cat-sports:        #1E9E9E;

  /* Formas */
  --r-sm: 10px;
  --r-md: 14px;
  --r-full: 999px;
  --border-w: 2.5px;
  --shadow-hard: 4px 4px 0 0 var(--ink);
  --shadow-press: 1px 1px 0 0 var(--ink);

  /* Espaciado: escala de 4 */
  --s-1: 4px;  --s-2: 8px;  --s-3: 12px; --s-4: 16px;
  --s-5: 24px; --s-6: 32px; --s-7: 48px; --s-8: 64px;

  /* Tipografía */
  --font-display: "Bricolage Grotesque", system-ui, sans-serif;
  --font-ui: "Instrument Sans", system-ui, sans-serif;
}
```

Tipografías autoalojadas en `frontend/static/fonts/` en formato `woff2`, con `font-display: swap`. La display se usa en títulos, marcadores y números grandes, siempre en peso 800. La de UI se usa en todo el texto común.

### 15.3 Componentes

| Componente | Qué es |
|---|---|
| `Button` | Variantes `primary`, `secondary`, `ghost`, `danger`. Tamaños `md` y `lg`. Siempre con borde grueso y sombra dura. |
| `AnswerTile` | La opción de respuesta. Estados: `idle`, `selected`, `correct`, `wrong`, `disabled`. Es el componente más importante de la pantalla de juego. Alto mínimo 64 px en móvil, texto grande, y una tecla numérica visible en un extremo. |
| `CategoryBadge` | Badge pill con el color de la categoría, el ícono propio y el nombre. |
| `TimerRing` | Aro de cuenta regresiva. Cambia a color de alerta en los últimos 5 segundos y hace un pulso por segundo. |
| `PlayerPanel` | Nombre, marcador y estado del jugador (`respondiendo`, `esperando`, `desconectado`). |
| `Scoreboard` | Marcador entre los dos jugadores, con el que va ganando destacado. |
| `CodeInput` | Campo de 6 casillas para el código de sala, navegable con teclado, sin caracteres ambiguos. |
| `NickInput` | Campo de nick con contador y validación. |
| `Modal` | Confirmaciones y ajustes. Fondo oscuro plano, sin blur. |
| `Toast` | Avisos breves. |
| `LifeStrip` | Vidas del arcade con iconos SVG. |

### 15.4 Sonido

Efectos cortos en `static/assets/sfx/`, en formato `.mp3` o `.ogg` y de menos de 60 KB:

`tick`, `reveal`, `correct`, `wrong`, `match_start`, `match_win`, `match_lose`, `best_score`.

El audio debe ser CC0 o de producción propia. Se inicializa después de la primera interacción del usuario, y hay un interruptor de silencio persistido en `localStorage`.

### 15.5 Pantallas

1. **Inicio** — marca propia, dos botones grandes: "Jugar con un amigo" y "Arcade". Debajo, un enlace de ranking y el nick actual.
2. **Jugar** — dos bloques: "Crear sala" con la elección de rondas y segundos, y "Unirme con un código".
3. **Lobby** — código gigante y copiable, los dos jugadores, y el botón de arrancar para el host.
4. **Partida** — la pantalla principal. Arriba el marcador y el temporizador, al medio la pregunta, abajo las 4 opciones. Al responder, la opción elegida se marca y se muestra "esperando al rival".
5. **Revelación** — dentro de la misma pantalla: la correcta se pinta, la incorrecta se pinta, y aparece el puntaje ganado con una animación breve.
6. **Fin de partida** — ganador, marcador, resumen ronda por ronda, y botón de revancha.
7. **Arcade** — misma pantalla de juego pero con vidas, racha y puntaje acumulado, y sin rival.
8. **Fin de arcade** — puntaje, si es nuevo récord, posición en el ranking global y semanal, y botón de volver a jugar.
9. **Ranking** — pestañas "Global" y "Semanal", con la lista y la fila propia destacada.
10. **Admin de preguntas** — listado con filtros, y carga de archivo.

---

## 16. Frontend

### 16.1 Responsive

- Diseño **mobile first**, vertical, pensado para jugar con una mano.
- Ancho máximo de contenido: 480 px, centrado, en cualquier pantalla.
- Sin scroll en la pantalla de partida: la pregunta y las 4 opciones entran en el viewport.
- Áreas táctiles de 44 px como mínimo.
- En escritorio, la misma columna centrada, con las teclas `1`–`4` activas.

### 16.2 Estado

- `sessionStore`: usuario, token, nick, sonido. Persistido en `localStorage`.
- `matchStore`: máquina de estados del modo online. Estados: `idle`, `connecting`, `lobby`, `playing`, `revealing`, `ended`, `opponent_away`.
- `arcadeStore`: máquina de estados del arcade. Estados: `idle`, `connecting`, `answering`, `revealing`, `ended`.
- `ws.ts`: cliente de WebSocket con reconexión, heartbeat, y un `EventTarget` propio o stores derivados para que la UI se suscriba.
- Toda la lógica de puntaje es de solo lectura en el cliente. Si el cliente tiene que mostrar puntos, los muestra porque el servidor se los mandó.

### 16.3 PWA

- `manifest.webmanifest` con nombre, íconos de 192 y 512 px, `display: standalone`, `theme_color` igual a `--ink` y `background_color` igual a `--paper`.
- Service worker generado por `@vite-pwa/sveltekit` en modo `generateSW`, con `navigateFallback`.
- El juego **no** funciona offline. El service worker solo cachea el app shell y los assets estáticos.

---

## 17. i18n

- Un archivo `frontend/src/lib/i18n/es.ts` con todas las cadenas, y un `index.ts` que exporta una función `t(clave, params)`.
- En el backend, `backend/app/i18n/es.json` para los mensajes de error que se muestran al usuario.
- **Regla:** ninguna cadena visible se escribe directamente en un componente.
- Solo se carga `es`. La estructura queda lista para agregar `en` y `pt` más adelante.
- Los textos de las preguntas viven en la base de datos con su campo `language`.

---

## 18. Testing

### Backend

- `test_match_engine.py` y `test_arcade_engine.py`: pruebas puras del motor. Casos obligatorios: acierto rápido, acierto al límite, error, sin respuesta, empate y desempate, progresión de dificultad y de tiempo, corte por vidas.
- `test_scoring.py`: tabla de valores exacta para que el puntaje no se rompa al refactorizar.
- `test_questions_service.py`: que nunca se repita una pregunta dentro de una partida, que respete la dificultad, y que no explote si no hay preguntas suficientes.
- `test_constraints_*.py`: **un test por regla de la base**, contra un Postgres real y exigiendo el constraint que corresponde. Nada de SQLite: no tiene `jsonb`, ni índices parciales, ni `CHECK` con regex.
- `test_nicks.py` y `test_tokens.py`: la seguridad sin HTTP. La lista de palabras prohibidas se recorre entera, y del token se prueba lo que importa: que lo firmado se lee, y que lo tocado, lo vencido y lo firmado por otro no.
- `test_auth_api.py`: `POST /auth/guest` con `httpx` contra la base real, incluida la reutilización del usuario cuando el token es válido y el rechazo cuando no lo es.
- `test_question_bank.py`: candidatas contra Postgres real, el tipo que va al cliente sin la respuesta, las vistas contra Redis real (caducidad y tope de 50) y el camino de degradación con un Redis que no contesta.
- `test_importer.py`: el parseo y la validación sin base (un caso por motivo de rechazo, y que el hash normalice tildes y signos) y la carga contra Postgres real: duplicado por `content_hash`, idempotencia, y que el archivo de semilla cargue las 60 repartidas entre las 6 categorías.
- `test_schema_matches_models.py`: guardia contra el drift entre los modelos y la migración. Hace falta porque `alembic check` **no compara los `CHECK`** (los deja pasar agregados, cambiados, renombrados o borrados).
- `test_rooms_api.py` y `test_arcade_ws.py`: con `httpx` y el cliente de test de FastAPI, incluyendo WebSocket.
- `test_room_ws.py`: partida completa entre dos clientes simulados, con desconexión y reconexión dentro de la ventana de gracia.

### Frontend

- `svelte-check` sin errores en CI.
- Playwright: una partida completa con dos contextos de navegador. Crear sala, unirse con el código, jugar 3 rondas, ver el ganador, pedir revancha.
- Playwright: un arcade completo hasta perder las 3 vidas y verificar que el puntaje aparece en el ranking.

### CI

`.github/workflows/ci.yml`, en cada push y pull request:

1. Levanta Postgres y Redis como servicios.
2. Backend: `ruff`, `mypy`, `pytest`.
3. Frontend: `npm ci`, `svelte-check`, `npm run build`.
4. Playwright contra un entorno local levantado en el mismo job.

---

## 19. Roadmap por fases

Cada fase termina en algo que se puede abrir en el navegador y mirar. No se pasa a la siguiente sin cumplir los criterios.

### Fase 0 — Esqueleto del proyecto

**Entregable:** monorepo con backend y frontend levantando, base y caché en Docker, CI corriendo.

**Criterios de aceptación**
- `make up && make migrate && make api` deja la API en `:8000` y `GET /health` devuelve `{"api":"ok","db":"ok","redis":"ok"}`.
- `make web` abre SvelteKit en `:5173` con la pantalla de inicio usando los tokens de diseño.
- El workflow de CI pasa en verde con `ruff`, `mypy`, `svelte-check` y build.
- `README.md` con las instrucciones exactas para levantar el proyecto desde cero.

### Fase 1 — Identidad y contenido

**Entregable:** un usuario invitado puede existir, y hay preguntas cargadas.

**Criterios de aceptación**
- `POST /auth/guest` devuelve usuario y token, y el token sirve para pegarle a `GET /me`.
- El nick se valida y se filtran palabras prohibidas.
- `make import FILE=preguntas.csv` carga preguntas y devuelve un informe con importadas, duplicadas y rechazadas.
- Una pantalla de admin lista las preguntas con filtros y permite cargar un archivo.
- Como mínimo 60 preguntas de ejemplo cargadas, repartidas entre las 6 categorías.

### Fase 2 — Salas y presencia

**Entregable:** dos navegadores se encuentran en una sala por código.

**Criterios de aceptación**
- `POST /rooms` devuelve un código de 6 caracteres sin caracteres ambiguos.
- Dos navegadores distintos abren `/room/{code}` y ambos se ven en la lista de jugadores en tiempo real.
- Si un tercero entra, se le informa que la sala está llena.
- Si el host cierra la pestaña, el invitado lo ve reflejado.
- Una sala sin arrancar expira a los 10 minutos y el código se libera.

### Fase 3 — Partida online completa

**Entregable:** el juego funciona de punta a punta.

**Criterios de aceptación**
- El host elige rondas y segundos, y arranca.
- Las preguntas llegan sin la respuesta correcta en el payload (verificado en los tests).
- Al contestar los dos o al vencer el tiempo, se revela el resultado con la opción correcta, los puntos y el marcador.
- El puntaje coincide exactamente con la fórmula, verificado por test.
- Al terminar se muestra el ganador con el resumen ronda por ronda.
- El empate dispara el desempate con la mitad del tiempo.
- Matar la conexión de un jugador y volver dentro de 20 segundos retoma la partida en el mismo estado.
- No volver en 20 segundos termina la partida y declara ganador al que quedó.
- El botón de revancha arranca una partida nueva con preguntas nuevas.

### Fase 4 — Arcade y ranking

**Entregable:** el modo individual con récord.

**Criterios de aceptación**
- Una corrida arranca con 3 vidas, 20 segundos y dificultad 1.
- El tiempo baja a medida que se acierta, hasta el piso de 5 segundos, verificado por test.
- La dificultad sube por tramos, verificado por test.
- Un error descuenta vida y reinicia la racha.
- Al quedarse sin vidas, se guarda el puntaje y se informa la posición en ambos rankings.
- `GET /leaderboard/arcade?period=all` y `period=week` devuelven las listas correctas, y la semana corta el lunes en horario de Argentina.
- Un nuevo récord personal se celebra de forma distinta en la pantalla de fin.

### Fase 5 — Identidad visual y pulido

**Entregable:** el juego se ve y se siente como un juego, no como una app.

**Criterios de aceptación**
- Los 9 componentes de la sección 15.3 están implementados y en uso, sin excepciones.
- Ningún archivo del frontend contiene `linear-gradient`, `radial-gradient`, `filter: blur`, ni un emoji.
- Todos los íconos son SVG propios, incluidos los 6 de categoría.
- Los efectos de sonido suenan en acierto, error, revelación, tic tac, victoria y derrota, con interruptor de silencio.
- La pantalla de partida no genera scroll en un viewport de 360 × 640.
- El match se puede jugar entero con el teclado.
- `npm run build` no supera los 250 KB de JavaScript comprimido en la pantalla de juego.

### Fase 6 — PWA, pruebas de extremo a extremo y documentación

**Entregable:** el MVP terminado y documentado.

**Criterios de aceptación**
- La app es instalable desde el navegador y abre en modo standalone.
- Playwright corre las dos pruebas de extremo a extremo en CI y pasan.
- `docs/plan.md` refleja el juego terminado y coincide con el código (producto, reglas y capa de datos en el Anexo A).
- El README explica cómo cargar preguntas nuevas y cómo agregar una categoría.

### Fase 7 (opcional, posterior) — Preparado para publicar

**Entregable:** contenedores listos y notas de despliegue.

**Criterios de aceptación**
- `docker compose -f docker-compose.prod.yml up` levanta API, web, base y caché en la máquina local, y el juego es jugable en `http://localhost`.
- `docs/deploy.md` describe las opciones gratuitas o de bajo costo evaluadas, con sus límites, y los pasos para publicar.
- Si se quiere mostrar el juego a otras personas sin gastar nada, se documenta el uso de un túnel (por ejemplo Cloudflare Tunnel) apuntando a la instancia local.

---

## 20. Definición de terminado del MVP

El MVP está terminado cuando se cumplen todos estos puntos a la vez:

1. Dos personas en navegadores distintos juegan una partida 1v1 completa entrando por un código, con rondas cronometradas, revelación de resultados, marcador y ganador.
2. Existe empate resuelto por desempate, hay revancha, y hay manejo de desconexión con 20 segundos de gracia.
3. Una persona juega el arcade, ve subir la dificultad, ve bajar el tiempo, pierde las 3 vidas, y su puntaje aparece en el ranking global y en el semanal.
4. No existe ninguna forma de que el cliente conozca la respuesta correcta antes de responder, y todos los puntajes se calculan en el servidor.
5. Hay al menos 60 preguntas cargadas por el importador, repartidas entre las 6 categorías.
6. El CI pasa en verde, incluidas las pruebas de extremo a extremo.
7. La interfaz no tiene ningún gradiente decorativo, ningún emoji y ningún componente genérico, y todos los íconos son SVG propios.
8. Levantar el proyecto desde cero toma a lo sumo cinco comandos documentados en el README.

---

## 21. Notas sobre despliegue (fuera del MVP)

No forma parte del MVP, pero queda preparado y documentado.

- El backend y el frontend tienen `Dockerfile` desde la Fase 0, para que publicar después no implique reescribir nada.
- Toda la configuración entra por variables de entorno, así que no hay que tocar código para desplegar.
- El estado de las salas vive en memoria más Redis, y la sincronización entre instancias por Pub/Sub, así que escalar horizontalmente no requiere cambios de modelo.
- **Advertencia honesta:** Fly.io ya no ofrece un plan gratuito real para cuentas nuevas. Las alternativas a evaluar cuando se decida publicar, por orden de conveniencia, son: exponer la instancia local por un túnel sin costo, un servicio gratuito con suspensión por inactividad, o una capa gratuita de largo plazo de algún proveedor de nube. Ninguna es ideal para tiempo real, y por eso el despliegue está deliberadamente fuera del alcance.
- El dominio propio también queda para más adelante. No es un requisito de nada.

---

## 22. Riesgos y cómo se mitigan

| Riesgo | Impacto | Mitigación |
|---|---|---|
| No hay suficientes preguntas y las partidas repiten | El juego se vuelve aburrido | Cargar la base por tramos con el importador, y que el motor tolere el faltante sin romperse |
| El temporizador depende del reloj del cliente | Trampa y sensación de injusticia | Todos los tiempos los calcula el servidor y el cliente solo dibuja |
| Diferencias de latencia en la red | El rival parece contestar antes | El puntaje premia un rango amplio y el tiempo medido es el del servidor, no el del navegador |
| El estado de las salas en memoria se pierde al reiniciar | Partidas colgadas | Todo cambio de sala se publica en Redis y cualquier instancia puede reconstruir la sala |
| Complejidad de SvelteKit para quien viene de Java | Retraso del proyecto | El proyecto se limita a un SPA sin SSR; el plan evita deliberadamente funcionalidades avanzadas de SvelteKit |
| Python es nuevo para el dueño | Código frágil | Backend tipado con `mypy`, motor de juego en funciones puras y bien testeadas, y cobertura alta en la lógica de puntaje |
| El diseño se vuelve "genérico" al crecer | Perder identidad | Las 10 reglas duras de la sección 15.1, y el criterio de la Fase 5 que las verifica de forma explícita |

---

## 23. Primer paso concreto para el agente implementador

1. Crear el monorepo con la estructura de la sección 6.
2. Escribir `docker-compose.yml`, `Makefile`, `.env.example` y `.gitignore`.
3. Levantar el backend mínimo con `GET /health` y el frontend mínimo con la pantalla de inicio usando los tokens de la sección 15.2.
4. Escribir el `README.md` con los cinco comandos para levantar el proyecto.
5. Recién después, empezar la Fase 1.

No adelantar fases. Cada fase se prueba en el navegador antes de seguir.
# Anexo A — Capa de datos y servicios

> Diseño de la capa de datos y servicios, plegado acá desde el viejo documento suelto.
> Escrito antes de implementar `models/`, Alembic, repositorios y WebSocket, para no
> refactorizar después: acá están las decisiones caras de cambiar.
> Estado: **acordado y aplicado**. Los cuatro puntos marcados con ⚠️ (sección A8) están
> confirmados e implementados en las migraciones `0001`–`0003`.

## A1. Principios

1. **Postgres es la fuente de verdad** de usuarios, preguntas e historial. Redis es caché y estado vivo: si se cae, el juego se degrada, no se rompe.
2. **Cero migraciones descartables.** Lo irreversible se decide ahora; lo cosmético se decide cuando haga falta.
3. **El tipo de retorno previene el bug**, no la disciplina del programador. Ejemplo: es imposible armar el mensaje de ronda con un objeto que incluya la respuesta correcta.
4. **Nada de SQLite en tests.** No soporta `jsonb`, ni índices parciales, ni `CHECK` con regex: daría confianza falsa justo en lo que estamos diseñando.
5. **Ningún estado inválido persistible**: toda regla que pueda vivir en un `CHECK` o en un índice único, vive ahí y no solo en Python.

## A2. Decisiones irreversibles

| # | Decisión | Por qué ahora |
|---|---|---|
| 1 | `MetaData(naming_convention=...)` desde la primera migración | Sin esto los constraints quedan anónimos y cada `drop_constraint` posterior es adivinanza. Retrofittearlo obliga a una migración de churn sobre todas las tablas |
| 2 | Enums como `varchar` + `CHECK`, no `ENUM` nativo | Agregar una categoría es un `ALTER` de un check, no un `ALTER TYPE`; y queda grepeable en la migración |
| 3 | `questions.options` como `jsonb` array de 4 | Es lo que el plan pide. El `CHECK` valida forma y largo; que las opciones no estén vacías ni repetidas se valida en Python (Postgres no admite subconsultas en un `CHECK`) |
| 4 | `match_rounds` guarda `correct_index`, `difficulty` y `seconds` | Con esos campos cada fila es autosuficiente: se puede auditar y recomputar un puntaje histórico. Agregar columnas después es fácil; rellenar las viejas es imposible |
| 5 | Hash de deduplicación con normalización congelada | `content_hash = sha256(texto normalizado)`. Si el algoritmo cambia, todos los hashes existentes quedan inválidos y entran duplicados. Se define una vez, con tests de vectores fijos |
| 6 | Índice único **parcial** de `nick`: `UNIQUE (nick) WHERE deleted_at IS NULL` | Con un único global, un usuario con borrado lógico bloquea su nick para siempre |
| 7 | Regla de desempate del ranking definida ahora | ⚠️ Propuesta: mejor puntaje `DESC`, y empate resuelto por **el momento más temprano en que ese jugador alcanzó ese puntaje**. El SQL del plan ordena por `MAX(ended_at) ASC`, que significa "quien jugó por última vez hace más tiempo va primero": arbitrario e inestable |

## A3. Decisiones de arquitectura

**A3.1 El tipo impide filtrar la respuesta correcta.** El repositorio devuelve dos formas distintas:

- `RoundQuestion`: id, enunciado, opciones, categoría, dificultad. **Sin** índice correcto.
- `GraderQuestion`: lo anterior más `correct_index` y explicación.

La capa de WebSocket solo puede construir `round_start` con la primera. Filtrar la respuesta correcta exige pedir explícitamente la segunda, así que el error deja de ser un descuido posible. Test: el diccionario del mensaje no contiene la clave.

**A3.2 La partida se escribe en dos momentos, no en cada ronda.** ⚠️ Me aparto del plan ("la base se escribe al terminar"):

- Al arrancar: `INSERT` de la fila de `matches` con `status = playing`.
- Al terminar: `UPDATE` del match + `INSERT` en bloque de `match_rounds`.

Motivo: el estado `void` del plan necesita una fila que exista. Si solo se escribe al final, un proceso que muere en medio no deja rastro y `void` es inalcanzable. Sigue habiendo cero escrituras por ronda. Un barrendero al arrancar marca como `void` toda partida `playing` más vieja que N minutos.

**A3.3 `score_a` / `score_b` son una copia derivada.** Se guardan para listados rápidos, y el único que los escribe es el motor, que los deriva del historial de rondas. Una sola verdad, una sola copia.

**A3.4 `matches` con `player_a_id` / `player_b_id`, no tabla de jugadores.** Como pide el plan. "Mis últimas partidas" queda como `OR` entre dos índices: suficiente para 1v1 fijo. Cambiar a una tabla de jugadores es posible pero no gratis, y solo hace falta si alguna vez se juega de a más de dos.

**A3.5 Ranking en Postgres, no en Redis.** Menos sincronización, menos bugs. Los sorted sets de Redis quedan para cuando se mida que hace falta.

**A3.6 La interfaz del estado de sala se define ahora, la implementación después.** Es la pieza con más chance de reescritura. Se define un protocolo `RoomStore` y una implementación en memoria con `asyncio.Lock` por sala. Multi-instancia = nueva implementación de la misma interfaz, sin tocar a quien la usa.

**A3.7 Redis caído no rompe el arcade.** Errores de Redis se atrapan y se loguean (mismo criterio que `/health`): el arcade degrada a repetir preguntas y el ranking sigue funcionando.

## A4. Esquema

Convenciones: todo `snake_case`, PK `uuid` nativa con `default=uuid.uuid4` (en Python, no en la base), timestamps `timestamptz` en UTC con `server_default=now()`.

| Tabla | Integridad | Índices |
|---|---|---|
| `users` | PK uuid; `nick` 1–16 sin espacios sobrantes; `email`/`provider` nulos en MVP; `deleted_at` para borrado lógico | único parcial de `nick` entre vivos |
| `questions` | PK uuid; `category` en 6 valores; `difficulty` 1–5; `prompt` ≤ 300; `options` jsonb array de 4; `correct_index` 0–3; `status` draft/published/archived; `content_hash` único; `media_type` none/image/audio con la regla "si no es none, `media_url` no es nulo" | `(status, category, difficulty)`; único en `content_hash` |
| `rooms` | PK uuid; `host_user_id` FK a `users` (el creador es el host; la fila vive más que las conexiones); `code` char(6) único, con `CHECK` del alfabeto sin caracteres ambiguos; `config` jsonb; `status` waiting/playing/finished/expired | `(status, expires_at)`; `host_user_id` |
| `matches` | PK uuid; FK a `rooms` y a los dos jugadores; `config` jsonb; `status` playing/finished/abandoned/void; `winner_id` nulo en empate y en void; `score_a`/`score_b` ≥ 0 | `(status, started_at)`, `player_a_id`, `player_b_id` |
| `match_rounds` | PK uuid; FK a `matches` `ON DELETE CASCADE`; único `(match_id, round_index)`; elecciones 0–3 o nulas; `ms` ≥ 0; `points` ≥ 0; + `correct_index`, `difficulty`, `seconds` | FKs |
| `arcade_runs` | PK uuid; FK a `users`; `score`, `correct_count`, `max_difficulty`, `longest_streak`; `status` playing/finished/invalid | `(user_id, score DESC)`, `(ended_at)`, `(score DESC)`, los tres parciales `WHERE status = 'finished'` |
| `arcade_answers` | PK uuid; FK a `arcade_runs` `ON DELETE CASCADE`; único `(run_id, round_index)`; `chosen_index` nulo si no contestó; `is_correct`, `ms`, `points` | FKs |

Detalles que quedan fijados:

- **`config` jsonb** con forma `{"rounds": n, "seconds": s}`. Se serializa desde y se parsea hacia la misma clase `MatchConfig` del motor, así el formato no puede divergir entre el motor y la base.
- **Anti-trampa**: `status = invalid` existe en el esquema; el umbral concreto (cantidad de respuestas imposibles) queda como constante a definir en `game/constants.py`.
- **Corte semanal**: lunes 00:00 en `America/Argentina/Buenos_Aires`, calculado con `zoneinfo` y comparado como `timestamptz`.
- **`last_seen_at`** se actualiza al crear sesión y al terminar una partida, no en cada request.
- **Sin revocación de tokens**: el JWT de invitado no se puede invalidar antes de su vencimiento. Consecuencia aceptada del diseño sin sesiones en base.

## A5. Migraciones y tests

- `alembic/env.py` **async** sobre el engine de asyncpg, con `compare_type=True` y `compare_server_default=True` para que autogenerate no ignore cambios de tipo o de default.
- **Una migración inicial** que crea todo. Nunca `create_all` en código de aplicación.
- **`alembic check` en CI**: falla si los modelos y las migraciones se desincronizaron. Es el guardarraíl contra "funciona en mi máquina porque yo tenía la tabla".
- Tests contra Postgres real, base `trivia_test`, migraciones una vez por sesión, cada test dentro de una transacción que se revierte. `pytest-asyncio` en modo `auto`.
- Los tests de constraints son explícitos: se intenta insertar el dato inválido y se exige el error. Es la única forma de saber que el `CHECK` está donde creemos.

## A6. Orden de implementación

Cada paso termina con su verificación y no se pisa con el siguiente.

| # | Paso | Verificación |
|---|---|---|
| 1 | `models/`: las 7 tablas, `MetaData` con convención, enums, checks | `mypy` limpio y autogenerate produce lo esperado |
| 2 | `alembic.ini`, `env.py` async y migración inicial revisada a mano | `upgrade head` sobre base limpia y `alembic check` sin diferencias |
| 3 | Fixtures de test con Postgres real y rollback por test | Un test por constraint, exigiendo el rechazo |
| 4 | `api/deps.py` con `get_session`; `POST /auth/guest` + JWT + filtro de nicks | Endpoints con `httpx`: nick duplicado resuelto, palabra prohibida rechazada |
| 5 | Repositorio de preguntas: candidatas desde Postgres (`RoundQuestion`), vistos desde Redis con degradación | Una partida de 7 rondas nunca repite; el payload no filtra el índice |
| 6 | Importador CSV/JSON + `cli.py` + 60 preguntas semilla | Informe de importadas/duplicadas/rechazadas y vectores fijos del hash |
| 7 | `game/protocols.py` (mensajes WS) y `RoomStore` en memoria con lock por sala | Tests de la máquina de estados de la sala |
| 8 | `ws/room_ws.py`: lobby, presencia, arranque, rondas con el motor, desempate, gracia de 20 s, revancha | Partida completa entre dos clientes simulados, con desconexión y reconexión |
| 9 | Arcade sobre WS + ranking + `leaderboard` con corte semanal | Test del lunes 00:00 local y de la regla de desempate |
| 10 | Admin, README y CI completo | CI en verde de punta a punta |

## A7. Lo que NO se hace

- Nada de `create_all` en runtime, ni migraciones automáticas al arrancar la API.
- Nada de estado de partida en Postgres mientras la partida ocurre (salvo la fila del match).
- Nada de SQLite en tests.
- Nada de escribir el estado vivo solo en Redis sin la interfaz `RoomStore` de por medio.
- Nada de ranking por sorted sets de Redis en el MVP.

## A8. Puntos a confirmar al arrancar

1. ⚠️ Fila de `matches` al arrancar (A3.2) en vez de solo al terminar, para que `void` sea alcanzable.
2. ⚠️ Desempate del ranking por el momento más temprano en que se alcanzó el mejor puntaje (decisión A7).
3. ⚠️ Índice único parcial de `nick` para permitir reuso tras el borrado lógico (decisión A6).
4. ⚠️ (confirmado 2026-10-17) El host de la sala es **quien la creó**, y se guarda en `rooms.host_user_id` (FK a `users` + índice). Una columna en la fila y no estado en memoria: la sala vive más que las conexiones, y el host es el único que elige la config y manda `start`.

## A9. Relación con el plan general

El **§9 del plan** sigue mandando en el producto, las reglas del juego y el protocolo de mensajes. Este anexo solo fija la capa de datos y servicios, y en los cuatro puntos marcados ⚠️ (sección A8) propone un cambio respecto del plan. Ya están confirmados y reflejados en el plan (secciones §8 y §14).
