# Fase 7 — Frontend multi-modo

> Rol: **frontend**. El menú y las pantallas dejan de estar hardcodeados: salen de
> `GET /modes`. Depende de: fase 6. Al terminar, tag `refactor-fase-7`.

---

### 7.1 — Cliente de modos y menú de inicio

**Rol:** frontend · **Depende de:** 6.3 · **Sesión:** 1

**Leé:**
- `docs/api.md` §`GET /modes`
- `frontend/src/lib/api/client.ts`
- `frontend/src/routes/+page.svelte`
- `frontend/src/lib/i18n/es.json`
- `docs/diseno.md` (botones y jerarquía)

**Hacé:**
- Crear `frontend/src/lib/api/modes.ts` con el tipo `GameMode` y `fetchModes()`.
- Crear `frontend/src/lib/modes/registry.ts`: por `code`, la ruta y el renderer que
  corresponde. Si un modo del backend no tiene renderer, se muestra deshabilitado con
  un texto claro (no se rompe la home).
- La home arma los botones desde el catálogo: `trivia_arcade` como modo principal,
  después `trivia_versus`. El ranking aparece solo si `ranking: true`.
- Todas las cadenas nuevas en `es.json`.
- Test manual: con el backend arriba, la home lista los dos modos y no hay URLs
  hardcodeadas.

**No toques:** `backend/`, `src/lib/match/`, `src/lib/arcade/`.

**Verificá:** `npm run check && npm run build`.

**Documentá:** `docs/frontend.md` (de dónde sale el menú) y `estado.md`.

**Commit:** `feat(ui): drive the home menu from the game mode catalog`

**Hecho cuando:** agregar un modo en el backend lo hace aparecer en la home sin tocar
el menú.

---

### 7.2 — Ruta `/play/[mode]` y registry de renderers

**Rol:** frontend · **Depende de:** 7.1 · **Sesión:** 1

**Leé:**
- `frontend/src/routes/arcade/+page.svelte`
- `frontend/src/routes/play/+page.svelte`
- `frontend/src/lib/arcade/live.svelte.ts`
- `frontend/src/lib/match/live.svelte.ts`
- `docs/api.md` §Sesiones y §WebSocket

**Hacé:**
- Crear `frontend/src/routes/play/[mode]/+page.svelte` que resuelve el modo con
  `registry.ts` y monta el renderer.
- Mover la pantalla del arcade a `src/lib/modes/arcade/ArcadeScreen.svelte`; usa
  `POST /sessions` + `WS /ws/session/{id}` (protocolo canónico) o el `/ws/arcade`
  mientras el backend mantenga el adaptador.
- Mover el flujo de sala 1v1 a `src/lib/modes/versus/VersusScreen.svelte`; sigue con
  `POST /rooms` + `WS /ws/room/{code}`.
- Redirecciones: `/arcade` → `/play/trivia_arcade`; `/play` → `/play/trivia_versus`.
- La lógica de red sigue viviendo en `src/lib/api/`; no hay `fetch`/`WebSocket` en
  componentes.

**No toques:** `backend/`, `docs/api.md` (si falta contrato, se pide, no se parchea).

**Verificá:** `npm run check && npm run build`; una partida de arcade y una de 1v1
completas a mano.

**Documentá:** `docs/frontend.md` y `docs/plan.md` §pantallas.

**Commit:** `feat(ui): add the mode route and renderer registry`

**Hecho cuando:** `/play/trivia_arcade` y `/play/trivia_versus` funcionan y las URLs
viejas redirigen.

---

### 7.3 — E2E y retiro de rutas viejas

**Rol:** frontend · **Depende de:** 7.2 · **Sesión:** 1

**Leé:**
- `frontend/e2e/arcade.spec.ts`
- `frontend/e2e/online.spec.ts`
- `frontend/e2e/errors.spec.ts`
- `frontend/playwright.config.ts`

**Hacé:**
- Actualizar las e2e a las rutas nuevas (`/play/trivia_arcade`, `/play/trivia_versus`).
- Agregar un caso: la home lista los modos que devuelve `GET /modes`.
- Si el backend ya expone `/ws/session/{id}`, migrar el arcade a ese canal y dejar el
  adaptador viejo sin uso.
- Borrar las rutas viejas (`src/routes/arcade/`, `src/routes/play/+page.svelte`) una vez
  que las redirecciones y las e2e estén verdes.
- Correr las 5+ e2e contra el backend real.

**No toques:** `backend/`, `docs/api.md`.

**Verificá:** `npm run check && npm run build && npm run test:e2e` (con `make up`,
`make migrate`, `make seed` y la API en `:8000`).

**Documentá:** `docs/frontend.md`, `docs/plan.md` y `estado.md`.

**Commit:** `test(ui): cover the mode catalog and retire the legacy routes`

**Hecho cuando:** las e2e pasan desde cero y no queda ninguna ruta hardcodeada.

**Cierre de fase:** `git tag refactor-fase-7`.
