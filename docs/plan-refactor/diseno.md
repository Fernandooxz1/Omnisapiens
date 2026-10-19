# Omnisapiens — diseño del backend multi-modo

> **Estado: diseño cerrado, sin implementar.** Este documento manda sobre el refactor.
> Si una tarea necesita una decisión que no está acá, se para y se pregunta: no se
> diseña sobre la marcha.
>
> Fecha: 2026-10-19. Base: `main` @ `fce8ce0` (553 tests, cobertura 93.82 %).

## 1. Decisiones cerradas

1. **Ranking por modo, nunca global.** Un modo declara si tiene ranking o no
   (`GameMode.ranking`). En la v1 solo lo tiene `trivia_arcade`.
2. **El rosco es opcional.** No está en el camino crítico. El refactor tiene que dejar
   las bases listas para agregarlo, pero no se implementa hasta que se decida.
3. **`trivia_arcade` es el único modo con ranking al principio.** `trivia_versus` no
   tiene ranking. Un modo nuevo entra al ranking solo con una decisión explícita.
4. **Un solo proceso.** El estado vivo sigue en memoria; `SessionStore` es una interfaz
   para poder mudarlo a Redis el día que haga falta.
5. **El servidor es la única autoridad.** Tiempos, corrección, puntaje y ganador salen
   del servidor. El cliente solo dibuja.
6. **La respuesta nunca viaja antes de tiempo.** El contenido público y la solución son
   tipos distintos y tablas distintas.
7. **Compatibilidad durante el refactor.** Los mensajes WS actuales no cambian hasta
   que el frontend migre. Los transcripts dorados son el candado.
8. **Una tarea por sesión, un commit por tarea.** Nada de trabajo sin commitear.

## 2. Conceptos: contenido, formato y modo

La confusión que hay que evitar es tratar "trivia 1v1", "arcade" y "rosco" como si fueran
lo mismo. No lo son:

| Concepto | Qué define | Ejemplos |
|---|---|---|
| **ContentKind** | Cómo se guarda, valida, importa y sirve el contenido | `quiz`, `rosco`, `song`, `movie` |
| **PlayFormat** | Cómo corre una sesión: sillas, reloj, progresión, final | `versus`, `arcade`, `fixed_solo`, `board_solo` |
| **GameMode** | La combinación registrada que el jugador elige | `trivia_arcade`, `trivia_versus`, `rosco_solo` |

Esto permite que `trivia_arcade` y `trivia_versus` **compartan el mismo `quiz`** sin
duplicar contenido, y que `rosco_solo` reutilice el runtime de sesiones solo.

### 2.1 Modos de la v1

| `mode` | `content_kind` | `format` | Ranking | Estado |
|---|---|---|---|---|
| `trivia_arcade` | `quiz` | `arcade` | **sí** | actual, se porta |
| `trivia_versus` | `quiz` | `versus` | no | actual, se porta |
| `rosco_solo` | `rosco` | `board_solo` | no | opcional (fase 8) |
| `song_solo` | `song` | `fixed_solo` | no | opcional (fase 9) |
| `movie_solo` | `movie` | `fixed_solo` | no | opcional (fase 9) |

`GET /modes` es la fuente de verdad para el frontend: nombre, formato, input, medios,
ranking y esquema de configuración. El menú no se hardcodea en dos lugares.

## 3. Contratos

### 3.1 `GameMode`

```python
@dataclass(frozen=True)
class GameMode:
    code: str                        # "trivia_arcade"
    content_kind: str                # "quiz"
    play_format: str                 # "arcade"
    ruleset_version: int             # se guarda en cada sesión
    content: ContentKind
    rules: RoundRules
    progression: Progression
    scoring: ScoringPolicy
    config_schema: type[BaseModel]
    public_schema: type[BaseModel]
    ranking: RankingPolicy | None    # None = sin ranking
    players: Players                 # SOLO | VERSUS
    connection: ConnectionPolicy     # EPHEMERAL | RESILIENT
    schedule: Schedule               # LINEAR | BOARD
```

### 3.2 `ContentKind`

