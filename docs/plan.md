# Omnisapiens

Trivia online. Backend: FastAPI + Python (proyecto `uv`, CPython 3.12), PostgreSQL 16 +
Redis 7 por `docker compose`, WebSocket. Frontend: SvelteKit + TypeScript (lo hace otra
persona; acá solo se toca `backend/`).

> **Documento único.** Arriba el **estado de sesión** (una pantalla: se lee al empezar y
> se poda en cada paso). Después la **spec viva del MVP** (reglas, protocolo, API,
> diseño) y al final los anexos: **A** (capa de datos y servicios) y **B** (trampas y
> decisiones ya tomadas). Se consulta por fragmento (`grep` o `read` con
> `offset`/`limit`): no hace falta leerlo entero.

## Estado de sesión

### Dónde estamos

Backend en `backend/` (uv, CPython 3.12; FastAPI, Postgres 16 y Redis 7 por `docker compose`). **Jugable y administrable**: HTTP, banco de preguntas e importador (CLI y HTTP), panel de admin con `X-Admin-Token`, motores puros, sala viva con WS, barrendero periódico, arcade con WS, persistencia y **ranking en Postgres**. 7 tablas, migraciones `0001`–`0003`, **543 tests en ~21 s**, cobertura **93 %**.

El arcade cerró sus cuatro cortes y el ranking quedó en SQL (A3.5/A6), no en Redis. El plan del MVP está abajo y el diseño de datos en el **Anexo A**. Verificación estándar antes de commitear: `make up` una vez y `make lint` + `make cov`. El panel se prueba a mano con los `curl` del `README.md`.

La página de prueba vive en `frontend/dev/` (`index.html` + `app.js` + `style.css`) y se sirve con `make web` en `http://localhost:5173` (el API sigue en `:8000`; CORS ya permite ese origen). Es de desarrollo, no el producto: login de invitado, sala 1v1, revancha, arcade, ranking, **sección de admin** (token en `localStorage`) y log crudo de mensajes. No reconecta sola al recargar, el marcador local queda en `0-0` tras reconectar, y duplicar la pestaña puede compartir la sesión.

### Hecho

- [x] Base, `models/` (7 tablas), Alembic `0001`–`0003` y guardia de schema.
- [x] HTTP: JWT, `/auth/guest`, `/me`, `/rooms`, `/leaderboard/arcade` y errores con código.
- [x] Banco de preguntas + importador + CLI + 60 semilla; motores puros y `runtime/`.
- [x] Sala 1v1: `runtime/room.py`, `room_manager` y `ws/room_ws.py` con presencia, gracia y revancha.
- [x] Arcade: `arcade_session`, `ws/arcade_ws`, persistencia (`arcade_runs`/`arcade_answers`) y ranking.
- [x] `GET /me` con marcas (`all_time`/`week`) e historial de arcade y 1v1 (`services/profile.py`), tope 10 y solo `finished`.
- [x] Barrendero periódico (`REAPER_INTERVAL_SECONDS=60`) con lo vivo en memoria excluido, cancelado limpio en el shutdown.
- [x] Auditoría H-01..H-25, README y calidad (ruff/mypy/cobertura/CI).
- [x] Página de prueba (`frontend/dev/`): dos pestañas, sala + revancha, arcade y ranking.
- [x] Admin Fase 1: `GET /admin/questions` paginado y `POST /admin/questions/import` (multipart), con `X-Admin-Token`.
- [x] Sección de admin en la página de prueba: token, listado con filtros y paginación, y subida de CSV/JSON con el informe.

### Próximos pasos

**Ahora: curar la semilla desde el panel.** El panel HTTP y su pantalla están completos; falta el trabajo de contenido (revisar las 60 semilla y publicar lo que corresponda).

- [ ] Fase 1 (curación): revisar la semilla y publicar lo que corresponda desde el panel.
- [ ] Fase 5 (visual; el frontend lo hace otra persona): componentes, íconos SVG, sonidos y teclado.
- [ ] Fase 6: PWA, e2e (Playwright) y documentación.
- [ ] Repasar `docs/observaciones.md` por pendientes P3 sin cerrar.
- [ ] Cerrar §20: repasar la "definición de terminado" del MVP.

> **Trampas y decisiones que no se re-descubren: Anexo B**, al final. Consultarlo por
> `grep` cuando el paso en curso lo pida (auth, tests, reloj, outbox, persistencia, ranking).

---

# Spec viva del MVP

> Contrato del producto: lo que el código ya cumple y lo que debe seguir cumpliendo.
> El *porqué* de cada decisión vive en el código, en los tests y en el Anexo B.

