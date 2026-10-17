# Omnisapiens — Plan de la capa de datos y servicios

> Diseño previo a implementar `models/`, Alembic, repositorios y WebSocket.
> Escrito para no refactorizar después: acá están las decisiones caras de cambiar.
> Estado: **acordado y aplicado**. Los cuatro puntos marcados con ⚠️ (sección 8) están confirmados e implementados en las migraciones `0001`–`0003`.

## 1. Principios

1. **Postgres es la fuente de verdad** de usuarios, preguntas e historial. Redis es caché y estado vivo: si se cae, el juego se degrada, no se rompe.
2. **Cero migraciones descartables.** Lo irreversible se decide ahora; lo cosmético se decide cuando haga falta.
3. **El tipo de retorno previene el bug**, no la disciplina del programador. Ejemplo: es imposible armar el mensaje de ronda con un objeto que incluya la respuesta correcta.
4. **Nada de SQLite en tests.** No soporta `jsonb`, ni índices parciales, ni `CHECK` con regex: daría confianza falsa justo en lo que estamos diseñando.
5. **Ningún estado inválido persistible**: toda regla que pueda vivir en un `CHECK` o en un índice único, vive ahí y no solo en Python.

## 2. Decisiones irreversibles

| # | Decisión | Por qué ahora |
|---|---|---|
| 1 | `MetaData(naming_convention=...)` desde la primera migración | Sin esto los constraints quedan anónimos y cada `drop_constraint` posterior es adivinanza. Retrofittearlo obliga a una migración de churn sobre todas las tablas |
| 2 | Enums como `varchar` + `CHECK`, no `ENUM` nativo | Agregar una categoría es un `ALTER` de un check, no un `ALTER TYPE`; y queda grepeable en la migración |
| 3 | `questions.options` como `jsonb` array de 4 | Es lo que el plan pide. El `CHECK` valida forma y largo; que las opciones no estén vacías ni repetidas se valida en Python (Postgres no admite subconsultas en un `CHECK`) |
| 4 | `match_rounds` guarda `correct_index`, `difficulty` y `seconds` | Con esos campos cada fila es autosuficiente: se puede auditar y recomputar un puntaje histórico. Agregar columnas después es fácil; rellenar las viejas es imposible |
| 5 | Hash de deduplicación con normalización congelada | `content_hash = sha256(texto normalizado)`. Si el algoritmo cambia, todos los hashes existentes quedan inválidos y entran duplicados. Se define una vez, con tests de vectores fijos |
| 6 | Índice único **parcial** de `nick`: `UNIQUE (nick) WHERE deleted_at IS NULL` | Con un único global, un usuario con borrado lógico bloquea su nick para siempre |
| 7 | Regla de desempate del ranking definida ahora | ⚠️ Propuesta: mejor puntaje `DESC`, y empate resuelto por **el momento más temprano en que ese jugador alcanzó ese puntaje**. El SQL del plan ordena por `MAX(ended_at) ASC`, que significa "quien jugó por última vez hace más tiempo va primero": arbitrario e inestable |

## 3. Decisiones de arquitectura

**3.1 El tipo impide filtrar la respuesta correcta.** El repositorio devuelve dos formas distintas:

- `RoundQuestion`: id, enunciado, opciones, categoría, dificultad. **Sin** índice correcto.
- `GraderQuestion`: lo anterior más `correct_index` y explicación.

La capa de WebSocket solo puede construir `round_start` con la primera. Filtrar la respuesta correcta exige pedir explícitamente la segunda, así que el error deja de ser un descuido posible. Test: el diccionario del mensaje no contiene la clave.

**3.2 La partida se escribe en dos momentos, no en cada ronda.** ⚠️ Me aparto del plan ("la base se escribe al terminar"):

- Al arrancar: `INSERT` de la fila de `matches` con `status = playing`.
- Al terminar: `UPDATE` del match + `INSERT` en bloque de `match_rounds`.

