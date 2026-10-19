# Fase 5 — Port del 1v1

> Rol: **backend**. El versus pasa al motor y la sesión genéricos, manteniendo lobby,
> gracia, pausa de reloj, desempate y revancha. Depende de: fase 4.
> Al terminar, tag `refactor-fase-5`.

---

### 5.1 — `VersusEngine` y sesión con sillas

**Rol:** backend · **Depende de:** 4.3 · **Sesión:** 1

**Leé:**
- `docs/plan-refactor/diseno.md` §3.3–§3.4
- `backend/app/game/match_engine.py`
- `backend/app/runtime/room.py`
- `backend/app/runtime/room_manager.py`
- `backend/tests/test_match_engine.py`
- `backend/tests/test_room.py`

**Hacé:**
- Crear `backend/app/game/versus_engine.py` con la lógica actual: dos sillas, rondas,
  dificultad por tramo, desempate (máx. 3), abandono, `void`, revancha.
- Extender `InMemorySessionStore` con sesiones versus:
  - `open`/`join`/`start`/`answer`/`disconnect`/`reconnect`/`close`/`rematch`;
  - lock por sesión, `outbox` por silla, gracia de 20 s, pausa y reanudación del reloj,
    tarea de vencimiento.
- Los mensajes siguen siendo los actuales; el motor no serializa nada.
- Portar los tests de `match_engine`/`room` al motor nuevo **sin cambiar expectativas**.

**No toques:** `app/ws/` (eso es 5.2), `frontend/`, tablas viejas.

**Verificá:** `make lint && make cov`.

**Documentá:** `docs/backend.md` (sillas, gracia, pausa) y `diseno.md` §3.3.

**Commit:** `refactor(runtime): add the versus engine and seated sessions`

**Hecho cuando:** una partida completa, un abandono y una revancha corren contra el
store nuevo en tests.

---

### 5.2 — Rewire de la sala al store nuevo

**Rol:** backend · **Depende de:** 5.1 · **Sesión:** 1

**Leé:**
- `backend/app/ws/room_ws.py`
- `backend/app/runtime/room_manager.py`
- `backend/app/runtime/session_store.py`
- `backend/tests/golden/` (fase 0)

**Hacé:**
- `room_manager.py` pasa a ser un adaptador fino del `SessionStore` (o desaparece y el
  handler usa el store directo, según lo que quede más simple).
- `room_ws.py` conserva el protocolo actual: `room_state`, `match_start`, `round_start`,
  `opponent_answered`, `round_result`, `match_end`, `opponent_left`, `error`.
- La sala sigue creando la fila `matches`/sesión al arrancar y cerrándola al terminar.
- Los golden de 1v1 y de reconexión pasan sin regenerarlos.

**No toques:** `arcade_ws.py`, `frontend/`, tablas viejas.

**Verificá:** `make lint && make cov`; golden idénticos; e2e 1v1.

**Documentá:** `docs/backend.md` y `diseno.md` §3.4 si cambió el borde.

**Commit:** `refactor(versus): run rooms on the generic session store`

**Hecho cuando:** el 1v1 es indistinguible para el cliente y la sesión nueva recibe el
historial.

---

### 5.3 — Borrar el versus viejo

**Rol:** backend · **Depende de:** 5.2 · **Sesión:** 1

**Leé:**
- `backend/app/game/match_engine.py`
- `backend/app/runtime/room.py`
- `backend/tests/test_match_engine.py`
- `backend/tests/test_room.py`

**Hacé:**
- Borrar `match_engine.py` y `room.py`; mover sus tests a `versus_engine`/store.
- Dejar de escribir en `matches`/`match_rounds`; quedan de solo lectura hasta la fase 10.
- Actualizar imports y `app/models/__init__.py`.
- No borrar tablas ni migraciones.

**No toques:** `frontend/`, `arcade_ws.py`, `rooms` (la tabla de lobby sigue).

**Verificá:** `make lint && make cov`; golden y e2e 1v1.

**Documentá:** `docs/backend.md` y `docs/archive/backend/arquitectura.md`.

**Commit:** `refactor(versus): remove the legacy match engine and room state`

**Hecho cuando:** no queda código de producción importando `match_engine` ni
`runtime/room.py`.

**Cierre de fase:** `git tag refactor-fase-5`.
