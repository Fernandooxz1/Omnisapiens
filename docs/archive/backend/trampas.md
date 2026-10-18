# Anexo B — Decisiones y trampas del backend (no re-descubrir)

> Memoria del proyecto: lo que ya costó un bug. Se consulta por `grep` cuando la tarea toque
> el backend. Formato: una línea por decisión, con el porqué cuando no es obvio.

**Modelos y esquema**

- `Mapped[X]` decide el NOT NULL; `uuid4` en Python; `DateTime(timezone=True)` +
  `server_default=now()`; todo constraint con nombre propio; único parcial para el borrado lógico.
- Los valores de cada `CHECK` salen de `game/constants.py` y de los enums de los motores:
  motor y base no pueden divergir sin que la migración lo delate.
- Un `CHECK` que evalúa a `NULL` **no viola nada**: para claves ausentes de un `jsonb`,
  `IS NOT DISTINCT FROM`, nunca `=`.
- Sin `relationship()` en los modelos, el ORM no deduce el orden de los INSERT: en los
  tests lo ordena `acepta()` (un flush por tabla). El día que el repositorio inserte filas
  relacionadas, tendrá el mismo problema.
- Alembic **nunca compara `CHECK`**: esas migraciones van a mano, y por eso existe la
  guardia de schema. Las FK y la expresión de un índice sí las detecta.
- Verificar una migración no es "mirar el archivo": se comparan inventarios de
  `pg_constraint`/`pg_indexes` de la base migrada contra el DDL de los modelos.
- Una migración que agrega una columna `NOT NULL` sin default sobre una tabla con filas
  falla a propósito: en `0002` no hay host que inventarle a una sala vieja.
- El único de `nick` es funcional sobre `lower(nick)` y parcial: `Ana` y `ana` son el mismo
  nombre y el borrado lógico lo libera. La guardia de schema compara texto de Postgres
  contra texto de Postgres, así que un índice funcional no la rompe.
- El código de sala se genera con `secrets` (no `random`): es la llave de la sala. La
  colisión la arbitra el único de `code` con reintento, patrón que comparte con el nick.
- El `server_default` no puebla el atributo en Python tras el `flush` (sin `eager_defaults`):
  por eso `POST /rooms` devuelve solo `code`/`config` y el status se lee en el `GET`.
- La URL de la base **no** está en `alembic.ini`: sale de `.env` por `app.config.settings`.

**Persistencia y commit**

- **H-05**: `get_session` commitea al cerrar el `yield`, pero FastAPI cierra eso **después**
  de emitir la respuesta: no protege al cliente. Los endpoints de escritura
  (`/auth/guest`, `POST /rooms`, `PATCH`/`DELETE /me`) commitean ellos antes de responder;
  `get_session` queda de red de seguridad. "El borde del pedido es el borde de la
  transacción" era falso.
- La CLI y el `room_manager` commitean a mano: no hay pedido, no heredan el commit de
  `get_session`. Si la escritura del manager falla, el estado en memoria vuelve atrás.
- La partida se escribe en dos momentos (A3.2) y `_persist` mira "la partida pasó a
  `playing`" en vez de "arrancó de cero": el rematch reusa el mismo bloque que `start`.
- El arcade igual: `INSERT` con `status` explícito al arrancar y `UPDATE` + **todas** las
  `arcade_answers` en el mismo commit al terminar. Si falla al arrancar → `RUN_NOT_STARTED`
  y el `rollback` deja la sesión limpia; si falla al cerrar → juega igual y la fila queda
  `playing` para que el barrendero la invalide.
- En los tests, un `rollback` de la corrida se lleva puesto lo sembrado en el SAVEPOINT: el
  test del reintento commitea el banco antes (es H-05 visto desde el fixture).

**Auth**

- El token se lee con `algorithms=[ALGORITHM]` explícito (sin eso pasaría el `alg: none`) y
  se atrapa `jwt.PyJWTError` entero: `InvalidTokenError` no cubre fallas de clave o algoritmo.
- Sin `Authorization` el usuario es `None`, pero con un token **roto** es 401 y no un usuario
  nuevo: ignorarlo le daría al cliente otra identidad sin avisarle.
- `get_current_user` **envuelve** a `get_optional_user`: un solo camino de auth.
- `authenticate` (`api/deps.py`) es la **única puerta**: la usan el header HTTP y el
  `?token=` del WS.
- `rename_user` NO hace SELECT previo (el único parcial es el árbitro y entre chequear y
  escribir hay carrera): atrapa `IntegrityError` y hace `rollback`, mismo patrón que
  `create_guest`. Costo: el PATCH rechazado se verifica por status, no por fila.