**Dos modos.** (1) **Sala privada 1v1 por código**: dos jugadores, pregunta a la vez,
ambos responden simultáneo, gana quien más puntos junta. (2) **Arcade**: un jugador solo,
dificultad y tiempo progresivos hasta quedarse sin vidas; ranking global y semanal.

**Fuera del MVP:** matchmaking público o salas abiertas; salas de más de 2; modo por
turnos; preguntas con imagen/audio/video (campos listos, sin usar); cuentas reales;
chat, amigos, notificaciones, bots; monetización; despliegue en la nube (queda preparado).

**Escala:** 100–200 concurrentes, una instancia, sin sharding ni colas distribuidas.
**Autoridad:** el servidor decide todo; la respuesta correcta nunca viaja antes de
contestar; los puntajes se calculan en el servidor con su propio reloj.
**Idioma:** interfaz en español; código, tablas, endpoints y variables en inglés.

## Arquitectura

Navegador (SvelteKit, PWA) ⇄ HTTP/JSON + WS/JSON ⇄ API FastAPI, con motor de juego en
memoria y autoritativo. Postgres guarda usuarios, preguntas e historial; Redis guarda
caché, estado vivo, rate limiting y el historial de vistas del arcade. Una sola
instancia alcanza; el estado vivo es uno por proceso (`room_store`, `engine`,
`redis_client`) y escala a multi-instancia cambiando la implementación de `RoomStore`
por una sobre Redis Pub/Sub, sin tocar a quien la usa.

Principios: el motor es **código puro** (sin base, Redis ni red; `now_ms`, `sleep` y
`rng` se inyectan); un modo, un flujo; **cero estado de partida en la base mientras la
partida ocurre** (solo la fila de `matches` al arrancar y el bloque al terminar, cero
escrituras por ronda).

## Estructura

```
backend/    app/{main,config,db,redis,cli,logging_config}.py
            app/models/  app/schemas/  app/security/  app/game/ (motor puro)
            app/runtime/ (estado vivo)  app/services/  app/api/  app/ws/  app/i18n/
            alembic/versions/  seeds/questions.csv  tests/
frontend/   lo de otra persona (dev/ tiene la página de prueba)
docs/       plan.md  observaciones.md
```

## Entorno local

`docker compose` levanta `db` (postgres:16-alpine) y `cache` (redis:7-alpine). Variables
en `backend/.env` (ver `.env.example`): `ENV`, `LOG_LEVEL`, `DATABASE_URL`, `REDIS_URL`,
`JWT_SECRET`, `JWT_TTL_DAYS`, `CORS_ORIGINS`, `ADMIN_TOKEN`, `RECONNECT_GRACE_SECONDS`,
`ROOM_IDLE_TIMEOUT_SECONDS`, `STALE_MATCH_MINUTES`, `WS_IDLE_TIMEOUT_SECONDS`,
`REAPER_INTERVAL_SECONDS`, `RATE_LIMIT_*`.

Comandos (`Makefile`): `make up|down`, `api` (:8000), `web` (:5173), `migrate`, `seed`,
`import FILE=...`, `test`, `cov` (gate de cobertura), `lint`, `check-schema`.

## Reglas del juego

### Constantes

```
CATEGORIES = geography, history, science, art, entertainment, sports
DIFFICULTY_MIN = 1 ; DIFFICULTY_MAX = 5

ONLINE_ROUNDS_OPTIONS = [3, 5, 7]      # default 5
ONLINE_SECONDS_OPTIONS = [10, 20, 30]  # default 20
ONLINE_BASE_POINTS = 100
ONLINE_TIME_BONUS_MAX = 50
MAX_TIEBREAK_ROUNDS = 3

ARCADE_LIVES = 3
ARCADE_SECONDS_START = 20 ; ARCADE_SECONDS_FLOOR = 5 ; ARCADE_SECONDS_STEP_EVERY = 3
ARCADE_DIFFICULTY_TIERS = [0, 4, 10, 18, 28]   # aciertos necesarios para dificultad 1..5
ARCADE_STREAK_BONUS_STEP = 10 ; ARCADE_STREAK_BONUS_MAX = 50

RECONNECT_GRACE_SECONDS = 20 ; ROOM_IDLE_TIMEOUT_SECONDS = 600
ROOM_CODE_LENGTH = 6
ROOM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # sin O, 0, I, 1
```

### Online (1v1)

- **Lobby:** el host crea la sala (`POST /rooms`, estado `waiting`) y comparte el código;
  los dos abren el WS. Con los dos conectados, el host manda `start`. Una sala `waiting`
  sin arrancar expira a los 10 minutos.