Motivo: el estado `void` del plan necesita una fila que exista. Si solo se escribe al final, un proceso que muere en medio no deja rastro y `void` es inalcanzable. Sigue habiendo cero escrituras por ronda. Un barrendero al arrancar marca como `void` toda partida `playing` más vieja que N minutos.

**3.3 `score_a` / `score_b` son una copia derivada.** Se guardan para listados rápidos, y el único que los escribe es el motor, que los deriva del historial de rondas. Una sola verdad, una sola copia.

**3.4 `matches` con `player_a_id` / `player_b_id`, no tabla de jugadores.** Como pide el plan. "Mis últimas partidas" queda como `OR` entre dos índices: suficiente para 1v1 fijo. Cambiar a una tabla de jugadores es posible pero no gratis, y solo hace falta si alguna vez se juega de a más de dos.

**3.5 Ranking en Postgres, no en Redis.** Menos sincronización, menos bugs. Los sorted sets de Redis quedan para cuando se mida que hace falta.

**3.6 La interfaz del estado de sala se define ahora, la implementación después.** Es la pieza con más chance de reescritura. Se define un protocolo `RoomStore` y una implementación en memoria con `asyncio.Lock` por sala. Multi-instancia = nueva implementación de la misma interfaz, sin tocar a quien la usa.

**3.7 Redis caído no rompe el arcade.** Errores de Redis se atrapan y se loguean (mismo criterio que `/health`): el arcade degrada a repetir preguntas y el ranking sigue funcionando.

## 4. Esquema

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

## 5. Migraciones y tests

- `alembic/env.py` **async** sobre el engine de asyncpg, con `compare_type=True` y `compare_server_default=True` para que autogenerate no ignore cambios de tipo o de default.
- **Una migración inicial** que crea todo. Nunca `create_all` en código de aplicación.
- **`alembic check` en CI**: falla si los modelos y las migraciones se desincronizaron. Es el guardarraíl contra "funciona en mi máquina porque yo tenía la tabla".
- Tests contra Postgres real, base `trivia_test`, migraciones una vez por sesión, cada test dentro de una transacción que se revierte. `pytest-asyncio` en modo `auto`.
- Los tests de constraints son explícitos: se intenta insertar el dato inválido y se exige el error. Es la única forma de saber que el `CHECK` está donde creemos.

## 6. Orden de implementación

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

## 7. Lo que NO se hace

- Nada de `create_all` en runtime, ni migraciones automáticas al arrancar la API.
- Nada de estado de partida en Postgres mientras la partida ocurre (salvo la fila del match).
- Nada de SQLite en tests.
- Nada de escribir el estado vivo solo en Redis sin la interfaz `RoomStore` de por medio.
- Nada de ranking por sorted sets de Redis en el MVP.

## 8. Puntos a confirmar al arrancar

1. ⚠️ Fila de `matches` al arrancar (3.2) en vez de solo al terminar, para que `void` sea alcanzable.
2. ⚠️ Desempate del ranking por el momento más temprano en que se alcanzó el mejor puntaje (decisión 7).
3. ⚠️ Índice único parcial de `nick` para permitir reuso tras el borrado lógico (decisión 6).
4. ⚠️ (confirmado 2026-10-17) El host de la sala es **quien la creó**, y se guarda en `rooms.host_user_id` (FK a `users` + índice). Una columna en la fila y no estado en memoria: la sala vive más que las conexiones, y el host es el único que elige la config y manda `start`.

## 9. Relación con el plan general

`docs/mvp-plan.md` sigue mandando en el producto, las reglas del juego y el protocolo de mensajes. Este documento solo fija la capa de datos y servicios, y en los cuatro puntos marcados ⚠️ (sección 8) propone un cambio respecto del plan. Ya están confirmados y reflejados en `docs/mvp-plan.md` (secciones 8 y 14) y en `docs/estado.md`.