- `PATCH /me` reemite el token (el pase lleva el `nick` adentro; dejarlo viejo sería un pase
  que miente). `DELETE /me` es baja lógica y el dep rechaza al borrado (401); el único
  parcial libera el nick sin borrar la fila.
- El perfil y el pase viven en `schemas/users.py` (`UserOut`, `AuthOut`, `NickUpdate`).
- El 422 incluye el campo (`loc[1:]`) para que el cliente sepa qué corregir. El formato es
  `{"error": {"code", "message"}}` también para el 422; el 404 de ruta desconocida sigue
  siendo el de FastAPI.
- `JWT_SECRET` de dev tiene 18 bytes y PyJWT avisa: en prod tiene que medir 32 o más
  (`Settings` lo rechaza si `env != "local"`).

**Tests**

- Un test que pasa no dice nada por sí solo: lo que prueba es el sabotaje.
- Los tests de API usan `client` con `ASGITransport` y reemplazan `get_session` por la
  sesión del test: el pedido entra en la misma transacción y el rollback lo deshace.
- Los tests de WS **no usan `starlette.testclient`** (levanta la app en otro hilo y loop, y
  la sesión de asyncpg no cruza): `tests/ws_client.py` maneja `scope: "websocket"` a mano,
  con el mismo aislamiento que el resto. `until(t)` saltea los ya llegados; el test pide por
  tipo, no por orden.
- En los tests, `drain()` vacía la cola: un solo `drain` por tanda (dos seguidos descartan
  el mensaje no mirado).
- Los tests del `room_manager` pasan la **sesión del test** como factory (su `commit` se
  vuelve SAVEPOINT), sin ensuciar `trivia_test`.
- Ojo con tests que rompen dos reglas a la vez: puede llegar el error de la otra. Aislar la
  fila inválida en vez de aflojar el `motivo`.
- El reloj y el `sleep` se inyectan: el `FakeClock` no duerme, espera a que el test mueva la
  hora, así una partida entera por vencimientos corre en milisegundos. Está en `tests/clock.py`.

**Contenido e importación**

- El `content_hash` se calcula sobre el enunciado normalizado (NFKD sin diacríticos,
  minúsculas, sin signos, espacios colapsados): "¿Cuál es el río?" y "Cual es el rio" son la
  misma pregunta.
- El default del import es `draft`; las 72 semilla entran `published` por flag (`make seed`),
  si no `candidates()` no ve nada que jugar.
- `import_rows` frena el duplicado **dentro del mismo archivo** en Python (dict de hashes):
  el `ON CONFLICT` solo ve lo ya cargado. El importador repite en Python los `CHECK` y las
  reglas que la base no expresa (opciones no vacías y distintas), para que el informe traiga
  fila y motivo en vez de un `IntegrityError` sin contexto.
- El import HTTP es un **borde sobre `services/importer.py`**, no un segundo importador:
  `parse_text` lo comparten CLI y endpoint. Errores de archivo → 400 `IMPORT_FORMAT`; de
  fila → `rejected` sin abortar. `python-multipart` está por `UploadFile`.
- El listado ordena `created_at DESC, id DESC` (dos importadas en el mismo lote comparten
  `created_at`; sin desempate, la página 2 repite una fila). `q` es `ILIKE` con `%` y `_`
  escapados y es **sensible a tildes** (`rio` no encuentra `río`; insensible pide `unaccent`).
- El panel es lo **único** que devuelve `correct_index`, a propósito. `ADMIN_TOKEN` es
  obligatorio: vacío siempre se rechaza y < 32 bytes se rechaza fuera de `local`; se compara
  con `compare_digest` sobre **bytes** (la versión de texto explota con no-ASCII).

**Sala viva (`runtime/`, `ws/`)**

- La sala viva es **estado inmutable + transiciones puras**: recibe `now_ms` y lo ya cargado
  (`LoadedQuestion`, `match_id`) y devuelve estado nuevo + mensajes. Base, sockets, reloj y
  lock son de afuera: se testea sin nada levantado.
- Los mensajes salen **por jugador** (`dict[user_id, mensajes]`), no como broadcast:
  `room_state` lleva `you` y `round_result`/`match_end` cambian de lado según quién mira.
- El host se sienta en `A` (calza con `rooms.host_user_id`/`matches.player_a_id`), el
  invitado en `B`; un tercero recibe `ROOM_FULL`.
- Al reanudar una ronda pausada se corre **todo** (arranque y respuestas ya dadas) por el
  hueco: el tiempo de quien ya contestó no cambia y el reloj no gasta pausa. Repetir una
  respuesta es idempotente.
- La última ronda emite `round_result` **y** `match_end` juntos.
- El `RoomStore` es un `Protocol`; el estado vivo es **uno por proceso** (`room_store`,
  como `engine` y `redis_client`) y se apaga en el lifespan.