- **Ronda:** se elige una pregunta publicada no usada en la partida, categoría al azar,
  dificultad por tramo (rondas 0–1 → 1–2, 2–3 → 2–3, 4–5 → 3–4, 6+ → 4–5). Se manda
  `round_start` con `ends_at`. La ronda se resuelve cuando **los dos** contestaron o al
  vencer el plazo, lo primero. `round_result` trae la correcta, qué eligió cada uno,
  ms, puntos y el marcador. No contestar = incorrecta, cero puntos.
- **Puntaje de ronda:** solo si acertó → `BASE + round(TIME_BONUS_MAX * ratio)`, con
  `ratio = clamp(1 - ms / (seconds * 1000), 0, 1)`. Con 20 s: acertar en 1 s da 148;
  al límite, 100.
- **Fin:** gana el que más puntos tiene. Empate → **rondas de desempate** a mitad de
  tiempo y dificultad 4–5, hasta `MAX_TIEBREAK_ROUNDS = 3`; agotado el tope, empate
  final (`winner_id` nulo). `match_end` trae ganador, puntajes y resumen ronda a ronda.
- **Abandono:** al desconectarse un jugador se pausa el reloj, el rival ve el aviso y
  corre una gracia de 20 s; si vuelve, sigue desde el mismo estado; si no, gana el que
  quedó y la partida queda `abandoned`. Si se van los dos, `void` (no cuenta).
- **Revancha:** al terminar, cuando los dos la piden, arranca una partida nueva en la
  misma sala con la misma config y preguntas nuevas; si uno no la pide, la sala vuelve a
  `waiting` y el host puede arrancar de nuevo con el mismo código.

### Arcade

- Arranca con 3 vidas, dificultad 1, racha 0, puntaje 0 y 20 s por pregunta.
- Dificultad por aciertos acumulados: 0–3 → 1, 4–9 → 2, 10–17 → 3, 18–27 → 4, 28+ → 5.
- Segundos: 20 al inicio, −1 cada 3 aciertos, piso 5.
- `puntos = BASE + round(TIME_BONUS_MAX * ratio) + min(STREAK_BONUS_STEP * streak, MAX)`,
  con `streak` = aciertos consecutivos **antes** de esta pregunta.
- Un error (o no contestar) descuenta vida; a 0 vidas termina. `arcade_end` trae puntaje,
  aciertos, dificultad máxima, mejor racha y la posición en ranking global y semanal.
- Anti-trampa: puntajes y tiempos siempre del servidor; una corrida con tiempos
  imposibles se marca `invalid` y no entra al ranking.

### Selección de preguntas (`services/questions.py`)

- Solo `published` y `language = 'es'`; nunca se repite dentro de la misma partida o corrida.
- En el arcade, además, se evitan las últimas 50 vistas por ese usuario (sorted set de
  Redis `arcade:seen:{user_id}`, 24 h). La sala no necesita esa memoria: su estado ya
  sabe qué salió.
- Si Redis no contesta, **la partida sigue sin historial** (se loguea); lo peor es repetir
  una pregunta. Si no hay preguntas suficientes, se permite repetir como último recurso.
- **La respuesta correcta no viaja con la pregunta**: `RoundQuestion` (al cliente) no
  tiene `correct_index`; vive en `LoadedQuestion`, del lado del servidor.
- Se busca por categoría y dificultad, se descartan las usadas y se elige al azar; vacío →
  ±1 de dificultad → sin categoría. Las opciones se **barajan al servir** y `correct_index`
  se remapea en la misma copia (la pregunta guardada no se toca).

## Protocolo WebSocket

Sobre único: `{"t": "tipo", "id": "opcional", "d": {}}`. Todo tiempo absoluto es epoch
en ms UTC y lo genera el servidor.

### Salas: `WS /ws/room/{code}?token=...`

Cliente → Servidor: `hello {}`, `start {}` (solo host, con 2 jugadores), `answer
{"round","choice"}`, `rematch {}`, `ping {}`.

Servidor → Cliente:

| `t` | `d` |
|---|---|
| `room_state` | `{"code","status","config","you":{"id","nick"},"players":[...],"match_id"}` — al entrar y en cada cambio |
| `match_start` | `{"match_id","config","rounds_total"}` |
| `round_start` | `{"round","question_id","prompt","options":[...],"category","difficulty","ends_at","total_seconds"}` — **sin la correcta** |
| `opponent_answered` | `{"round"}` (no revela qué eligió) |
| `round_result` | `{"round","correct_index","explanation","you":{"choice","ms","points","correct"},"opponent":{...},"scores":{"you","opponent"}}` |
| `reconnect_pending` | `{"seconds_left"}` |
| `opponent_returned` | `{}` |
| `match_end` | `{"winner":"you\|opponent\|tie","scores":{...},"rounds":[...],"reason":"completed\|abandoned"}` |
| `rematch_waiting` | `{}` |
| `error` | `{"code","message"}` |
| `pong` | `{}` |

