# Fase 4 — Port del arcade

> Rol: **backend**. El arcade pasa a usar el motor y la sesión genéricos **sin cambiar
> un solo mensaje**. Depende de: fase 3. Al terminar, tag `refactor-fase-4`.

---

### 4.1 — `SessionStore` para sesiones solo

**Rol:** backend · **Depende de:** 3.5 · **Sesión:** 1

**Leé:**
- `docs/plan-refactor/diseno.md` §3.4
- `backend/app/runtime/arcade_session.py`
- `backend/app/runtime/room_manager.py` (patrón de lock, outbox, vencimiento)
- `backend/app/game/solo_engine.py`

**Hacé:**
- Crear `backend/app/runtime/session_store.py`:
  - `SessionStore` (protocolo): `open`, `close`, `submit`, `live`, `sessions`.
  - `InMemorySessionStore` para sesiones solo: estado, `outbox`, reloj y `sleep`
    inyectados, `rng`, tarea de vencimiento, registro `live.sessions`.
- La sesión es de una conexión: si el socket se cae, la sesión se cierra y la fila queda
  para que el barrendero la invalide (misma semántica que el arcade actual).
- Tests con `FakeClock`: abrir, servir, responder, vencer, cerrar, outbox lleno,
  cierre idempotente.

**No toques:** `app/ws/` (eso es 4.2), `frontend/`, tablas viejas.

**Verificá:** `make lint && make cov`.

**Documentá:** `docs/backend.md` (estado vivo) y `diseno.md` §3.4 si cambió la interfaz.

**Commit:** `refactor(runtime): add the generic solo session store`

**Hecho cuando:** una sesión de prueba se juega de punta a punta contra el store sin
tocar el WebSocket.

---

### 4.2 — Rewire del arcade al motor y la sesión nuevos

**Rol:** backend · **Depende de:** 4.1 · **Sesión:** 1

**Leé:**
- `backend/app/ws/arcade_ws.py`
- `backend/app/runtime/session_store.py` (de 4.1)
- `backend/app/game/solo_engine.py`
- `backend/app/services/sessions.py`
- `backend/tests/golden/` (fase 0)

**Hacé:**
- `arcade_ws.py` pasa a: crear la sesión en el store, pedir ítems al `QuizContent`,
  delegar reglas al `SoloEngine` y persistir con `services/sessions.py`.
- **Los mensajes no cambian**: `arcade_start`, `arcade_question`, `arcade_result`,
  `arcade_end`, `pong`, `error`, con los mismos campos y el mismo orden.
- El `seen` de Redis sigue con la misma clave y TTL.
- Los golden de la fase 0 pasan sin regenerarlos.
- Si aparece una diferencia de comportamiento, **no la normalices**: es un bug del port.

**No toques:** `room_ws.py`, `room_manager.py`, `frontend/`, tablas viejas.

**Verificá:** `make lint && make cov`; golden idénticos; e2e de arcade.

**Documentá:** `docs/backend.md` si cambió el flujo interno.

**Commit:** `refactor(arcade): run on the generic engine and session store`

**Hecho cuando:** el arcade es indistinguible para el cliente y las tablas nuevas
reciben la sesión.

---

### 4.3 — Borrar el arcade viejo

**Rol:** backend · **Depende de:** 4.2 · **Sesión:** 1

**Leé:**
- `backend/app/game/arcade_engine.py`
- `backend/app/runtime/arcade_session.py`
- `backend/app/services/arcade_runs.py`
- `backend/tests/test_arcade_engine.py`
- `backend/tests/test_arcade_session.py`

**Hacé:**
- Borrar los tres módulos viejos y mover sus tests al motor/sesión nuevos
  (`test_solo_engine.py`, `test_session_store.py`).
- Dejar de escribir en `arcade_runs`/`arcade_answers`; las tablas quedan de solo
  lectura hasta la fase 10.
- Actualizar imports y `app/models/__init__.py` si hace falta.
- No borrar todavía las tablas ni las migraciones.

**No toques:** `frontend/`, `room_ws.py`, `matches`/`match_rounds`.

**Verificá:** `make lint && make cov`; golden y e2e de arcade.

**Documentá:** `docs/backend.md` y `docs/archive/backend/arquitectura.md` (nota de
transición).

**Commit:** `refactor(arcade): remove the legacy arcade engine and store`

**Hecho cuando:** no queda código de producción importando `arcade_engine` ni
`arcade_session`.

**Cierre de fase:** `git tag refactor-fase-4`.