- Por eso mismo, fuera de `local` la API **se niega a arrancar** sin `SINGLE_PROCESS=1`
  (H-07): con `--workers 2` cada worker tendría su propio `room_store` y dos verdades para
  el mismo código de sala. Desde adentro no se pueden contar los workers: lo declara quien
  despliega. Cuando el `RoomStore` sea el de Redis, el guard se cae solo.
- Dos salas en el mismo test comparten la `AsyncSession` de la fixture: una sesión no
  soporta dos operaciones a la vez, así que la fábrica va con `_serializada` (cerrojo). Lo
  que queda intercalado, que es lo que se quiere probar, son las transiciones y el `Random`
  compartido; en producción cada `_pick`/`_persist` se lleva su propia sesión del pool.
- `room.start` sólo se acepta desde `WAITING` (H-06): con la sala `finished`, el único
  camino es la revancha acordada. `disconnect` vuelve la sala a `WAITING`, así "se fue uno,
  entra otro, arrancamos" sigue andando.
- `GET /rooms/{code}` informa `players` desde el `RoomStore` (presencia viva), no desde la base.
- El pool de preguntas se recorta al tramo de dificultad **antes** de elegir; si no hay
  pregunta en el tramo, los dos reciben `NO_QUESTIONS` y la sala queda `playing` (la fila la
  cierra el barrendero, no el vacío).
- Los vencimientos son **una task por sala** que duerme al próximo plazo (ronda o gracia) y
  se despierta con un `Event`; bajo el lock vuelve a chequear el plazo.
- El reloj **no muere con el primer error de base**: reintenta con backoff y, agotados
  `MAX_EXPIRY_FAILURES`, avisa `ROOM_CLOCK_DOWN` y se rinde. `_tick` aísla una vuelta del
  reloj; reintentar es seguro porque `_step` dejó el estado coherente con Postgres.
  `retry_serve` cubre el fallo al cargar la **próxima** pregunta (no alcanza con
  `needs_next_round`: `NO_QUESTIONS` también lo deja en `True` y ahí hay que esperar).
- H-03: `RoomStore.open` desaloja, antes de crear una sala, las que no tienen `outbox`, no
  están `playing` y llevan más de `ROOM_IDLE_TIMEOUT_SECONDS` sin actividad
  (`last_activity_ms` se toca en cada transición). Una entrada `expired` que se reabre se
  reemplaza por una fresca.
- H-04: el barrido de salas filtra `status='waiting'`; para que eso signifique algo,
  `rooms.status` se sincroniza con la vida de la sala (`playing` al arrancar/revancha,
  `finished` al cerrar, `waiting` al irse alguien de una terminada). Al arrancar la partida
  se refresca `expires_at` con `rounds × (seconds + gracia) + 60 s`.
- Una sala **vencida no se revive** (`room_is_available`): `expired`, o `waiting` con
  `expires_at` pasado → 404 en la vista previa y `ROOM_NOT_FOUND` en el WS. `playing` y
  `finished` siguen abiertas.
- El **barrendero** (`services/reaper.py`) corre al arrancar y cada
  `REAPER_INTERVAL_SECONDS` (60) desde el lifespan, cancelado limpio. Cierra lo que nadie
  más cierra: `waiting` vencidas → `expired`, `playing` más viejas que
  `STALE_MATCH_MINUTES` (15) → `void`, corridas de arcade igual de viejas → `invalid`. Tres
  `UPDATE` con `returning` y un commit; idempotente y best-effort (si la base no contesta,
  loguea y la API arranca igual; el `except` no atrapa `CancelledError`).
- El barrido **no adivina qué está vivo**: recibe `Live` (`runtime/live.py`) con lo que el
  proceso sabe (`RoomStore.live()`, `live_arcade_runs`) y excluye esos ids con `NOT IN`.
  Correcto con un proceso; con varias instancias vive en Redis.
- La entrega es un **outbox** (cola) por jugador, no un callback: el vencimiento entrega sin
  que haya nadie esperando y el timer no conoce sockets. `OUTBOX_MAX = 64`: si el cliente no
  lee, se descarta el más viejo. `disconnect` suelta esa cola.
- `disconnect` recibe el `outbox` de **su** conexión y no toca la silla si esa cola ya no es
  la vigente (H-01): un corte silencioso deja al socket viejo vivo hasta el timeout, y al
  cerrar no puede desmontar al que ya reconectó. El `outbox` es único por conexión, así que
  la comparación por identidad alcanza.
- El WS **acepta antes de autenticar**: un token malo tiene que poder recibir `AUTH_REQUIRED`
  por el socket; el rechazo de entrada (token, sala, sala llena) cierra con **1008**.
- El handler hace `join` **al conectar**, no al `hello`; `hello` → `sync` repinta el estado
  completo y la ronda en curso con su `ends_at` original.