```python
class ContentKind(Protocol):
    code: str
    schema_version: int

    def parse_row(self, raw: Mapping[str, str]) -> ContentDraft: ...
    def fingerprint(self, draft: ContentDraft) -> str: ...
    async def candidates(self, session, *, config) -> list[ItemRef]: ...
    async def load(self, session, ref: ItemRef) -> LoadedItem: ...
```

`LoadedItem` contiene `public: PublicItem` y `solution: Solution`. El borde solo recibe
`public`; la solución solo la ve `grade()`.

### 3.3 `RoundRules`

```python
class RoundRules(Protocol):
    def serve(self, item: LoadedItem, *, difficulty: int, seconds: int,
              now_ms: int, rng: Random) -> ServedItem: ...
    def grade(self, served: ServedItem, submission: Submission,
              *, now_ms: int) -> Verdict: ...
```

`Submission` es una unión discriminada:

```python
ChoiceSubmission(index: int)
TextSubmission(text: str)
LetterSubmission(letter: str, word: str)
OrderSubmission(order: tuple[int, ...])
```

`Verdict` trae lo común (`correct`, `elapsed_ms`, `rejected`) y un `detail` tipado por
modo. La ventana temporal y el "fuera de ventana no existe" son compartidos.

### 3.4 `Progression` y `ScoringPolicy`

- `Progression.next(state, format) -> Step`: dificultad, segundos y si la sesión sigue.
  `arcade` implementa las curvas actuales; `board_solo` devuelve un tablero fijo.
- `ScoringPolicy.points(verdict, elapsed_ms, seconds, state) -> int`: el bonus de tiempo
  es compartido; el bonus de racha es del formato `arcade`; rosco puede usar otra regla.

Extraído en 1.2 (`backend/app/game/solo_engine.py`):

```python
SoloRules(lives, difficulty_tiers, seconds_start, seconds_floor,
          seconds_step_every, streak_bonus_step, streak_bonus_max)

SoloEngine(rules).start() -> SoloRun
SoloEngine(rules).next_question(run, *, question_id, now_ms) -> ServedQuestion
SoloEngine(rules).resolve(run, served, *, correct_index, answer) -> Resolved[run]
```

`SoloRun` lleva sus `rules` (así las vidas se validan contra el formato) y no guarda
historial: `resolve` devuelve el `RoundRecord`. Los valores actuales viven en
`ARCADE_RULES` (`arcade_engine.py`), no en el motor; `ArcadeRun` es la fachada de
compatibilidad hasta la fase 4. En 1.3, `Progression` y `ScoringPolicy` se apoyan en
estas curvas.

Implementado en 1.3 (`backend/app/game/modes/`):

```python
# base.py
GameMode(code, content_kind, play_format, ruleset_version, content, rules,
         progression, scoring, config_schema, public_schema, ranking,
         players, connection, schedule)

ItemRef(content_id, difficulty, categories)
PublicItem(payload, media_type="none", media_url=None)
Solution(payload)
LoadedItem(content_id, public, solution)
ContentDraft(schema_version, public, solution, difficulty, categories, language="es")

SessionState: round_index, score, streak, correct_count, longest_streak,
              max_difficulty, finished
Step(difficulty, seconds, finished=False)
Progression.next(state, format) -> Step
ScoringPolicy.points(verdict, elapsed_ms, seconds, state) -> int
```

- `ContentKind.candidates/load` reciben `AsyncSession` y `config: BaseModel`; el
  `payload` público y la `Solution` nunca comparten estructura.
- `RoundRules.grade` es la única puerta a `core.settle`: ningún modo reimplementa la
  ventana.
- `RankingPolicy` es un marcador en la v1: `ranking is not None` alcanza para saber si
  el modo rankea; la forma concreta se cierra en 3.4/6.1.
- `registry.py` expone `ModeRegistry` (`register`/`get`/`all`) y el singleton
  `registry`; arranca vacío y los modos se registran en la fase 6.
- `tests/test_modes_conformance.py` parametriza por `registry.all()` (hoy 0 casos) y
  deja listas las aserciones de payload sin solución, determinismo, ventana y puntos
  no negativos.

## 4. Datos

### 4.1 Contenido

