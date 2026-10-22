# Fase 1 — Núcleo de reglas

> Rol: **backend**. Extrae lo común a todos los modos **sin cambiar las reglas actuales**.
> Depende de: fase 0. Al terminar, tag `refactor-fase-1`.

---

### 1.1 — Tipos comunes de ítem, respuesta y veredicto

**Rol:** backend · **Depende de:** 0.1 · **Sesión:** 1

**Leé:**
- `docs/plan-refactor/diseno.md` §3.2–§3.3
- `backend/app/game/answers.py`
- `backend/app/game/scoring.py`
- `backend/tests/test_answers.py`
- `backend/tests/test_scoring.py`

**Hacé:**
- Crear `backend/app/game/core/` con:
  - `items.py`: `ServedItem` (item_key, difficulty, seconds, served_at_ms, deadline),
    `Submission` (unión discriminada: `Choice`, `Text`, `Letter`, `Order`) y
    `Verdict` (correct, elapsed_ms, rejected, detail).
  - `settle.py`: `settle(served, submission, *, now_ms)` con la ventana temporal actual
    ("fuera de ventana no existe") y un `grade` provisto por el modo.
- Mantener `answers.py` y `scoring.py` funcionando: son la implementación de referencia
  hasta la fase 4. No los borres todavía.
- Tests unitarios de la ventana: borde inferior, borde superior, sin respuesta, intento
  duplicado, submission de tipo equivocado.

**No toques:** `app/runtime/`, `app/ws/`, `frontend/`, tablas.

**Verificá:** `make lint && make cov`.

**Documentá:** `docs/plan-refactor/diseno.md` si el contrato cambió respecto de §3.

**Commit:** `refactor(core): generalize served items, submissions and verdicts`

**Hecho cuando:** los tipos nuevos tienen tests propios y los tests viejos siguen verdes.

---

### 1.2 — `SoloEngine` extraído del arcade

**Rol:** backend · **Depende de:** 1.1 · **Sesión:** 1

**Leé:**
- `backend/app/game/arcade_engine.py`
- `backend/app/runtime/arcade_session.py`
- `backend/tests/test_arcade_engine.py`
- `backend/tests/test_arcade_session.py`
- `docs/plan-refactor/diseno.md` §3.4

**Hacé:**
- Crear `backend/app/game/solo_engine.py` con la lógica actual del arcade:
  vidas, racha, dificultad por aciertos, segundos, fin de corrida.
- Parametrizar lo que el arcade hace fijo: `lives`, curva de dificultad, curva de
  segundos, bonus de racha. Los valores actuales quedan como defaults del formato
  `arcade`, no como constantes del motor.
- El estado sigue siendo inmutable y el historial no vive en el estado.
- Adaptar `runtime/arcade_session.py` para usar `SoloEngine` sin cambiar los mensajes.
- Los tests actuales del arcade **no cambian de expectativas**: si hay que tocar un
  test, es señal de que cambió el comportamiento y hay que parar.

**No toques:** `app/ws/`, `frontend/`, tablas, `services/arcade_runs.py`.

**Verificá:** `make lint && make cov`; los golden de la fase 0 siguen pasando.

**Documentá:** `docs/plan-refactor/diseno.md` §3.4 si cambió la firma.

**Commit:** `refactor(core): extract the solo engine from the arcade rules`

**Hecho cuando:** `test_arcade_engine.py` y `test_arcade_session.py` pasan sin cambios y
los golden son idénticos.

---

### 1.3 — Protocolos de modo, progresión y scoring

**Rol:** backend · **Depende de:** 1.2 · **Sesión:** 1

**Leé:**
- `docs/plan-refactor/diseno.md` §2 y §3
- `backend/app/game/solo_engine.py` (de 1.2)
- `backend/app/services/questions.py`
- `backend/app/services/question_bank.py`

**Hacé:**
- Crear `backend/app/game/modes/base.py` con:
  - `ContentKind`, `RoundRules`, `Progression`, `ScoringPolicy` (protocolos);
  - `GameMode` (dataclass con `code`, `content_kind`, `play_format`, `ruleset_version`,
    `content`, `rules`, `progression`, `scoring`, `config_schema`, `public_schema`,
    `ranking`, `players`, `connection`, `schedule`);
  - `Players`, `ConnectionPolicy`, `Schedule`.
- Crear `backend/app/game/modes/registry.py` con un registro vacío y
  `register(mode)` / `get(code)`.
- Crear `backend/tests/test_modes_conformance.py` con la suite vacía parametrizada por
  `registry.all()`: por ahora 0 casos, pero con las funciones de aserción listas
  (payload sin solución, determinismo, ventana, puntos ≥ 0).
- **No** registrar todavía `trivia_arcade`/`trivia_versus`: eso es fase 6.

**No toques:** `app/ws/`, `app/runtime/`, `frontend/`.

**Verificá:** `make lint && make cov`.

**Documentá:** `docs/plan-refactor/diseno.md` §3 (contratos finales) y
`docs/plan-refactor/README.md` si cambió el formato de tarea.

**Commit:** `refactor(core): add the game mode contracts and registry`

**Hecho cuando:** los protocolos están tipados con `mypy --strict` y la suite de
conformidad corre vacía sin romper.

**Cierre de fase:** `git tag refactor-fase-1`.