- `RoomStore.seated` existe por el tercero: le deja su `ROOM_FULL` en el `outbox` y el
  handler lo manda y **corta**.
- El socket lo escribe **una sola corrutina** (la que drena el `outbox`); el lector pasa por
  el mismo lock para el `pong`. Dos `send` en paralelo no son seguros.
- Un corte de red silencioso no genera `disconnect`: lo detecta el timeout de inactividad
  (45 s = 3 heartbeats) y recién ahí arranca la gracia.
- Códigos nuevos del WS: `BAD_MESSAGE` (sobre o `answer` mal formados) y `UNKNOWN_MESSAGE`;
  no se reusa `VALIDATION_ERROR`, que es del cuerpo HTTP.
- El token del WS viaja en `?token=` y uvicorn loguea la URL completa:
  `logging_config._HideWebSocketTokens` descarta los registros de `/ws/...` o con `?token=`
  (el filtro va por logger, no por handler).
- Swing del `shuffle`: se barajan **índices**, no textos, para que un banco con opciones
  repetidas no desplace la respuesta. `RoomStore` acepta `shuffle_served_options=False` para
  tests que necesitan predecir la letra.

**Arcade**

- El arcade resuelve **en la primera respuesta**, no espera a nadie: `answer` devuelve
  `arcade_result` y deja la sesión pidiendo la próxima. Una respuesta repetida de la misma
  ronda llega cuando la ronda ya no está en vuelo → `ROUND_MISMATCH`.
- La transición devuelve `(state, effects, record)` y **no** acumula `RoundRecord` en el
  estado: el motor los entrega para que el borde los guarde y el estado quede chico.
  `ArcadeEnd` sale con las posiciones en `None`; el ranking las completa.
- El `seen` vive en el estado de la sesión (el motor no guarda historial a propósito).
  `serve(..., allow_repeat=True)` es la excepción de §Selección: pool agotado → repite y
  sigue, con la advertencia en el log del llamador.
- El **WS del arcade no tiene store global**: una conexión es una corrida, el estado vive en
  el handler. La cola lleva `(mensaje, id)`, hasta el `pong`, y conserva la correlación sin lock.
- El reloj y el `Random` entran por `ArcadeRuntime` (inyectable). El `sleep` del `FakeClock`
  calcula el vencimiento al llamarlo y resuelve un registro que nace vencido: cubre la
  carrera entre `advance` y la tarea recién agendada.
- El `start` es **una vez por conexión**: para otra corrida se reconecta (no hay `restart`).
- El ranking se hace en Postgres (A3.5): `DISTINCT ON` por usuario ordenado por
  `score DESC, ended_at ASC` y la posición con `row_number()` sobre esa subquery. En
  SQLAlchemy 2.1 `.distinct(expr)` está deprecado: va `select(...).ext(distinct_on(...))`.
- El desempate usa el `ended_at` de la corrida que **alcanzó** el puntaje, no el último del
  jugador; con puntaje y fecha idénticos desempata `user_id`.
- La semana corta lunes 00:00 local (`zoneinfo`) y se compara como `timestamptz`: un run del
  domingo 23:59:59 local sigue en la semana anterior aunque en UTC ya sea lunes.
- `personal_best`/`is_new_best` miran la mejor corrida **anterior** (sin la actual): empatar
  el récord no es récord nuevo, y `personal_best` igual incluye la actual porque es el máximo.
  Si el ranking falla, esos campos salen en `None` pero la corrida ya quedó guardada.
- El `arcade_end` lo completa el borde con `dataclasses.replace` después de cerrar la fila.
  El JSON de `/leaderboard/arcade/me` usa `global` por `serialization_alias` (no puede ser
  nombre de campo en Python).

**Calidad y procesos**

- La barra de calidad es un **gate**: `ruff` con `select` (incluye `ASYNC`, `B`, `SIM`,
  `PT`; `N818` ignorado), `mypy strict` y la cobertura en `make cov` (umbral 85 %), **no** en
  `addopts` (si estuviera, una corrida dirigida fallaría por la cobertura global).
- Los bordes tienen tope de tamaño: cuerpo HTTP 1 MB, `max_length` en el schema del nick, e
  import por lotes de 500.
- **Rate limiting** (`api/rate_limit.py`): ventana fija de 60 s por IP con bucket en Redis
  (`INCR`+`EXPIRE`), en alta de invitado, vista previa y WS. Si Redis no contesta, se deja
  pasar y se loguea. Un fixture autouse lo apunta al Redis de test con límites altos.
- Todo lo de frontend es de otra persona: acá solo se toca `backend/`.
- Este documento se mantiene alineado con el código en el mismo paso: el plan es lo que lee
  la próxima sesión.