```sql
content_items (
  id uuid pk,
  kind text not null,                 -- quiz | rosco | song | movie
  schema_version smallint not null,
  status text not null,               -- draft | published | archived
  language text not null default 'es',
  difficulty smallint not null check (difficulty between 1 and 5),
  categories text[] not null default '{}',
  payload jsonb not null,             -- público: enunciado, opciones, media
  media_type text not null default 'none',
  media_url text,
  content_hash char(64) not null unique,
  supersedes_id uuid references content_items(id),
  created_at timestamptz, updated_at timestamptz,
  check (jsonb_typeof(payload) = 'object'),
  check ((payload->>'v')::int = schema_version)
)

content_solutions (
  content_id uuid pk references content_items(id) on delete cascade,
  payload jsonb not null              -- correct_index, answer, explanation
)
```

- **Solución en tabla aparte**: el camino público no la puede filtrar con un `SELECT *`.
- **Publicado inmutable**: editar = nueva fila con `supersedes_id`.
- **`content_hash`** único, con la normalización congelada por `ContentKind`.
- Índices: `(kind, status, difficulty)`, GIN en `categories`, funcional por modo cuando
  haga falta (ej. `payload->>'letter'` para rosco).

### 4.2 Sesiones

```sql
game_sessions (
  id uuid pk,
  mode text not null,
  content_kind text not null,
  play_format text not null,
  ruleset_version smallint not null,
  status text not null,               -- playing | finished | abandoned | void | invalid
  config jsonb not null,
  owner_user_id uuid references users(id),   -- solo; null en versus
  room_id uuid references rooms(id),
  score integer not null default 0,
  correct_count integer not null default 0,
  longest_streak integer not null default 0,
  max_difficulty smallint not null default 1,
  started_at timestamptz not null,
  ended_at timestamptz,
  check ((status = 'playing') = (ended_at is null)),
  check (score >= 0 and correct_count >= 0),
  check (longest_streak between 0 and correct_count)
)

game_participants (
  session_id uuid references game_sessions(id) on delete cascade,
  seat smallint not null,
  user_id uuid not null references users(id),
  score integer not null default 0,
  outcome text,                       -- win | lose | draw | abandoned | void
  primary key (session_id, seat),
  unique (session_id, user_id)
)

session_items (
  id uuid pk,
  session_id uuid references game_sessions(id) on delete cascade,
  item_key text not null,             -- "0", "1" o "A", "B"
  position smallint not null,
  content_id uuid references content_items(id) on delete set null,
  difficulty smallint not null,
  seconds integer not null,
  served_at timestamptz not null,
  deadline_at timestamptz,
  closed_at timestamptz,
  solution_snapshot jsonb not null,   -- autocontenido para auditar/replay
  unique (session_id, item_key)
)

session_attempts (
  id uuid pk,
  item_id uuid references session_items(id) on delete cascade,
  attempt_seq smallint not null,
  seat smallint not null default 0,
  submitted_at timestamptz not null,
  submission jsonb not null,
  correct boolean not null,
  elapsed_ms integer not null check (elapsed_ms >= 0),
  points integer not null check (points >= 0),
  rejected text,
  unique (item_id, seat, attempt_seq)
)
```

- `item_key` + `attempt_seq` cubren lineal y tablero sin dos esquemas.
- `solution_snapshot` hace la fila autocontenida aunque el contenido se archive (mismo
  criterio que `match_rounds.correct_index`).
- Los contadores de `game_sessions` son proyección: los escribe el motor al cerrar.
- `rooms` suma `mode` (default `trivia_versus`); su `config` pasa a validarse por el
  `config_schema` del modo y la base solo exige `jsonb_typeof(config) = 'object'`.
  Es una pérdida deliberada de rigidez del `CHECK`; se compensa con tests de contrato.

### 4.3 Ranking

```sql
create index ix_sessions_ranking
  on game_sessions (mode, score desc, ended_at asc)
  where status = 'finished' and owner_user_id is not null;

create index ix_sessions_best_by_user
  on game_sessions (mode, owner_user_id, score desc)
  where status = 'finished' and owner_user_id is not null;
```

- Solo modos `SOLO` con `ranking != None` en la v1.
- Desempate: `ended_at ASC` (el momento más temprano en que se alcanzó el puntaje).
- `GET /leaderboard/{mode}` devuelve `404 MODE_WITHOUT_RANKING` si el modo no tiene
  ranking. El frontend lo oculta usando `GET /modes`.
