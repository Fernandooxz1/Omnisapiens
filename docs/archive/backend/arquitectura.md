# Backend — arquitectura, entorno y capa de datos

> Archivo histórico. El backend está cerrado: se conserva para responder por qué el servidor
> se comporta como se comporta. El contrato que usa el frontend está en `docs/api.md`.

## En números

FastAPI + CPython 3.12 (proyecto `uv`), PostgreSQL 16 + Redis 7 por `docker compose`,
WebSocket. **7 tablas**, migraciones `0001`–`0003`, **553 tests en ~18 s**, cobertura **94 %**.

Jugable y administrable: HTTP, banco de preguntas e importador (CLI y HTTP), panel de admin
con `X-Admin-Token`, motores puros, sala viva con WS, barrendero periódico, arcade con WS,
persistencia y ranking en Postgres.

- Auditoría H-01..H-25 resuelta (`observaciones.md`), incluido H-07 (guard `SINGLE_PROCESS`)
  y los tests de concurrencia.
- Verificación estándar: `make up` una vez, y después `make lint` + `make cov`.
- Pendiente menor, no urgente: `_pick` fuera del lock y una sola sesión por transición.

## Estructura

```
backend/    app/{main,config,db,redis,cli,logging_config}.py
            app/models/  app/schemas/  app/security/  app/game/ (motor puro)
            app/runtime/ (estado vivo)  app/services/  app/api/  app/ws/  app/i18n/
            alembic/versions/  seeds/questions.csv  tests/
frontend/   la app SvelteKit (dev/ tiene la página de prueba del backend)
docs/       plan.md  api.md  diseno.md  tareas.md  archive/
```

## Entorno local

`docker compose` levanta `db` (postgres:16-alpine) y `cache` (redis:7-alpine). Variables en
`backend/.env` (ver `.env.example`): `ENV`, `LOG_LEVEL`, `DATABASE_URL`, `REDIS_URL`,
`JWT_SECRET`, `JWT_TTL_DAYS`, `CORS_ORIGINS`, `ADMIN_TOKEN`, `RECONNECT_GRACE_SECONDS`,
`ROOM_IDLE_TIMEOUT_SECONDS`, `STALE_MATCH_MINUTES`, `WS_IDLE_TIMEOUT_SECONDS`,
`REAPER_INTERVAL_SECONDS`, `SINGLE_PROCESS`, `RATE_LIMIT_*`.

Fuera de `local`, el despliegue tiene que declarar `SINGLE_PROCESS=1` o la API se niega a
arrancar: el estado vivo (salas y arcade) es del proceso y dos workers serían dos verdades
para el mismo código de sala (H-07).

Comandos (`Makefile`): `make up|down`, `api` (:8000), `web` (:5173), `migrate`, `seed`,
`import FILE=...`, `test`, `cov` (gate de cobertura), `lint`, `check-schema`.

## Testing del backend

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
- **CI** (`.github/workflows/ci.yml`): Postgres y Redis como services, `ruff`, `mypy`,
  `pytest` con cobertura.

## Riesgos y despliegue

| Riesgo | Mitigación |
|---|---|
| Faltan preguntas y las partidas repiten | banco por tramos con el importador; el motor tolera el faltante |
| Reloj del cliente como trampa | todos los tiempos son del servidor; el cliente solo dibuja |
| El estado vivo en memoria se pierde al reiniciar | cada cambio de sala se publica en Redis (multi-instancia sin cambiar el modelo) |
| El diseño se vuelve genérico al crecer | las reglas duras de diseño (`docs/diseno.md`) |

Deploy (fuera del MVP): `Dockerfile` desde la Fase 0, toda la config por variables de
entorno, estado de sala en memoria + Redis con Pub/Sub para escalar horizontalmente. Hoy el
estado vivo es del proceso: fuera de `local` hay que declarar `SINGLE_PROCESS=1` (un solo
worker) o la API se niega a arrancar (H-07); cuando el `RoomStore` sea el de Redis, esa
declaración deja de hacer falta y se levanta sin tocar el resto.

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
  Quedó vigente hasta la fase 5.3; desde entonces el camino en vivo escribe
  `game_sessions` y estas tablas son de solo lectura (ver A4).
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

