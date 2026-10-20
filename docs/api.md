# Contrato API — HTTP + WebSocket

> Lo que el frontend puede esperar del backend. El backend está cerrado; esto es la
> fuente de verdad del cliente. Se consulta por sección.

- **Base HTTP:** `http://localhost:8000` (configurable; en SvelteKit, `PUBLIC_API_URL`).
- **Base WS:** mismo host, esquema `ws://` (`wss://` en producción).
- **JSON** siempre. Errores: `{"error": {"code", "message"}}`.
- **Tiempos absolutos:** epoch en **ms UTC**, generados por el servidor (`ends_at`, `achieved_at`).
  `created_at`/`ended_at` del perfil son ISO-8601 (`timestamptz`).
- **Auth HTTP:** `Authorization: Bearer <token>`. **Auth WS:** `?token=<token>`
  (el navegador no permite headers en `new WebSocket`).
- **CORS:** `CORS_ORIGINS` ya permite `http://localhost:5173`.
- **Rate limit:** 60 s por IP en `POST /auth/guest`, `POST /sessions`,
  `GET /rooms/{code}` y los WS. Al pasarse: `429 RATE_LIMITED`.

## HTTP

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `POST` | `/auth/guest` | opcional | Alta de invitado o token fresco → `201` |
| `GET` | `/me` | sí | Perfil + marcas + historial |
| `PATCH` | `/me` | sí | Cambia el nick → token fresco |
| `DELETE` | `/me` | sí | Baja lógica (`204`) |
| `POST` | `/sessions` | sí | Crea una sesión solo → `201` |
| `POST` | `/rooms` | sí | Crea sala 1v1 → `201` |
| `GET` | `/rooms/{code}` | no | Vista previa pública |
| `GET` | `/modes` | no | Catálogo de modos y su configuración |
| `GET` | `/leaderboard/{mode}` | no | Tabla global o semanal del modo |
| `GET` | `/leaderboard/{mode}/me` | sí | Posición propia en ambos períodos |
| `GET` | `/admin/content/{kind}` | `X-Admin-Token` | Listado del contenido del kind |
| `POST` | `/admin/content/{kind}` | `X-Admin-Token` | Subida CSV/JSON + informe |
| `GET` | `/admin/questions` | `X-Admin-Token` | Alias de `/admin/content/quiz` |
| `POST` | `/admin/questions/import` | `X-Admin-Token` | Alias de `/admin/content/quiz` |
| `GET` | `/health` | no | `200` o `503` |

### `POST /auth/guest`

Body `{"nick"?: string}` (opcional). Con un token válido **no crea a nadie**: devuelve el
mismo usuario con token fresco e **ignora** el nick del body.

```json
{ "user": { "id": "uuid", "nick": "Ana", "is_guest": true,
            "created_at": "...", "last_seen_at": "..." },
  "token": "eyJ..." }
```

Errores: `400 NICK_LENGTH` / `400 NICK_FORBIDDEN` / `409 NICK_TAKEN`.

### `GET /me`

```json
{ "id": "uuid", "nick": "Ana", "is_guest": true,
  "created_at": "...", "last_seen_at": "...",
  "best": { "all_time": 1240, "week": 980 },
  "arcade_runs": [ { "id": "uuid", "score": 1240, "correct_count": 11,
                     "longest_streak": 5, "max_difficulty": 3,
                     "ended_at": "..." } ],
  "matches": [ { "id": "uuid", "ended_at": "...", "opponent_nick": "Beto",
                 "my_score": 520, "opponent_score": 480, "result": "win" } ] }
```

`best` y las listas pueden venir vacíos (`null` / `[]`). `arcade_runs` y `matches`: hasta 10,
solo terminadas, de la más nueva a la más vieja. `result`: `win` | `loss` | `draw`, desde el
punto de vista del jugador. La **posición** no está acá: vive en `/leaderboard/{mode}/me`.

### `PATCH /me`

