# Fase 6 — Registro y rutas genéricas

> Rol: **backend**. El catálogo de modos y el endpoint de sesión genérico. Las rutas
> viejas siguen funcionando como adaptadores. Depende de: fase 5.
> Al terminar, tag `refactor-fase-6`.

---

### 6.1 — Registrar los modos y `GET /modes`

**Rol:** backend · **Depende de:** 5.3 · **Sesión:** 1

**Leé:**
- `docs/plan-refactor/diseno.md` §2 y §7
- `backend/app/game/modes/registry.py`
- `backend/app/game/modes/quiz/`
- `backend/app/game/solo_engine.py`
- `backend/app/game/versus_engine.py`

**Hacé:**
- Registrar en `MODES`:
  - `trivia_arcade`: `quiz` + `arcade`, `players=SOLO`, `ranking=RankingPolicy(...)`;
  - `trivia_versus`: `quiz` + `versus`, `players=VERSUS`, `ranking=None`.
- Cada modo declara `config_schema` y `public_schema` (pydantic) y `ruleset_version=1`.
- Reemplazar el `RANKED_MODES` local de la tarea 3.4 por `mode.ranking`: el ranking
  deja de tener una lista aparte.
- Crear `app/api/routers/modes.py` con `GET /modes`: code, name, content_kind,
  play_format, players, input, media, ranking, config_schema.
- Tests: el catálogo lista los dos modos, `trivia_arcade` tiene ranking y
  `trivia_versus` no, el esquema de config rechaza valores inválidos.
- La suite de conformidad (`test_modes_conformance.py`) ahora corre contra los dos
  modos registrados.

**No toques:** `app/ws/`, `frontend/`, tablas.

**Verificá:** `make lint && make cov`.

**Documentá:** `docs/api.md` §`GET /modes` y `docs/plan.md` §modos.

**Commit:** `feat(modes): register trivia arcade and versus in the catalog`

**Hecho cuando:** `GET /modes` describe los dos modos y la conformance suite pasa.

---

### 6.2 — `POST /sessions` y `WS /ws/session/{id}`

**Rol:** backend · **Depende de:** 6.1 · **Sesión:** 1

**Leé:**
- `docs/plan-refactor/diseno.md` §5 y §7
- `backend/app/ws/arcade_ws.py`
- `backend/app/runtime/session_store.py`
- `backend/app/api/routers/rooms.py`
- `backend/app/api/deps.py`

**Hacé:**
- `POST /sessions {mode, config}`: valida que el modo exista y sea `SOLO`; valida el
  `config_schema`; crea la sesión solo y devuelve `{session_id, ws_url}`. Rate limit y
  auth como el resto. Un modo `VERSUS` responde `422 MODE_NOT_SOLO`.
- `WS /ws/session/{id}`: canal genérico solo, con protocolo canónico
  (`session_start`, `item_start`, `item_result`, `session_end`, `session_state`,
  `error`). Reutiliza auth, heartbeat, `outbox` y cierre `1008`.
- El `payload` de `item_start` sale del `public_schema` del modo; la solución no viaja.
- `/ws/arcade` sigue existiendo y sigue emitiendo los mensajes viejos (adaptador).
- Tests: partida solo completa; modo inexistente (404); config inválida (422); fuga
  de solución (el test de la fase 0 debe cubrir el canal nuevo).

**No toques:** `room_ws.py`, `frontend/`, tablas.

**Verificá:** `make lint && make cov`; golden de arcade siguen verdes.

**Documentá:** `docs/api.md` §Sesiones y §WebSocket; `estado.md`.

**Commit:** `feat(api): add generic solo sessions and the session websocket`

**Hecho cuando:** una sesión `trivia_arcade` se juega por `/ws/session/{id}` con el
protocolo canónico y sin filtrar la respuesta.

---

### 6.3 — Contrato, alias y matriz de compatibilidad

**Rol:** backend · **Depende de:** 6.2 · **Sesión:** 1

**Leé:**
- `docs/api.md`
- `docs/plan.md`
- `docs/backend.md`

**Hacé:**
- Documentar en `docs/api.md`: catálogo, `POST /sessions`, protocolo canónico, ranking
  por modo y códigos de error nuevos (`MODE_NOT_FOUND`, `MODE_WITHOUT_RANKING`,
  `INVALID_CONFIG`).
- Agregar una tabla de compatibilidad: qué ruta/mensaje viejo queda como alias y hasta
  qué fase.
- Actualizar `docs/plan.md` con la separación contenido/formato/modo.
- Tests de contrato: los alias responden igual que las rutas nuevas.

**No toques:** `frontend/`, lógica de juego.

**Verificá:** `make lint && make cov`; `docs/api.md` sin referencias muertas.

**Documentá:** los tres archivos de arriba y `estado.md`.

**Commit:** `docs(api): document the multi-mode contract and compatibility aliases`

**Hecho cuando:** un cliente puede implementar un modo nuevo leyendo solo `api.md` y
`GET /modes`.

**Cierre de fase:** `git tag refactor-fase-6`.