### Arcade: `WS /ws/arcade?token=...`

Cliente → Servidor: `start {}`, `answer {"round","choice"}`, `ping {}`.

| `t` | `d` |
|---|---|
| `arcade_start` | `{"run_id","lives","seconds"}` |
| `arcade_question` | `{"round","prompt","options","category","difficulty","seconds","ends_at","score","lives","streak","correct_count"}` |
| `arcade_result` | `{"round","correct_index","explanation","you":{...},"score","lives","streak","correct_count"}` |
| `arcade_end` | `{"run_id","score","correct_count","max_difficulty","longest_streak","rank_global","rank_weekly","personal_best","is_new_best"}` |
| `error` / `pong` | `{"code","message"}` / `{}` |

### Cliente

Reconexión con backoff 0.5s→10s; al reconectar manda `hello` y recibe el estado completo
(incluida la ronda en curso con su `ends_at` original). Heartbeat cada 15 s; sin `pong`
en 10 s se considera caída. El cliente **nunca** decide el resultado de una ronda.

## API HTTP

Errores: `{"error": {"code": "...", "message": "..."}}`.

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/auth/guest` | Body `{"nick"?: str}`. Crea o reutiliza invitado → `{"user","token"}`. |
| `GET` | `/me` | Perfil, mejor marca, últimas partidas. |
| `PATCH` | `/me` | Cambia el nick → token fresco. |
| `DELETE` | `/me` | Baja lógica (204). |
| `POST` | `/rooms` | Body `{"rounds":5,"seconds":20}` → `{"code","config"}`. |
| `GET` | `/rooms/{code}` | Vista previa: `code`, `config`, `status`, `host_nick`, `expires_at`, `players`. |
| `GET` | `/leaderboard/arcade?period=all\|week&limit=50` | Posición, nick, puntaje, fecha. |
| `GET` | `/leaderboard/arcade/me` | Posición y mejor marca en ambos períodos. |
| `GET` | `/admin/questions?status=&category=&difficulty=&q=&page=&page_size=` | Listado paginado, `X-Admin-Token` (§13.4). |
| `POST` | `/admin/questions/import` | CSV/JSON multipart + informe, `X-Admin-Token` (§13.4). |
| `GET` | `/health` | Estado de la API, la base y Redis (503 si algo falla). |
| `WS` | `/ws/room/{code}` y `/ws/arcade` | Tiempo real. |

## Autenticación

- Invitado primero: `POST /auth/guest` da de alta con `is_guest = true` y nick generado
  si no se manda. Con un token válido **no** crea a nadie: devuelve el mismo usuario y
  token fresco, e **ignora el nick del body** (la identidad la manda el token).
- Códigos: `AUTH_REQUIRED` (401), `NICK_TAKEN` (409), `NICK_FORBIDDEN`/`NICK_LENGTH`
  (400), `ROOM_NOT_FOUND` (404), `VALIDATION_ERROR` (422). El nick se limpia y valida en
  `security/nicks.py` (1–16, lista corta de palabras prohibidas).
- `GET /me` agrega `best` (`all_time`/`week`), `arcade_runs` y `matches` (hasta 10, solo
  `finished`); los puntajes del 1v1 vienen desde el punto de vista del jugador. La
  posición del ranking vive solo en `/leaderboard/arcade/me`. `GET` refresca
  `last_seen_at` como mucho una vez por minuto.
- JWT HS256 con `sub`, `nick`, `guest`, `iat`, `exp` (30 días), firmado con `JWT_SECRET`.
  Se lee con `algorithms=[ALGORITHM]` explícito y se atrapa `jwt.PyJWTError` entero. Sin
  contraseñas ni refresh ni sesiones en base.
- `Authorization: Bearer ...` en HTTP; `?token=` en los WS (el navegador no deja headers).
- CORS desde `CORS_ORIGINS` (el frontend vive en otro puerto).

## Banco de preguntas

**Import CSV** — encabezado con estas columnas exactas:

```
category,difficulty,prompt,option_a,option_b,option_c,option_d,correct,explanation,source,tags
```

Validación: categoría entre las 6; dificultad 1–5; `prompt` no vacío ≤ 300; las 4 opciones
no vacías y distintas; `correct` en `A`–`D`; `content_hash` = SHA-256 del enunciado
normalizado (NFKD sin diacríticos, minúsculas, sin signos, espacios colapsados). El hash
duplicado se omite y se informa. Informe: importadas, duplicadas y rechazadas con motivo.
El import JSON acepta un array con las mismas claves.

`make seed` carga `backend/seeds/questions.csv` (60, 10 por categoría) y las deja
**`published`**; el importador usa `draft` por defecto (§13.2) y `--status` lo cambia.

**Curación:** las preguntas generadas con IA entran `draft`; un humano las pasa a
`published`. Objetivo recomendado: 20 por categoría y dificultad (600), por tramos.

**Futuro (media):** `media_type`/`media_url` ya soportan imagen/audio; el motor no cambia
(sigue siendo elegir 1 de 4); solo se agrega subir archivos y que la tarjeta sepa
renderizar.

### Panel de administración (`api/routers/admin.py`)

`X-Admin-Token` igual al `ADMIN_TOKEN` del `.env`, comparado con `compare_digest`; la
dependencia cuelga del router `/admin` entero, así una ruta nueva nace protegida. Token
ausente e inválido dan el mismo 401 `ADMIN_REQUIRED`.

- `GET /admin/questions` — filtros `status`, `category`, `difficulty`, `q` (substring,
  mayúsculas ignoradas, tildes **no**) y `page`/`page_size` (20 por defecto, tope 100).
  Devuelve `{items, page, page_size, total, pages}`; cada `item` **sí** trae
  `correct_index` (es la vista de curación). Orden `created_at DESC, id DESC`. Categoría
  desconocida: 422; página de más: 200 con lista vacía.
- `POST /admin/questions/import` — multipart `file` (CSV/JSON según extensión) y `status`
  opcional (`draft` por defecto). Mismo informe que la CLI: `{total, imported,
  duplicated, rejected:[{row, reason}]}`. Errores de archivo: 400 `IMPORT_FORMAT`.

## Ranking

- **Global:** por usuario, su mejor `score` de corridas `finished`; empate resuelto por el
  **momento más temprano en que alcanzó ese puntaje**, y a igualdad de todo, por
  `user_id` (para que la posición no baile).
- **Semanal:** mismo criterio desde el lunes 00:00 en `America/Argentina/Buenos_Aires`
  (`zoneinfo`, comparado como `timestamptz`).
- **Mejor marca personal:** máximo de sus corridas. Se refresca al abrir la pantalla (sin
  push). En Postgres (A3.5), no en Redis.

```sql
SELECT * FROM (
  SELECT DISTINCT ON (u.id) u.id, u.nick, r.score AS best, r.ended_at AS achieved_at
  FROM arcade_runs r JOIN users u ON u.id = r.user_id
  WHERE r.status = 'finished' AND u.deleted_at IS NULL
    -- AND r.ended_at >= :since   -- solo en el semanal
  ORDER BY u.id, r.score DESC, r.ended_at ASC
) AS mejor
ORDER BY best DESC, achieved_at ASC
LIMIT :limit;
```

## Sistema de diseño (frontend)

**Reglas duras (no se negocian):** cero gradientes decorativos; cero emojis (íconos SVG
propios); sombras duras `4px 4px 0 0 var(--ink)` sin blur; bordes `2.5px solid var(--ink)`
en todo interactivo; toda superficie presionable baja 3 px al hacer clic y reduce la
sombra a 1 px; radios contenidos (10 px botones, 14 px tarjetas, `999px` solo badges); la
tipografía se elige, no se hereda; el color de categoría manda en badge y acierto; cero
animaciones de entrada por scroll (animar solo feedback); accesibilidad mínima: foco
visible, contraste AA y todo jugable con teclado (`1`–`4` responde, `Enter` confirma).

```css
:root {
  --ink: #101828; --ink-2: #344054; --ink-3: #667085;
  --paper: #FCF8F0; --paper-2: #F2EADF; --white: #FFFFFF;
  --correct: #2FA36B; --correct-dark: #1E7A4D;
  --wrong: #E14B4B; --wrong-dark: #A32F2F;
  --brand: #2F6BFF; --brand-dark: #1E4FD1; --gold: #D99B1C;
  --cat-geography: #2E9E5B; --cat-history: #C77B2E; --cat-science: #2A6FD6;
  --cat-art: #8A4FD3; --cat-entertainment: #E0498F; --cat-sports: #1E9E9E;
  --r-sm: 10px; --r-md: 14px; --r-full: 999px; --border-w: 2.5px;
  --shadow-hard: 4px 4px 0 0 var(--ink); --shadow-press: 1px 1px 0 0 var(--ink);
  --s-1: 4px; --s-2: 8px; --s-3: 12px; --s-4: 16px; --s-5: 24px; --s-6: 32px; --s-7: 48px; --s-8: 64px;
  --font-display: "Bricolage Grotesque", system-ui, sans-serif;
  --font-ui: "Instrument Sans", system-ui, sans-serif;
}
```

Fuentes autoalojadas en `frontend/static/fonts/` (woff2, `swap`); display en título,
marcador y números grandes, peso 800; UI en el texto común.

**Componentes:** `Button` (primary/secondary/ghost/danger; md/lg), `AnswerTile` (idle/
selected/correct/wrong/disabled; alto ≥ 64 px móvil, tecla numérica visible), `CategoryBadge`,
`TimerRing` (alerta y pulso en los últimos 5 s), `PlayerPanel`, `Scoreboard`, `CodeInput`
(6 casillas), `NickInput`, `Modal` (fondo plano, sin blur), `Toast`, `LifeStrip`.
**Sin librería de UI ni Tailwind**: CSS propio con variables.

**Sonido:** `tick`, `reveal`, `correct`, `wrong`, `match_start`, `match_win`, `match_lose`,
`best_score` en `static/assets/sfx/` (mp3/ogg, < 60 KB, CC0). Se inicializa tras la
primera interacción; interruptor de silencio persistido.

**Pantallas:** inicio (dos botones), jugar (crear/unirse), lobby (código gigante),
partida, revelación, fin (ganador + resumen + revancha), arcade, fin de arcade, ranking
(global/semanal) y admin de preguntas.

**Frontend:** mobile first, columna máx. 480 px, sin scroll en partida, táctiles ≥ 44 px;
stores `sessionStore`/`matchStore`/`arcadeStore` con máquinas de estados; `ws.ts` con
reconexión y heartbeat. **PWA:** manifest + service worker (`generateSW`), cachea app
shell; el juego **no** funciona offline. **i18n:** todas las cadenas en `es.ts` y
`app/i18n/es.json`; ninguna cadena visible en un componente.

## Testing

- Motores puros: acierto rápido, al límite, error, sin respuesta, empate y desempate,
  progresión de dificultad y tiempo, corte por vidas. Tabla exacta de puntajes.
- `test_questions_service.py`: nunca se repite en una partida, respeta la dificultad, no
  explota sin preguntas. `hasattr` vigila que `RoundQuestion` no filtre `correct_index`.
- `test_constraints_*.py`: **un test por regla de la base**, contra Postgres real exigiendo
  el constraint (nada de SQLite). `test_schema_matches_models.py` es la guardia contra el
  drift modelos↔migración (Alembic no compara `CHECK`).
- `test_nicks.py`/`test_tokens.py` (seguridad sin HTTP), `test_auth_api.py`, `test_importer.py`,
  `test_question_bank.py`, `test_rooms_api.py`, `test_room_ws.py` (partida completa con
  desconexión y reconexión) y `test_arcade_ws.py`.
- Frontend (otra persona): `svelte-check`, y Playwright para una partida 1v1 completa y un
  arcade hasta el final. **CI** (`.github/workflows/ci.yml`): Postgres y Redis como
  services, `ruff`, `mypy`, `pytest` (con cobertura).

## Fases (roadmap)

| Fase | Entregable | Estado |
|---|---|---|
| 0 Esqueleto | monorepo, compose, CI, `/health`, inicio con tokens | ✅ |
| 1 Identidad y contenido | invitado + token, nicks, import, panel, 60 semilla | ✅ (falta curación) |
| 2 Salas y presencia | dos navegadores por código, sala llena, host cae, expira | ✅ backend |
| 3 Partida online | rondas cronometradas, revelación, puntajes, desempate, gracia, revancha | ✅ backend |
| 4 Arcade y ranking | 3 vidas, progresión, corte semanal, récord personal | ✅ backend |
| 5 Identidad visual | 9 componentes, SVG propios, sonido, teclado, sin scroll, ≤250 KB JS | frontend |
| 6 PWA, e2e y docs | instalable, Playwright en CI, plan y README al día | frontend |
| 7 (opcional) Publicar | `docker-compose.prod.yml`, `docs/deploy.md` | pendiente |

## Definición de terminado del MVP (§20)

1. Dos navegadores juegan un 1v1 completo entrando por código: rondas cronometradas,
   revelación, marcador y ganador.
2. Hay desempate, revancha y desconexión con 20 s de gracia.
3. El arcade sube dificultad, baja tiempo, pierde las 3 vidas y entra al ranking global y
   semanal.
4. El cliente no puede conocer la respuesta antes de contestar y todo puntaje sale del servidor.
5. ≥ 60 preguntas cargadas por el importador, repartidas entre las 6 categorías.
6. El CI pasa en verde, incluidas las e2e.
7. La interfaz no tiene gradientes decorativos ni emojis, y todos los íconos son SVG propios.
8. Levantar el proyecto desde cero toma a lo sumo cinco comandos documentados.

## Riesgos y despliegue

| Riesgo | Mitigación |
|---|---|
| Faltan preguntas y las partidas repiten | banco por tramos con el importador; el motor tolera el faltante |
| Reloj del cliente como trampa | todos los tiempos son del servidor; el cliente solo dibuja |
| El estado vivo en memoria se pierde al reiniciar | cada cambio de sala se publica en Redis (multi-instancia sin cambiar el modelo) |
| El diseño se vuelve genérico al crecer | las reglas duras de diseño y el criterio de la Fase 5 |

Deploy (fuera del MVP): `Dockerfile` desde la Fase 0, toda la config por variables de
entorno, estado de sala en memoria + Redis con Pub/Sub para escalar horizontalmente.

---

# Anexo A — Capa de datos y servicios

> Escrito antes de implementar `models/`, Alembic y WS. Estado: **acordado y aplicado**
> en las migraciones `0001`–`0003` (los ⚠️ de A7, confirmados).

## A1. Principios

1. **Postgres es la fuente de verdad**; Redis es caché y estado vivo: si cae, el juego se
   degrada, no se rompe.
2. **Cero migraciones descartables**: lo irreversible se decide ahora.
3. **El tipo previene el bug**, no la disciplina (ej.: es imposible armar la ronda con la
   respuesta correcta).
4. **Nada de SQLite en tests** (no tiene `jsonb`, índices parciales ni `CHECK` con regex).
5. **Ningún estado inválido persistible**: toda regla que entre en un `CHECK` o un índice
   único vive ahí, no solo en Python.

## A2. Decisiones irreversibles

| Decisión | Por qué ahora |
|---|---|
| `MetaData(naming_convention=...)` desde la primera migración | sin esto los constraints quedan anónimos y cada `drop_constraint` es adivinanza |
| Enums como `varchar` + `CHECK`, no `ENUM` nativo | agregar una categoría es un `ALTER` de un check, y queda grepeable |
| `questions.options` como `jsonb` array de 4 | el `CHECK` valida forma y largo; "no vacías ni repetidas" va en Python (Postgres no admite subconsultas en `CHECK`) |
| `match_rounds` guarda `correct_index`, `difficulty` y `seconds` | cada fila es autosuficiente: auditar y recomputar años después. Agregar columnas después es fácil; rellenarlas, imposible |
| `content_hash` con normalización congelada | si el algoritmo cambia, los hashes viejos quedan inválidos y entran duplicados: se define una vez, con vectores fijos |
| Índice único **parcial** de `nick` (`WHERE deleted_at IS NULL`) | con un único global, el borrado lógico bloquea el nick para siempre |
| Desempate del ranking definido ahora | mejor puntaje `DESC`, empate por el **momento más temprano** en que se alcanzó (no `MAX(ended_at)`, que es arbitrario e inestable) |

## A3. Arquitectura

- **A3.1 El tipo impide filtrar la respuesta.** `RoundQuestion` (sin índice correcto) y
  `GraderQuestion` (con `correct_index` y explicación). El WS solo puede construir
  `round_start` con la primera; filtrarla exige pedir la segunda. Test: el dict no tiene la clave.
- **A3.2 La partida se escribe en dos momentos.** `INSERT` de `matches` con `status =
  playing` al arrancar y `UPDATE` + `INSERT` en bloque de `match_rounds` al terminar. El
  estado `void` necesita una fila que exista; cero escrituras por ronda. El barrendero
  marca `void` toda partida `playing` más vieja que N minutos, salvo la que el proceso tiene viva.
- **A3.3 `score_a`/`score_b` son copia derivada,** escritas solo por el motor desde el
  historial de rondas (una verdad, una copia).
- **A3.4 `matches` con `player_a_id`/`player_b_id`,** no tabla de jugadores (suficiente
  para 1v1; "mis partidas" es un `OR` entre dos índices).
- **A3.5 Ranking en Postgres, no Redis** (menos sincronización, menos bugs).
- **A3.6 `RoomStore` es un protocolo** con implementación en memoria y `asyncio.Lock` por
  sala; multi-instancia = otra implementación, sin tocar a quien la usa.
- **A3.7 Redis caído no rompe el arcade**: se atrapa y loguea; degrada a repetir preguntas
  y el ranking sigue funcionando.

## A4. Esquema

Convenciones: `snake_case`; PK `uuid` con `default=uuid.uuid4` en Python; timestamps
`timestamptz` UTC con `server_default=now()`.

| Tabla | Integridad | Índices |
|---|---|---|
| `users` | PK uuid; `nick` 1–16; `email`/`provider` nulos; `deleted_at` para borrado lógico | único parcial de `nick` entre vivos (funcional sobre `lower(nick)`) |
| `questions` | `category` en 6; `difficulty` 1–5; `prompt` ≤ 300; `options` jsonb de 4; `correct_index` 0–3; `status` draft/published/archived; `content_hash` único; `media_type` none/image/audio con "si no es none, `media_url` no es nulo" | `(status, category, difficulty)`; único en `content_hash` |
| `rooms` | `host_user_id` FK (**el creador es el host**); `code` varchar(6) único con `CHECK` del alfabeto; `config` jsonb; `status` waiting/playing/finished/expired | `(status, expires_at)`; `host_user_id` |
| `matches` | FK a `rooms` (`SET NULL`) y a los dos jugadores; `config` jsonb; `status` playing/finished/abandoned/void; `winner_id` nulo en empate/void; scores ≥ 0 | `(status, started_at)`, `player_a_id`, `player_b_id` |
| `match_rounds` | FK `CASCADE`; único `(match_id, round_index)`; elecciones 0–3 o nulas; `ms` ≥ 0; `points` ≥ 0; + `correct_index`, `difficulty`, `seconds` | FKs |
| `arcade_runs` | FK a `users`; `score`, `correct_count`, `max_difficulty`, `longest_streak` (≤ `correct_count`); `status` playing/finished/invalid; `ended_at` nulo ⇔ `playing` | `(user_id, score DESC)`, `(score DESC)`, `(ended_at)`, los tres **parciales** `WHERE status='finished'` |
| `arcade_answers` | FK `CASCADE`; único `(run_id, round_index)`; `chosen_index` nulo si no contestó; `is_correct`, `ms`, `points`, `rejected` | FKs |

Notas que quedan fijadas:

- `config` jsonb con forma `{"rounds": n, "seconds": s}`, serializado desde la misma clase
  `MatchConfig` del motor: el formato no puede divergir.
- `match_rounds` copia `correct_index`/`difficulty`/`seconds` (fila auditable) y guarda
  `a_correct`/`b_correct` explícitos: fuera de la ventana hasta el acierto cuenta mal, no
  se derivan de `(choice, correct_index)`.
- `status = invalid` existe para el anti-trampa; el umbral concreto es una constante en
  `game/constants.py`.
- Corte semanal: lunes 00:00 local con `zoneinfo`, comparado como `timestamptz`.
- `last_seen_at` se toca al crear sesión y al terminar una partida, no en cada request.
- **Sin revocación de tokens** (consecuencia aceptada del diseño sin sesiones).

## A5. Migraciones y tests

- `alembic/env.py` **async** sobre asyncpg, con `compare_type` y `compare_server_default`.
- **Una migración inicial** que crea todo; nunca `create_all` en runtime. `alembic check`
  en CI falla si los modelos y las migraciones se desincronizaron.
- Tests contra Postgres real (`trivia_test`), migraciones por sesión, cada test en una
  transacción que se revierte, `pytest-asyncio` en modo `auto`. Constraints explícitos:
  se inserta el dato inválido y se exige el error.
- Redis de tests en otra base (`:6379/1` vs `/0`): un `FLUSHDB` no toca el juego.

## A6. Lo que NO se hace

Nada de `create_all` en runtime ni migraciones al arrancar la API; nada de estado de
partida en Postgres mientras la partida ocurre (salvo la fila del match); nada de SQLite
en tests; nada de estado vivo solo en Redis sin la interfaz `RoomStore`; nada de ranking
por sorted sets de Redis en el MVP.

## A7. Puntos confirmados al arrancar

1. ⚠️ Fila de `matches` al arrancar (A3.2) para que `void` sea alcanzable.
2. ⚠️ Desempate del ranking por el momento más temprano del mejor puntaje.
3. ⚠️ Índice único parcial de `nick` para reusar tras el borrado lógico.
4. ⚠️ El host es **quien creó la sala** (`rooms.host_user_id`), no "el primero que entra":
   la fila vive más que las conexiones y el host es el único que elige config y manda `start`.

El §Reglas sigue mandando en el producto y el protocolo; este anexo fija la capa de datos.

---

# Anexo B — Decisiones y trampas (no re-descubrir)

> Memoria del proyecto: lo que ya costó un bug. Se consulta por `grep` cuando el paso lo
> pida. Formato: una línea por decisión, con el porqué cuando no es obvio.

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
- El default del import es `draft`; las 60 semilla entran `published` por flag (`make seed`),
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