Body `{"nick": "Nuevo"}` → mismo `AuthOut` que el alta (guardar el token nuevo).
Errores: `400 NICK_LENGTH` / `400 NICK_FORBIDDEN` / `409 NICK_TAKEN` / `401 AUTH_REQUIRED`.

### `DELETE /me`

`204`, sin body. El token deja de servir (`401`).

### `GET /modes`

Sin auth. Es la fuente de verdad del menú: el cliente no hardcodea los modos.

```json
[
  { "code": "trivia_arcade", "name": "Arcade",
    "content_kind": "quiz", "play_format": "arcade",
    "players": "solo", "input": "choice",
    "media": ["none", "image", "audio"], "ranking": true,
    "config_schema": { "type": "object", "properties": {},
                       "additionalProperties": false, "title": "ArcadeConfig" } },
  { "code": "trivia_versus", "name": "1v1",
    "content_kind": "quiz", "play_format": "versus",
    "players": "versus", "input": "choice",
    "media": ["none", "image", "audio"], "ranking": false,
    "config_schema": { "type": "object",
                       "properties": { "rounds":  { "type": "integer", "default": 5 },
                                       "seconds": { "type": "integer", "default": 20 } },
                       "additionalProperties": false, "title": "VersusModeConfig" } }
]
```

`players`: `solo` | `versus`. `input`: forma de la respuesta (`choice`). `media`: tipos de
medio que el modo sabe mostrar. `ranking`: si el modo publica tabla (ver
`/leaderboard/{mode}`). `config_schema`: JSON Schema que valida el `config` de la sesión
o de la sala; `{}` es válido para el arcade porque sus reglas son fijas.

**Cómo consume el cliente cualquier modo.** El catálogo manda: no hay rutas por modo.

1. Leer `players` para elegir el canal: `solo` → `POST /sessions` + `WS /ws/session/{id}`;
   `versus` → `POST /rooms` + `WS /ws/room/{code}`.
2. Mandar el `config` tal cual lo valida `config_schema`; los defaults también los pone el
   esquema. Un modo `solo` con `config={}` usa sus reglas fijas (`ruleset_version`).
3. Dibujar el `payload` de `item_start` con `content_kind` + `input` + `media`; la forma la
   define el modo y la solución nunca viene en ese mensaje.
4. Mostrar el ranking solo si `ranking` es `true` y usar `/leaderboard/{code}`.
5. Tratar `MODE_NOT_FOUND` (`404`), `MODE_NOT_SOLO` (`422`), `INVALID_CONFIG` (`422`) y
   `MODE_WITHOUT_RANKING` (`404`) como parte del contrato, no como errores inesperados.

### `POST /sessions`

Crea una partida **solo** y devuelve su socket. Body:

```json
{ "mode": "trivia_arcade", "config": {} }
```

`config` se valida con el `config_schema` que publica `GET /modes`; para
`trivia_arcade` es `{}` (sus reglas son fijas por `ruleset_version`). Respuesta `201`:

```json
{ "session_id": "6f1c…", "ws_url": "/ws/session/6f1c…" }
```

`ws_url` es una ruta del backend: el cliente le antepone el host y el esquema
(`ws://`/`wss://`) que ya usa para el resto de los sockets.

| Caso | Respuesta |
|---|---|
| Modo inexistente | `404 MODE_NOT_FOUND` |
| Modo `players=versus` | `422 MODE_NOT_SOLO` |
| `config` inválido para el modo | `422 INVALID_CONFIG` |
| Sin token | `401 AUTH_REQUIRED` |
| Más de N por minuto desde la IP | `429 RATE_LIMITED` |

La fila nace en `playing` con `started_at`, dueño y el `config` validado. Si el
socket no llega a abrirse, el barrendero la invalida.

### `POST /rooms`

Body `{"rounds": 3|5|7, "seconds": 10|20|30}` (defaults `5` / `20`).

```json
{ "code": "K7MPQ2", "config": { "rounds": 5, "seconds": 20 } }
```

`201`. El `status` no viene acá (se lee en el `GET`). `code`: 6 caracteres del alfabeto
`ABCDEFGHJKLMNPQRSTUVWXYZ23456789` (sin `O`, `0`, `I`, `1`).