> **Estado desde la fase 10.** Las tablas `questions`, `matches`, `match_rounds`,
> `arcade_runs` y `arcade_answers` se dropearon en la migración `0006`. El esquema
> vigente del historial es `game_sessions` + `game_participants` + `session_items` +
> `session_attempts`; el banco es `content_items` + `content_solutions`. Las filas de
> abajo quedan como registro de la primera versión, no como esquema actual.

| Tabla | Integridad | Índices |
|---|---|---|
| `users` | PK uuid; `nick` 1–16; `email`/`provider` nulos; `deleted_at` para borrado lógico | único parcial de `nick` entre vivos (funcional sobre `lower(nick)`) |
| `questions` *(retirada en 0006)* | `category` en 6; `difficulty` 1–5; `prompt` ≤ 300; `options` jsonb de 4; `correct_index` 0–3; `status` draft/published/archived; `content_hash` único; `media_type` none/image/audio con "si no es none, `media_url` no es nulo" | `(status, category, difficulty)`; único en `content_hash` |
| `rooms` | `host_user_id` FK (**el creador es el host**); `code` varchar(6) único con `CHECK` del alfabeto; `config` jsonb; `status` waiting/playing/finished/expired | `(status, expires_at)`; `host_user_id` |
| `matches` *(retirada en 0006)* | FK a `rooms` (`SET NULL`) y a los dos jugadores; `config` jsonb; `status` playing/finished/abandoned/void; `winner_id` nulo en empate/void; scores ≥ 0 | `(status, started_at)`, `player_a_id`, `player_b_id` |
| `match_rounds` *(retirada en 0006)* | FK `CASCADE`; único `(match_id, round_index)`; elecciones 0–3 o nulas; `ms` ≥ 0; `points` ≥ 0; + `correct_index`, `difficulty`, `seconds` | FKs |
| `arcade_runs` *(retirada en 0006)* | FK a `users`; `score`, `correct_count`, `max_difficulty`, `longest_streak` (≤ `correct_count`); `status` playing/finished/invalid; `ended_at` nulo ⇔ `playing` | `(user_id, score DESC)`, `(score DESC)`, `(ended_at)`, los tres **parciales** `WHERE status='finished'` |
| `arcade_answers` *(retirada en 0006)* | FK `CASCADE`; único `(run_id, round_index)`; `chosen_index` nulo si no contestó; `is_correct`, `ms`, `points`, `rejected` | FKs |

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
- **Transición (fase 4.3)**: el camino en vivo del arcade ya no escribe
  `arcade_runs`/`arcade_answers`; usa `game_sessions` con sus ítems e intentos. Se
  borraron `game/arcade_engine.py`, `runtime/arcade_session.py` y
  `services/arcade_runs.py`; las reglas del formato viven en `game/modes/arcade.py`.
  Las dos tablas viejas quedaron de solo lectura y se dropearon en `0006`.
- **Transición (fase 5.3)**: el camino en vivo del 1v1 ya no escribe
  `matches`/`match_rounds`; desde 5.2 usa `game_sessions` con ítems, intentos y
  participantes. Se borraron `game/match_engine.py` y `runtime/room.py`; las reglas
  viven en `game/versus_engine.py` y el estado vivo en `runtime/session_store.py`.
  Las dos tablas viejas quedaron de solo lectura y se dropearon en `0006`.

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

1. ⚠️ Fila de `matches` al arrancar (A3.2) para que `void` sea alcanzable. Desde la
   fase 10 ese rol lo cumple la fila `playing` de `game_sessions`.
2. ⚠️ Desempate del ranking por el momento más temprano del mejor puntaje.
3. ⚠️ Índice único parcial de `nick` para reusar tras el borrado lógico.
4. ⚠️ El host es **quien creó la sala** (`rooms.host_user_id`), no "el primero que entra":
   la fila vive más que las conexiones y el host es el único que elige config y manda `start`.
