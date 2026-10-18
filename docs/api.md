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
- **Rate limit:** 60 s por IP en `POST /auth/guest`, `GET /rooms/{code}` y los WS.
  Al pasarse: `429 RATE_LIMITED`.

## HTTP

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `POST` | `/auth/guest` | opcional | Alta de invitado o token fresco → `201` |
| `GET` | `/me` | sí | Perfil + marcas + historial |
| `PATCH` | `/me` | sí | Cambia el nick → token fresco |
| `DELETE` | `/me` | sí | Baja lógica (`204`) |
| `POST` | `/rooms` | sí | Crea sala 1v1 → `201` |
| `GET` | `/rooms/{code}` | no | Vista previa pública |
| `GET` | `/leaderboard/arcade` | no | Tabla global o semanal |
| `GET` | `/leaderboard/arcade/me` | sí | Posición propia en ambos períodos |
| `GET` | `/admin/questions` | `X-Admin-Token` | Listado del banco (con la correcta) |
| `POST` | `/admin/questions/import` | `X-Admin-Token` | Subida CSV/JSON + informe |
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
punto de vista del jugador. La **posición** no está acá: vive en `/leaderboard/arcade/me`.

### `PATCH /me`

Body `{"nick": "Nuevo"}` → mismo `AuthOut` que el alta (guardar el token nuevo).
Errores: `400 NICK_LENGTH` / `400 NICK_FORBIDDEN` / `409 NICK_TAKEN` / `401 AUTH_REQUIRED`.

### `DELETE /me`

`204`, sin body. El token deja de servir (`401`).

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
`status`: `waiting` | `playing` | `finished` | `expired`. Sala vencida → `404 ROOM_NOT_FOUND`.

### `GET /leaderboard/arcade?period=all|week&limit=1..100`

```json
{ "period": "all",
  "entries": [ { "position": 1, "nick": "Ana", "score": 1240,
                 "achieved_at": "2026-10-17T21:05:00Z" } ] }
```

Criterio: mejor `score` por usuario; empate → **el momento más temprano** en que alcanzó ese
puntaje. La semana corta lunes 00:00 en `America/Argentina/Buenos_Aires`.

### `GET /leaderboard/arcade/me`

```json
{ "global": { "rank": 12, "score": 1240, "achieved_at": "..." },
  "week":   { "rank": null, "score": null, "achieved_at": null } }
```

Los tres campos van juntos: sin corridas en el período, los tres son `null`.

### Admin

`X-Admin-Token: <ADMIN_TOKEN>` en **todas**. Ausente o inválido → `401 ADMIN_REQUIRED`
(mismo mensaje en ambos casos). El token se guarda en `sessionStorage`, nunca en el repo.

**`GET /admin/questions`** — filtros `status` (`draft|published|archived`), `category`,
`difficulty` (1–5), `q` (substring, mayúsculas ignoradas, **tildes no**), `page` (desde 1),
`page_size` (1–100, default 20). Orden `created_at DESC, id DESC`.

```json
{ "items": [ { "id": "uuid", "category": "science", "difficulty": 3,
               "prompt": "...", "options": ["...","...","...","..."],
               "correct_index": 2, "explanation": "...", "source": null,
               "status": "draft", "media_type": "none", "media_url": null,
               "tags": [], "created_at": "...", "updated_at": "..." } ],
  "page": 1, "page_size": 20, "total": 72, "pages": 4 }
```

Es la **única** vista que trae `correct_index`. Categoría desconocida → `422 VALIDATION_ERROR`;
página de más → `200` con `items: []`.

**`POST /admin/questions/import`** — `multipart/form-data`: `file` (CSV o JSON según
extensión) y `status` opcional (`draft` por defecto).

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
- **`answer` repetido** (doble tap, retry) → `ROUND_MISMATCH`; la ronda ya no está en vuelo.

## Pedido pendiente al backend

**Pausa de revelación.** Hoy `room_manager._step` entrega `round_result` y sirve la ronda
siguiente en el mismo instante; en el arcade, cada `answer` encadena la próxima pregunta sin
pausa. Así, el reloj de la próxima ronda corre mientras el cliente todavía muestra el
resultado. Se pide una pausa de **2,5 s** (configurable) entre el resultado y la próxima
ronda o pregunta, en 1v1 y en arcade.

Hasta que exista, la pantalla de partida no se cierra: el cliente no inventa tiempo ni
retiene la ronda por su cuenta.

## Códigos de error

| Código | HTTP | Cuándo |
|---|---|---|
| `AUTH_REQUIRED` | 401 | Falta el token, venció o no es válido (HTTP y WS) |
| `ADMIN_REQUIRED` | 401 | Falta o no coincide `X-Admin-Token` |
| `NICK_LENGTH` | 400 | Nick fuera de 1–16 |
| `NICK_FORBIDDEN` | 400 | Nick en la lista corta de prohibidos |
| `NICK_TAKEN` | 409 | Otro usuario vivo usa ese nick |
| `ROOM_NOT_FOUND` | 404 | Código inexistente o sala vencida |
| `VALIDATION_ERROR` | 422 | Body/query inválido (incluye el campo en `message`) |
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
| `BAD_MESSAGE` | Sobre o `answer` mal formados |
| `UNKNOWN_MESSAGE` | `t` desconocido |
| `ROOM_CLOCK_DOWN` | El reloj del servidor se rindió tras fallos de base (la sala se cierra) |