### `GET /rooms/{code}`

```json
{ "code": "K7MPQ2", "config": { "rounds": 5, "seconds": 20 },
  "status": "waiting", "host_nick": "Ana",
  "expires_at": "2026-10-18T12:30:00Z", "players": 1 }
```

`players` es un **número** (presencia viva en el proceso), no la lista de jugadores.
`host_nick` identifica al host: el lobby lo usa para mostrar `start` solo a esa persona.
`status`: `waiting` | `playing` | `finished` | `expired`. Sala vencida → `404 ROOM_NOT_FOUND`.

### `GET /leaderboard/{mode}?period=all|week&limit=1..100`

```json
{ "period": "all",
  "entries": [ { "position": 1, "nick": "Ana", "score": 1240,
                 "achieved_at": "2026-10-17T21:05:00Z" } ] }
```

Criterio: mejor `score` por usuario entre las sesiones `finished` con dueño (modos solo) del
`mode`; empate → **el momento más temprano** en que alcanzó ese puntaje. La semana corta lunes
00:00 en `America/Argentina/Buenos_Aires`. Un modo sin ranking → `404 MODE_WITHOUT_RANKING`
(hoy solo `trivia_arcade` lo tiene; `GET /modes` lo publica en `ranking`).
`/leaderboard/arcade` es alias de `/leaderboard/trivia_arcade`.

### `GET /leaderboard/{mode}/me`

```json
{ "global": { "rank": 12, "score": 1240, "achieved_at": "..." },
  "week":   { "rank": null, "score": null, "achieved_at": null } }
```

Los tres campos van juntos: sin corridas en el período, los tres son `null`.

### Admin

`X-Admin-Token: <ADMIN_TOKEN>` en **todas**. Ausente o inválido → `401 ADMIN_REQUIRED`
(mismo mensaje en ambos casos). El token se guarda en `sessionStorage`, nunca en el repo.

La ruta nueva es `/admin/content/{kind}`; hoy el único `kind` registrado es `quiz`.
`/admin/questions` y `/admin/questions/import` son alias de `/admin/content/quiz` y
devuelven lo mismo. Un `kind` desconocido → `422 VALIDATION_ERROR`.

**`GET /admin/content/{kind}`** — filtros `status` (`draft|published|archived`), `category`,
`difficulty` (1–5), `q` (substring, mayúsculas ignoradas, **tildes no**), `page` (desde 1),
`page_size` (1–100, default 20). Orden `created_at DESC, id DESC`. Lee
`content_items`/`content_solutions`.

```json
{ "items": [ { "id": "uuid", "category": "science", "difficulty": 3,
               "prompt": "...", "options": ["...","...","...","..."],
               "correct_index": 2, "explanation": "...", "source": null,
               "status": "draft", "media_type": "none", "media_url": null,
               "tags": [], "created_at": "...", "updated_at": "..." } ],
  "page": 1, "page_size": 20, "total": 120, "pages": 6 }
```

Es la **única** vista que trae `correct_index`. Categoría desconocida → `422 VALIDATION_ERROR`;
página de más → `200` con `items: []`. `source` y `tags` eran columnas de `questions` y el
contenido genérico no las guarda: salen `null` y `[]`.

**`POST /admin/content/{kind}`** — `multipart/form-data`: `file` (CSV o JSON según
extensión) y `status` opcional (`draft` por defecto). Escribe siempre en
`content_items`/`content_solutions`; la tabla vieja `questions` ya no recibe escrituras
(queda de solo lectura hasta la fase 10).

```json
{ "total": 12, "imported": 10, "duplicated": 1,
  "rejected": [ { "row": 7, "reason": "opción vacía" } ] }
```

Formato CSV: `category,difficulty,prompt,option_a,option_b,option_c,option_d,correct,
explanation,source,tags`. Archivo roto / no UTF-8 / extensión rara → `400 IMPORT_FORMAT`.
Una fila mala **no aborta**: viene en `rejected` con fila y motivo.

## WebSocket

Sobre único en ambas direcciones:

```json
{ "t": "tipo", "id": "opcional", "d": {} }
```

`id` solo se usa en el arcade para correlacionar respuestas; el cliente puede ignorarlo.

### Salas — `WS /ws/room/{code}?token=...`

Cliente → servidor: `hello {}`, `start {}` (solo host, con 2 jugadores), `answer
{"round": n, "choice": 0..3}`, `rematch {}`, `ping {}`.

| `t` | `d` |
|---|---|
| `room_state` | `{"code","status","config","you":{"id","nick"},"players":[{"id","nick"}],"match_id"}` |
| `match_start` | `{"match_id","config","rounds_total"}` |
| `round_start` | `{"round","question_id","prompt","options":[...],"category","difficulty","ends_at","total_seconds"}` — **sin la correcta** |
| `opponent_answered` | `{"round"}` (no revela qué eligió) |
| `round_result` | `{"round","correct_index","explanation","you":{"choice","ms","points","correct"},"opponent":{...},"scores":{"you","opponent"}}` |
| `reconnect_pending` | `{"seconds_left"}` |
| `opponent_returned` | `{}` |
| `match_end` | `{"winner":"you\|opponent\|tie","scores":{...},"rounds":[RoundResult,...],"reason":"completed\|abandoned"}` |
| `rematch_waiting` | `{}` |
| `error` | `{"code","message"}` |
| `pong` | `{}` |

- `round_result` y `match_end` cambian de lado según quién mira (`you`/`opponent`).
- En `match_end`, `rounds` trae **todos** los `round_result` de la partida.
- La última ronda emite `round_result` **y** `match_end` seguidos.
- `players` incluye sillas desconectadas (el servidor cuenta la silla hasta que vence la gracia).

### Arcade — `WS /ws/arcade?token=...`

Adaptador de compatibilidad: mantiene los mensajes históricos tal cual. El canal nuevo es
`WS /ws/session/{id}` (§Sesiones); la ventana de convivencia está en §Compatibilidad.

Cliente → servidor: `start {}`, `answer {"round": n, "choice": 0..3}`, `ping {}`.

| `t` | `d` |
|---|---|
| `arcade_start` | `{"run_id","lives","seconds"}` |
| `arcade_question` | `{"round","prompt","options","category","difficulty","seconds","ends_at","score","lives","streak","correct_count"}` |
| `arcade_result` | `{"round","correct_index","explanation","you":{...},"score","lives","streak","correct_count"}` |
| `arcade_end` | `{"run_id","score","correct_count","max_difficulty","longest_streak","rank_global","rank_weekly","personal_best","is_new_best"}` |
| `error` / `pong` | `{"code","message"}` / `{}` |

- El arcade **no espera a nadie**: cada `answer` devuelve `arcade_result` y el servidor
  manda la próxima `arcade_question` sin que el cliente la pida.
- `rank_global`, `rank_weekly` y `personal_best` pueden ser `null` (si el ranking falló);
  `is_new_best` igual llega.
- `start` vale **una vez por conexión**: para otra corrida se abre otra conexión (no hay
  `restart`).

### Sesiones — `WS /ws/session/{id}?token=...`

El canal genérico de una sesión solo. La sesión se crea antes con
`POST /sessions`; este socket no la crea ni la reinicia, solo la juega. Es
**efímero**: si el socket se cae, la fila queda `abandoned` y no se retoma.

Cliente → servidor: `answer {"round": n, "choice": 0..3}`, `state {}`, `ping {}`.

| `t` | `d` |
|---|---|
| `session_start` | `{"session_id","mode","config","lives"}` |
| `item_start` | `{"item_key","position","ends_at","total_seconds","payload"}` — **sin la solución** |
| `item_result` | `{"item_key","correct","submission","solution","points","scores"}` |
| `session_end` | `{"session_id","score","correct_count","max_difficulty","longest_streak","ranking"}` |
| `session_state` | respuesta a `state`: `{"session_id","mode","config","position","ends_at","total_seconds","payload","scores","finished"}` |
| `error` / `pong` | `{"code","message"}` / `{}` |

