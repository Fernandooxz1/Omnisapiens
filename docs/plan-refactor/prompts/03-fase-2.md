# Fase 2 — Contenido genérico

> Rol: **backend**. El contenido deja de ser "una pregunta de 4 opciones" y pasa a ser
> un ítem con `kind`, payload público y solución aparte. El `quiz` actual es el primer
> `ContentKind`. Depende de: fase 1. Al terminar, tag `refactor-fase-2`.

---

### 2.1 — Tablas de contenido y migración

**Rol:** backend · **Depende de:** 1.3 · **Sesión:** 1

**Leé:**
- `docs/plan-refactor/diseno.md` §4.1
- `backend/app/models/question.py`
- `backend/app/models/base.py`
- `backend/alembic/versions/0001_schema_inicial.py` (convenciones)

**Hacé:**
- Crear `backend/app/models/content.py`:
  - `ContentItem`: id, kind, schema_version, status, language, difficulty, categories,
    payload jsonb, media_type, media_url, content_hash, supersedes_id, timestamps.
  - `ContentSolution`: content_id PK/FK cascade, payload jsonb.
- Constraints: `kind` no vacío, `status` conocido, `difficulty` 1–5, `payload` objeto,
  `(payload->>'v')::int = schema_version`, `content_hash` hex único, media coherente.
  Índices: `(kind, status, difficulty)`, GIN en `categories`.
- Migración `0004_content.py` (solo crea tablas; no toca `questions`).
- Tests de constraints en `backend/tests/test_constraints_content.py`: insertar cada
  dato inválido y exigir el rechazo.
- Actualizar `app/models/__init__.py` y `backend/tests/test_schema_matches_models.py`.

**No toques:** `app/services/`, `app/ws/`, `app/runtime/`, `frontend/`, `questions`.

**Verificá:** `make lint && make cov && make check-schema`.

**Documentá:** `docs/plan-refactor/diseno.md` §4.1 si cambió una columna.

**Commit:** `refactor(content): add generic content and solution tables`

**Hecho cuando:** `alembic upgrade head` corre sobre base limpia y los constraints
rechazan cada caso inválido.

---

### 2.2 — Backfill de `questions` a `content_items`

**Rol:** backend · **Depende de:** 2.1 · **Sesión:** 1

**Leé:**
- `docs/plan-refactor/diseno.md` §6
- `backend/app/models/question.py`
- `backend/app/services/importer.py`
- `backend/app/cli.py`

**Hacé:**
- Agregar a `app/cli.py` el comando `backfill-content --kind quiz` (idempotente).
- Mapear cada `questions` a:
  - `ContentItem(kind='quiz', payload={v:1, prompt, options, media}, difficulty,
    categories=[category], content_hash, status, language)`;
  - `ContentSolution(payload={v:1, correct_index, explanation})`.
- Reporte: leídas, creadas, ya existentes, rechazadas (con motivo).
- El backfill **no borra** `questions`; se puede correr dos veces sin duplicar.
- Test de integración: 120 seed → 120 `content_items`; segunda corrida → 0 creadas.

**No toques:** `app/services/question_bank.py` (eso es 2.3), `frontend/`.

**Verificá:** `make lint && make cov`; correr el comando dos veces contra la base de
test y comparar conteos.

**Documentá:** `README.md` §comandos (`make backfill-content`) y `diseno.md` §6.

**Commit:** `refactor(content): backfill quiz questions into the generic content tables`

**Hecho cuando:** la base tiene el mismo contenido en las dos formas y el comando es
idempotente.

---

### 2.3 — `ContentKind` de quiz, importador y admin

**Rol:** backend · **Depende de:** 2.1, 2.2 · **Sesión:** 1

**Leé:**
- `docs/plan-refactor/diseno.md` §3.2
- `backend/app/services/importer.py`
- `backend/app/services/question_admin.py`
- `backend/app/api/routers/admin.py`
- `backend/app/cli.py`

**Hacé:**
- Crear `backend/app/game/modes/quiz/` con:
  - `models.py`: `QuizPayload` (prompt, options, media) y `QuizSolution`
    (correct_index, explanation), versionados.
  - `content.py`: `QuizContent` implementando `ContentKind` (parse_row, fingerprint,
    candidates, load). Mantener el barajado de opciones y el tipo público sin
    `correct_index`.
- El importador y el admin escriben en `content_items`/`content_solutions` usando el
  `ContentKind`, y **temporalmente también en `questions`** (dual-write) para que el
  juego siga leyendo la tabla vieja hasta 2.4.
- CLI: `import-content --kind quiz FILE` (alias `import-questions`); admin:
  `GET/POST /admin/content/{kind}` con alias `/admin/questions`.
- Tests: el CSV semilla se importa en las dos formas; duplicados; fila inválida; kind
  desconocido.

**No toques:** `app/services/question_bank.py` (eso es 2.4), `app/ws/`, `app/runtime/`,
`frontend/`.

**Verificá:** `make lint && make cov`; una partida de arcade sigue viendo lo importado.

**Documentá:** `docs/api.md` §Admin y `README.md` §cargar preguntas.

**Commit:** `refactor(content): add the quiz content kind and dual-write imports`

**Hecho cuando:** el mismo CSV se importa igual que antes y el juego sigue funcionando
sin cambios.

---

### 2.4 — Banco de contenido y corte del dual-write

**Rol:** backend · **Depende de:** 2.3 · **Sesión:** 1

**Leé:**
- `backend/app/services/question_bank.py`
- `backend/app/services/questions.py`
- `backend/tests/test_question_bank.py`
- `backend/tests/golden/` (fase 0)

**Hacé:**
- `question_bank.py` lee de `content_items(kind='quiz')` y `content_solutions`; conserva
  las firmas que usan el arcade y el 1v1 y el tipo público sin `correct_index`.
- Quitar el dual-write a `questions` del importador/admin (la tabla queda de solo
  lectura hasta la fase 10).
- Actualizar `backend/tests/factories.py` para crear contenido genérico.
- Los tests de `test_question_bank.py` y los golden siguen verdes.
- Tests: importar → jugar → la pregunta aparece; segunda importación no duplica.

**No toques:** `app/ws/`, `app/runtime/`, `frontend/`, `questions` (solo lectura).

**Verificá:** `make lint && make cov`; golden de fase 0 idénticos; e2e de arcade.

**Documentá:** `docs/plan-refactor/diseno.md` §4.1 si cambió la forma del payload.

**Commit:** `refactor(content): read quiz content from the generic bank`

**Hecho cuando:** el arcade y el 1v1 sirven las mismas preguntas desde las tablas nuevas,
sin dual-write y sin cambiar un solo mensaje WS.

**Cierre de fase:** `git tag refactor-fase-2`.
