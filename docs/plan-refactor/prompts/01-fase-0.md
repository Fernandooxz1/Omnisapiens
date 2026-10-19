# Fase 0 — Red de seguridad

> Rol: **backend**. No cambia comportamiento: solo congela lo que hoy funciona.
> Depende de: nada. Al terminar, tag `refactor-baseline`.

---

### 0.1 — Congelar transcripts de WS y guardia de fuga

**Rol:** backend · **Depende de:** — · **Sesión:** 1

**Leé:**
- `docs/plan-refactor/diseno.md` §5 (protocolo y anti-fuga)
- `backend/tests/ws_client.py`
- `backend/tests/test_room_ws.py`
- `backend/tests/test_arcade_ws.py`

**Hacé:**
- Crear `backend/tests/golden/` con transcripts normalizados (sin timestamps absolutos)
  de tres escenarios:
  1. arcade completo hasta las 3 vidas;
  2. partida 1v1 completa;
  3. desconexión + reconexión dentro de la gracia.
- Agregar `backend/tests/test_golden_ws.py` que reproduzca los escenarios y compare
  contra los JSONL. Un helper de normalización reemplaza `ends_at`, ids y tiempos por
  placeholders estables.
- Agregar `backend/tests/test_protocol_leak.py`: recorre los mensajes públicos actuales
  y falla si aparecen `correct_index`, `solution`, `answer` o el valor de la respuesta
  antes de `round_result` / `arcade_result`.
- Si un escenario no se puede capturar con el harness actual, extraer el mínimo helper
  de grabación; no cambiar el comportamiento del servidor.

**No toques:** `app/` (salvo un helper de test), `frontend/`.

**Verificá:** `make lint && make cov` (los golden pasan dos veces: grabar y comparar).

**Documentá:** `docs/plan-refactor/estado.md` (historial).

**Commit:** `test(refactor): freeze the current ws transcripts and leak guard`

**Hecho cuando:** los tres golden pasan en CI local y el test de fuga falla si se
intenta agregar `correct_index` a un `round_start` de prueba.

**Cierre de fase:** `git tag refactor-baseline`.