- `payload` es el ítem público validado por el `public_schema` del modo. La forma
  la define el modo, no una clase de mensaje: para `trivia_arcade` es
  `{"v", "prompt", "options", "media"}`.
- `solution` (y `submission`) recién aparecen en `item_result`, cuando el ítem ya
  cerró. `submission` es `null` si la ventana venció sin respuesta.
- `scores` es el estado del corredor después de la ronda:
  `{"score","lives","streak","correct_count"}`.
- `ranking` es `null` en un modo sin tabla (o si el cálculo falló). Con ranking:
  `{"rank_global","rank_weekly","personal_best","is_new_best"}`.
- Las opciones llegan barajadas: `choice` es el índice sobre `payload.options`.
- Igual que el arcade, `answer` repetido o fuera de ronda → `ROUND_MISMATCH`.

### Cliente: reconexión y heartbeat

- Backoff `0.5s → 10s` (exponencial con tope). Al reconectar, mandar `hello` y esperar el
  `room_state` completo; el servidor repone la ronda en curso con su `ends_at` original.
- Heartbeat cada `15 s`; sin `pong` en `10 s`, se considera caída y se reconecta.
- El cliente **nunca** decide el resultado de una ronda ni calcula puntos.
- Para abandonar una partida: cerrar la conexión. El rival ve la gracia de 20 s.

## Trampas del cliente

- **`room_state` no lleva puntajes.** Después de reconectar, el marcador local empieza en
  `0-0` hasta el próximo `round_result`; no inventar el puntaje desde el historial.
- **`players` cuenta sillas, no conexiones.** `2/2` puede aparecer antes de que el otro esté
  listo; el servidor rechaza `start` con `NOT_READY` y el botón no debe asumirlo.
- **No hay presencia por jugador.** Los elementos de `room_state.players` son `{id, nick}`,
  sin `connected`: el lobby dibuja las sillas sin estado de conexión y no debe inventarlo.
  El host se reconoce por `host_nick` de `GET /rooms/{code}`.
- **`GET /rooms/{code}` devuelve `players` como número**, no como lista (el WS sí manda la lista).
- **Las opciones llegan barajadas** en cada `round_start`/`arcade_question`: `choice` es el
  índice sobre el orden recibido, no el de la pregunta original.
- **La correcta no existe en el cliente** hasta `round_result`/`arcade_result`.
- **Todo tiempo sale del servidor.** Usar `ends_at` contra un reloj sincronizado; el `ms`
  que puntúa lo mide el servidor, no el navegador.
- **El rechazo de entrada del WS cierra con `1008`** (token, sala inexistente, sala llena).
  Un token inválido también puede llegar como `error AUTH_REQUIRED` por el socket.
- **El token viaja en la URL del WS**: no loguearlo en el cliente.
- **`status` de sala vencida**: `GET` da 404 y el WS `ROOM_NOT_FOUND`; no reintentar en loop.
- **Arcade: `start` una sola vez por conexión.** Al terminar, cerrar y abrir otra.
- **Sesión genérica: el socket no crea nada.** El id sale de `POST /sessions`; si el
  socket se cae, la fila queda `abandoned` y hay que crear otra sesión.
- **`answer` repetido** (doble tap, retry) → `ROUND_MISMATCH`; la ronda ya no está en vuelo.

## Compatibilidad

Durante el refactor conviven la superficie genérica y la histórica. Los alias responden
directo (sin redirect) y devuelven exactamente lo mismo que la ruta nueva: migrar el
cliente no cambia ningún payload.

