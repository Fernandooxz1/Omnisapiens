# Fase 3 — Sesiones, ranking y barrendero

> Rol: **backend**. Un solo modelo de sesión para todos los formatos, con ranking
> opcional por modo. Depende de: fase 2. Al terminar, tag `refactor-fase-3`.

---

### 3.1 — Tablas de sesión y `rooms.mode`

**Rol:** backend · **Depende de:** 2.4 · **Sesión:** 1

**Leé:**
- `docs/plan-refactor/diseno.md` §4.2–§4.3
- `backend/app/models/match.py`
- `backend/app/models/arcade.py`

**Hacé:**
- Crear `backend/app/models/session.py`:
  - `GameSession`: mode, content_kind, play_format, ruleset_version, status, config,
    owner_user_id, room_id, score, correct_count, longest_streak, max_difficulty,
    started_at, ended_at.
  - `GameParticipant`: session_id, seat, user_id, score, outcome.
  - `SessionItem`: session_id, item_key, position, content_id, difficulty, seconds,
    served_at, deadline_at, closed_at, solution_snapshot.
  - `SessionAttempt`: item_id, attempt_seq, seat, submitted_at, submission, correct,
    elapsed_ms, points, rejected.
- Constraints: estado/ended_at, contadores ≥ 0, racha ≤ aciertos, unicidad
  `(session_id, item_key)` y `(item_id, seat, attempt_seq)`, `elapsed_ms >= 0`,
  `points >= 0`.
- Migración `0005_sessions.py`: crea las cuatro tablas y agrega `rooms.mode`
  (default `trivia_versus`). Relajar el `CHECK` de `rooms.config` a
  `jsonb_typeof(config) = 'object'`; el modo valida en Python.
- Tests de constraints en `backend/tests/test_constraints_sessions.py`.
- Actualizar `tests/test_constraints_match.py` si el CHECK relajado cambia una
  expectativa; documentar por qué.

**No toques:** `app/ws/`, `app/runtime/`, `app/services/` (eso es 3.2), `frontend/`.

**Verificá:** `make lint && make cov && make check-schema`.

**Documentá:** `docs/plan-refactor/diseno.md` §4.2 y `docs/backend.md` (invariantes).

**Commit:** `refactor(sessions): add the generic session tables`

**Hecho cuando:** `alembic upgrade head` corre limpio y cada constraint rechaza su caso.

---

### 3.2 — Servicio de sesiones (arranque y cierre)

**Rol:** backend · **Depende de:** 3.1 · **Sesión:** 1

**Leé:**
- `backend/app/services/arcade_runs.py`
- `backend/app/runtime/room_manager.py` (las dos escrituras)
- `docs/plan-refactor/diseno.md` §4.2

**Hacé:**
- Crear `backend/app/services/sessions.py` con:
  - `start_session(session, *, session_id, mode, ...)`: fila `playing`.
  - `finish_session(session, *, session_id, state, items, attempts)`: `UPDATE` del
    resumen + `INSERT` de ítems e intentos en **una** transacción.
  - `abandon_session` / `invalidate_session` para los cierres sin final.
- El servicio no sabe de sockets ni de relojes; recibe lo ya decidido.
- Tests: arranque + cierre, cierre idempotente, cierre sin fila (warning, no excepción),
  ítems duplicados rechazados.

**No toques:** `app/ws/`, `app/runtime/`, `frontend/`; no borres `arcade_runs.py`.

**Verificá:** `make lint && make cov`.

**Documentá:** `docs/backend.md` (dónde se escribe una sesión).

**Commit:** `refactor(sessions): add the start and finish service`

**Hecho cuando:** una sesión de prueba se escribe y se lee completa, y el cierre es
atómico.

---

### 3.3 — Backfill de arcade y 1v1

**Rol:** backend · **Depende de:** 3.2 · **Sesión:** 1

**Leé:**
- `backend/app/models/arcade.py`
- `backend/app/models/match.py`
- `docs/plan-refactor/diseno.md` §6

**Hacé:**
- Agregar `app/cli.py backfill-sessions` (idempotente):
  - `arcade_runs` + `arcade_answers` → sesión `trivia_arcade` + ítems + intentos;
  - `matches` + `match_rounds` → sesión `trivia_versus` + participantes + ítems +
    intentos.
- Usar el mismo UUID de `questions` como `content_id` (el backfill de 2.2 lo preserva)
  y `solution_snapshot = {v:1, correct_index}` para el contenido viejo.
- Reporte: leídas, creadas, ya existentes, saltadas.
- Test: una partida de cada tipo se reconstruye con el mismo puntaje y la misma
  secuencia de ítems; correr dos veces no duplica.
- Esta tarea **no** cambia el camino en vivo.

**No toques:** `app/ws/`, `app/runtime/`, `frontend/`.

**Verificá:** `make lint && make cov`; comparar 5 partidas al azar contra las tablas
viejas.

**Documentá:** `README.md` §comandos y `diseno.md` §6.

**Commit:** `refactor(sessions): backfill arcade and versus history`

**Hecho cuando:** el historial viejo se lee igual desde las tablas nuevas.

---

### 3.4 — Ranking por modo

**Rol:** backend · **Depende de:** 3.2 · **Sesión:** 1

**Leé:**
- `backend/app/services/leaderboard.py`
- `backend/app/api/routers/leaderboard.py`
- `backend/app/schemas/leaderboard.py`
- `docs/plan-refactor/diseno.md` §4.3

**Hacé:**
- Parametrizar `leaderboard.py` por `mode`; solo sesiones `finished` y `owner_user_id`
  no nulo (solo). Desempate `ended_at ASC`.
- `GET /leaderboard/{mode}` y `/leaderboard/{mode}/me`.
- Si el modo no tiene `ranking` (según el registro de la fase 6; por ahora una tabla
  local `RANKED_MODES = {"trivia_arcade"}`), devolver `404 MODE_WITHOUT_RANKING`.
- `/leaderboard/arcade` queda como alias de `trivia_arcade`.
- Tests: orden, empate, corte semanal, modo sin ranking, alias.

**No toques:** `frontend/`, `app/ws/`, `app/runtime/`.

**Verificá:** `make lint && make cov`.

**Documentá:** `docs/api.md` §Ranking y `docs/plan.md` §Arcade.

**Commit:** `refactor(ranking): make the leaderboard mode-aware`

**Hecho cuando:** el ranking de arcade da exactamente el mismo orden que antes y un modo
sin ranking responde 404.

---

### 3.5 — Barrendero genérico y registro de sesiones vivas

**Rol:** backend · **Depende de:** 3.1, 3.2 · **Sesión:** 1

**Leé:**
- `backend/app/services/reaper.py`
- `backend/app/runtime/live.py`
- `backend/tests/test_reaper.py`

**Hacé:**
- Extender `Live` con `sessions: frozenset[UUID]`.
- Agregar al barrido: `game_sessions` en `playing` más viejas que el umbral y no vivas
  → `invalid` con `ended_at`.
- Mantener los tres barridos viejos hasta la fase 10 (las tablas viejas siguen en uso).
- Tests: sesión vieja se invalida, sesión viva no, sala `waiting` sigue igual, idempotencia.

**No toques:** `app/ws/`, `app/runtime/room_manager.py`, `frontend/`.

**Verificá:** `make lint && make cov`.

**Documentá:** `docs/plan-refactor/diseno.md` §7 y `docs/backend.md` (barrendero).

**Commit:** `refactor(sessions): sweep generic sessions in the reaper`

**Hecho cuando:** el barrido cubre las tablas nuevas sin romper las viejas.

**Cierre de fase:** `git tag refactor-fase-3`.
