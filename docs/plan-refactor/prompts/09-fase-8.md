# Fase 8 — Rosco (**opcional**)

> Rol: **backend + frontend**. No está en el camino crítico. Se hace solo si el usuario
> lo pide al llegar acá. Si se hace, es el primer modo que valida el contrato con un
> tablero (respuestas fuera de orden, reloj global, `pasapalabra`).
> Depende de: fase 7. Al terminar, tag `refactor-fase-8`.

**Gate de entrada:** la primera tarea de la fase pregunta:
"La fase 8 (rosco) es opcional. ¿La hacemos o cerramos el refactor acá?"

---

### 8.1 — `ContentKind` de rosco y contenido semilla

**Rol:** backend · **Depende de:** 7.3 · **Sesión:** 1

**Leé:**
- `docs/plan-refactor/diseno.md` §2 y §3.2
- `backend/app/game/modes/quiz/` (como referencia)
- `backend/app/services/importer.py`

**Hacé:**
- Crear `backend/app/game/modes/rosco/`:
  - `models.py`: `RoscoPayload` (letter, definition) y `RoscoSolution` (answer,
    alternatives), `schema_version=1`.
  - `content.py`: `RoscoContent` (parse_row, fingerprint, candidates por letra,
    load).
- Definir el alfabeto (A–Z; documentar si entra `Ñ`) y validarlo.
- Seed de 3–5 roscos en `backend/seeds/rosco.csv`; el importador acepta `--kind rosco`.
- Tests: letra inválida, respuesta alternativa, dedupe, 27 letras.

**No toques:** `frontend/`, el motor todavía.

**Verificá:** `make lint && make cov && make check-schema`.

**Documentá:** `docs/api.md` §contenido rosco y `docs/plan.md` §rosco.

**Commit:** `feat(rosco): add the rosco content kind and seed`

**Hecho cuando:** un rosco de prueba se importa y se lee público/solución por separado.

---

### 8.2 — Motor puro de tablero

**Rol:** backend · **Depende de:** 8.1 · **Sesión:** 1

**Leé:**
- `backend/app/game/solo_engine.py`
- `backend/app/game/core/`
- `docs/plan-refactor/diseno.md` §3.3–§3.4

**Hacé:**
- `BoardSoloEngine`: 27 ítems, reloj global, respuestas en cualquier orden,
  `pasapalabra`, cierre por tiempo o tablero completo.
- `Progression` de tablero: sin curva de dificultad; segundos fijos por rosco.
- El estado es inmutable y expone qué letras quedan, cuáles se pasaron y cuáles se
  cerraron.
- Tests puros: tablero completo, pasapalabra, tiempo agotado, respuesta fuera de orden,
  respuesta duplicada, letra inválida.

**No toques:** `app/runtime/`, `app/ws/`, `frontend/`.

**Verificá:** `make lint && make cov`.

**Documentá:** `docs/plan-refactor/diseno.md` §3.3 si cambió la firma.

**Commit:** `feat(rosco): add the pure board engine`

**Hecho cuando:** un rosco entero corre en tests sin I/O y sin reloj real.

---

### 8.3 — Sesión, persistencia y WS del tablero

**Rol:** backend · **Depende de:** 8.2 · **Sesión:** 1

**Leé:**
- `backend/app/runtime/session_store.py`
- `backend/app/ws/session_ws.py`
- `backend/app/services/sessions.py`

**Hacé:**
- El store acepta `schedule=BOARD`: un `session_item` por letra, `attempt_seq` por
  intento; el estado vive en memoria y se persiste al cerrar.
- Registrar `rosco_solo` con `ranking=None`, `players=SOLO`, `connection=EPHEMERAL`.
- WS canónico `/ws/session/{id}`: `item_start` lleva la letra y la definición;
  `item_result` la respuesta recién cuando el ítem cierra.
- Tests de integración: un rosco de punta a punta, sin fuga de la respuesta, sin fila
  de ranking.

**No toques:** `frontend/`, `trivia_*`.

**Verificá:** `make lint && make cov`; conformance suite incluye `rosco_solo`.

**Documentá:** `docs/api.md` §WebSocket rosco y `docs/plan.md`.

**Commit:** `feat(rosco): add the board session and websocket`

**Hecho cuando:** un rosco se juega de punta a punta por WS sin ranking.

---

### 8.4 — Pantalla del rosco

**Rol:** frontend · **Depende de:** 8.3 · **Sesión:** 1

**Leé:**
- `docs/diseno.md`
- `frontend/src/lib/modes/registry.ts`
- `frontend/src/routes/play/[mode]/+page.svelte`
- `frontend/src/lib/api/ws.ts`

**Hacé:**
- `src/lib/modes/rosco/RoscoScreen.svelte`: tablero de letras, letra activa,
  definición, entrada de texto, `pasapalabra`, reloj global, feedback por letra.
- Registrar el renderer en `registry.ts` (`input: "text"`, `schedule: "board"`).
- Todas las cadenas en `es.json`; teclado y táctil ≥44 px.
- E2E: un rosco completo (o hasta el tiempo) y un `pasapalabra`.

**No toques:** `backend/`.

**Verificá:** `npm run check && npm run build && npm run test:e2e`.

**Documentá:** `docs/frontend.md`, `docs/plan.md` y `estado.md`.

**Commit:** `feat(rosco): add the board screen`

**Hecho cuando:** el rosco se juega desde la home y la e2e lo cubre.

---

### 8.5 — Cierre de la fase

**Rol:** backend · **Depende de:** 8.4 · **Sesión:** 1

**Leé:**
- `docs/plan-refactor/diseno.md` §9
- `docs/api.md`
- `docs/plan-refactor/estado.md`

**Hacé:**
- Revisar que `rosco_solo` no tenga ranking y que la home lo muestre sin link al
  ranking.
- Actualizar `docs/api.md`, `docs/plan.md`, `docs/backend.md`, `docs/frontend.md`.
- Correr la verificación completa (backend + frontend + e2e).

**No toques:** código de juego; esta tarea solo cierra docs y verifica.

**Verificá:** `make lint && make cov && make check-schema` y
`npm run check && npm run build && npm run test:e2e`.

**Documentá:** `docs/api.md`, `docs/plan.md`, `docs/backend.md`, `docs/frontend.md` y
`estado.md`.

**Commit:** `docs(rosco): close the optional board mode`

**Hecho cuando:** la verificación completa pasa y el rosco no aparece con ranking.

**Cierre de fase:** `git tag refactor-fase-8`.