| Superficie vieja | Superficie nueva | Qué se mantiene | Hasta |
|---|---|---|---|
| `GET /leaderboard/arcade` y `/leaderboard/arcade/me` | `GET /leaderboard/trivia_arcade` y `/me` | status y body idénticos | se mantiene después de la fase 10 |
| `GET /admin/questions` | `GET /admin/content/quiz` | misma página y filtros | se mantiene después de la fase 10 |
| `POST /admin/questions/import` | `POST /admin/content/quiz` | mismo informe de importación | se mantiene después de la fase 10 |
| `POST /admin/content/{kind}/import` | `POST /admin/content/{kind}` | mismo informe; ruta aceptada pero fuera del OpenAPI | se mantiene después de la fase 10 |
| `WS /ws/arcade` + `arcade_start/question/result/end` | `WS /ws/session/{id}` + `session_start/item_start/item_result/session_end` | mismo motor y transcripts dorados | hasta la fase 7.3, cuando el cliente pasa al canal nuevo |

- Los alias HTTP no dependen de las tablas viejas (`questions`, `arcade_runs`, `matches`):
  por eso sobreviven al retiro de esas tablas en la fase 10.
- Cada socket habla **un solo** protocolo: los mensajes `arcade_*` no aparecen en
  `/ws/session/{id}` y los canónicos no aparecen en `/ws/arcade`.
- El 1v1 no tiene todavía un canal canónico: `WS /ws/room/{code}` con sus mensajes
  `room_state`, `match_start`, `round_start`, `round_result` y `match_end` es la única
  superficie y no cambia.
- El cliente nunca lee las tablas: cualquier detalle de persistencia es interno.

## Revelación

El servidor duerme `REVEAL_SECONDS` (default `2.5`) entre el `round_result` / `arcade_result`
y la ronda o pregunta siguiente. El `ends_at` de la próxima se calcula **después** de la
pausa: el reloj no gasta la revelación. El final de partida no lleva pausa extra.

El cliente no retiene la ronda por su cuenta: dibuja el resultado y espera el próximo
`round_start` / `arcade_question`.

## Códigos de error

| Código | HTTP | Cuándo |
|---|---|---|
| `AUTH_REQUIRED` | 401 | Falta el token, venció o no es válido (HTTP y WS) |
| `ADMIN_REQUIRED` | 401 | Falta o no coincide `X-Admin-Token` |
| `NICK_LENGTH` | 400 | Nick fuera de 1–16 |
| `NICK_FORBIDDEN` | 400 | Nick en la lista corta de prohibidos |
| `NICK_TAKEN` | 409 | Otro usuario vivo usa ese nick |
| `ROOM_NOT_FOUND` | 404 | Código inexistente o sala vencida |
| `MODE_NOT_FOUND` | 404 | No hay un modo registrado con ese `code` |
| `MODE_NOT_SOLO` | 422 | El modo no se juega como sesión solo |
| `INVALID_CONFIG` | 422 | El `config` no valida contra el `config_schema` del modo |
| `MODE_WITHOUT_RANKING` | 404 | El modo pedido no publica ranking |
| `VALIDATION_ERROR` | 422 | Body, query o `kind` inválido (incluye el campo en `message`) |
| `IMPORT_FORMAT` | 400 | Archivo no UTF-8, encabezado o JSON roto, extensión rara |
| `RATE_LIMITED` | 429 | Más de N pedidos por minuto desde la misma IP |

En el WS (todos por `t: "error"`):

| Código | Cuándo |
|---|---|
| `ROOM_FULL` | Un tercero intenta entrar a una sala de 2 |
| `NOT_READY` | `start` sin dos jugadores o desde un estado que no es `waiting` |
| `NO_QUESTIONS` | No hay preguntas para servir en ese tramo |
| `ROUND_MISMATCH` | `answer` de una ronda que ya no está en vuelo |
| `RUN_NOT_STARTED` | `answer` en el arcade antes de `start` / sin corrida |
| `NOT_PLAYING` | La sesión no existe, es de otro usuario, ya terminó o no hay ronda en vuelo |
| `ALREADY_STARTED` | Ya hay un socket jugando esa sesión |
| `SESSION_NOT_STARTED` | La sesión no se pudo abrir (fallo de base al cargar el primer ítem) |
| `BAD_MESSAGE` | Sobre o `answer` mal formados |
| `UNKNOWN_MESSAGE` | `t` desconocido |
| `ROOM_CLOCK_DOWN` | El reloj del servidor se rindió tras fallos de base (la sala se cierra) |