- `/leaderboard/arcade` queda como alias de `/leaderboard/trivia_arcade`.

## 5. Protocolo y anti-fuga

Protocolo canónico (nuevo):

```
session_start   { session_id, mode, config, ... }
item_start      { item_key, position, ends_at, total_seconds, payload }
item_result     { item_key, correct, submission?, solution?, points, scores? }
session_end     { score, correct_count, ..., ranking? }
session_state   { ... }        // reconexión
error           { code, message }
```

- `payload` lo valida el `public_schema` del modo. No hay una clase de mensaje por modo.
- `solution` recién aparece en `item_result`, cuando el ítem ya cerró.
- **Compatibilidad**: durante las fases 4–7, `trivia_arcade` y `trivia_versus` siguen
  emitiendo los mensajes actuales (`arcade_*`, `round_*`, `match_*`) mediante un
  adaptador. Los transcripts dorados garantizan que no cambió nada.
- **Test de fuga**: recorre todos los modos, serializa el payload público y falla si
  aparece `solution`, `answer`, `correct_*` o el valor de la solución.

## 6. Migración

Migraciones separadas, una por fase:

| Migración | Fase | Qué hace |
|---|---|---|
| `0004_content.py` | 2 | crea `content_items` y `content_solutions` |
| `0005_sessions.py` | 3 | crea `game_*` y agrega `rooms.mode` |
| `0006_media.py` | 9 (opcional) | crea `media_assets` |
| `0007_drop_legacy.py` | 10 | dropea las tablas viejas |

El backfill **no** va dentro de la migración: es un comando idempotente de `app/cli.py`
(`backfill-content`, `backfill-sessions`), con reporte y test. Una migración no debería
depender de datos que pueden faltar.

1. `questions` → `content_items(kind='quiz')` + `content_solutions` (mismo UUID).
2. `arcade_runs`/`arcade_answers` → `game_sessions(mode='trivia_arcade')` + ítems +
   intentos.
3. `matches`/`match_rounds` → `game_sessions(mode='trivia_versus')` + ídem.
4. Las tablas viejas quedan de solo lectura hasta `0007` (fase 10).

## 7. Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| `GET` | `/modes` | catálogo con ranking/input/media/config |
| `POST` | `/sessions` | crea sesión solo `{mode, config}` |
| `WS` | `/ws/session/{id}` | juego solo |
| `POST` | `/rooms` | crea sala `{mode?, config}` |
| `WS` | `/ws/room/{code}` | lobby + partida versus |
| `GET` | `/leaderboard/{mode}` | ranking (404 si el modo no tiene) |
| `GET` | `/leaderboard/{mode}/me` | posición propia |
| `GET/POST` | `/admin/content/{kind}` | listado e importación |

Alias de compatibilidad: `/admin/questions` → `/admin/content/quiz`,
`/leaderboard/arcade` → `/leaderboard/trivia_arcade`.

## 8. Riesgos

| Riesgo | Mitigación |
|---|---|
| Sobre-generalizar | Cada abstracción nace de dos casos; un modo se lee en 3–5 archivos |
| `jsonb` debilita la base | Columnas comunes tipadas + esquema versionado + conformance |
| Fuga de respuesta | Tabla de solución aparte + test recursivo + nombres de archivo opacos |
| Rosco rompe la linealidad | `schedule=BOARD` desde el diseño; fase 8 opcional |
| Pérdida de historial | Backfill + comparación + tablas viejas de solo lectura |
| Licencias de medios | Decisión de catálogo antes de la fase 9; no es técnica |
| Costo frontend | `GET /modes` + registry de renderers + componentes compartidos |

## 9. Criterio de terminado del refactor

1. `trivia_arcade` y `trivia_versus` funcionan igual que hoy (golden + e2e).
2. Un modo nuevo se agrega con: un `ContentKind`, un `RoundRules`, una `Progression`,
   una entrada en `MODES` y su contenido. Sin tocar `reaper`, `session_ws`,
   `leaderboard` ni el modelo de datos.
3. `GET /modes` maneja el menú del frontend.
4. `make lint`, `make cov` (≥85 %), `make check-schema` y las e2e en verde.
5. `docs/api.md` documenta el contrato nuevo y los alias.
