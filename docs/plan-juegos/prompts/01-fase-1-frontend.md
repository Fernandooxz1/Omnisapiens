# Fase 1 — Sección, navegación y sistema visual

> Rol: frontend. Leé `docs/frontend.md` y la sección de
> `docs/plan-juegos/diseno.md` que indique cada tarea.
> Una tarea por sesión. No toques `backend/`.

---

### 1.1 — Contrato, escala y sistema visual

**Leé:**
- `docs/plan-juegos/diseno.md` (completo).
- `docs/plan.md` §Estado, §Producto, §Modos.
- `docs/diseno.md` §Un solo estilo, §Paleta, §Quién usa cada color, §Acento del jugador.
- `docs/frontend.md` §Proyecto y límites, §Menú de inicio, §Rutas y pantallas por modo.

**Hacé:**
- Revisá y finalizá `docs/plan-juegos/diseno.md`: matriz de dificultad, reglas,
  tipos, AST de pistas, sobres, `BoardViewport`, accesibilidad y verificación.
  Corregí cualquier inconsistencia (por ejemplo, que el piso de pistas sea N−1).
- Actualizá `docs/plan.md`:
  - Diferenciá "modos de trivia" (arcade y 1v1) de la nueva sección de juegos.
  - Agregá "Juegos de lógica" con alcance v1: Murdoku, 62 casos de 5×5 a 15×15,
    progreso local, sin backend, sin ranking.
  - Aclarar que el backend sigue cerrado y que los juegos no usan sesiones,
    WebSocket ni `/modes`.
- Actualizá `docs/diseno.md`:
  - Tab bar inferior y sus reglas de visibilidad.
  - `shell--wide` y `shell--play`.
  - Sobre de caso: solapa, mini-vista de regiones, sello, estado.
  - Tokens de región (`--region-1..6`, `--region-line`), colores de dificultad.
  - Reglas de accesibilidad del tablero y `prefers-reduced-motion`.
- Actualizá `docs/frontend.md`:
  - La tab bar pasa a ser el acceso persistente a Inicio, Juegos y Ranking.
  - El link de ranking del final del home se elimina.
  - La sección de juegos no habla con la API ni con `/modes`.
- No escribas código de producción.

**No toques:**
- `backend/`, `frontend/src/`, `docs/api.md`.

**Verificación:**
- `git diff --check`.
- Revisión de consistencia: `docs/plan.md` no debe seguir diciendo "dos modos"
  sin aclarar que son los de trivia; no debe haber colores fuera de la paleta.
- Confirmá que la matriz de dificultad suma 62 casos.
- Es una tarea solo de docs: no hace falta `npm run check` ni `npm run build`.

**Commit:**
```
docs(games): define puzzle scale and visual system
```

**Cierre:** actualizá `estado.md` a 1.2. Reportá en 3–5 líneas.

---

### 1.2 — Tab bar, rutas y hub

**Leé:**
- `docs/plan-juegos/diseno.md` §2, §8 (hub), §9 (tab bar).
- `docs/frontend.md` §Menú de inicio, §Rutas y pantallas por modo.
- `frontend/src/routes/+layout.svelte`, `frontend/src/routes/+page.svelte`.
- `frontend/src/app.css` §Columna de la app.
- `frontend/src/lib/i18n/es.json`.

**Hacé:**
- Crear `frontend/src/lib/components/TabBar.svelte`:
  - Destinos: Inicio `/`, Juegos `/juegos`, Ranking `/ranking`.
  - Activo según `page.url.pathname`, con `aria-current="page"`.
  - Iconos SVG propios (agregá `home` y `grid` a `Icon.svelte` si faltan).
  - Fondo `--card-edge`/`--panel-edge`, borde superior, labels en
    `--font-ui`; activo con `--accent` y barra inferior de 3 px.
- Integrar la tab bar en `+layout.svelte`:
  - Visible en home, `/juegos*` y `/ranking`.
  - Oculta en `/play/*`, `/room/*`, `/admin/*` y en la partida de un caso
    (`/juegos/<juego>/<caso>`).
  - Reservar el padding inferior cuando está visible.
- Agregar las clases de shell:
  - `.shell--wide` (960 px) para `/juegos` y `/juegos/murdoku`.
  - `.shell--play` (1100 px) para la partida.
  - Se aplican desde el layout según la ruta.
- Crear el registro `frontend/src/lib/games/types.ts` y
  `frontend/src/lib/games/catalog.ts` con una entrada `murdoku` (ruta, icono,
  acento, orden, claves de texto).
- Crear `/juegos` con:
  - Título "Juegos" y una línea de contexto.
  - Tarjeta de Murdoku (versión simple de `GameCard`; la tarea 1.3 la pule).
  - Estado vacío si el registro no tiene juegos.
- Crear `/juegos/[game]`:
  - Resuelve el juego con `catalog.ts`.
  - Para `murdoku`, muestra el esqueleto del catálogo: header con volver,
    título y un estado "Catálogo en preparación" (la tarea 1.3 lo llena con
    sobres y filtros).
  - Juego desconocido: estado con volver a `/juegos`, sin romper la ruta.
- Eliminar el link de ranking del final de `+page.svelte` y su CSS si queda sin
  uso; la tab bar pasa a ser el acceso persistente.
- Agregar las claves de i18n necesarias en `src/lib/i18n/es.json`.

**No toques:**
- `backend/`, las pantallas de trivia, `src/lib/api/`, `src/lib/modes/`.

**Verificación:**
- `cd frontend && npm run check && npm run build`.
- `npm run test:e2e` (actualizá `e2e/home.spec.ts` si el link de ranking cambió
  y agregá `e2e/games.spec.ts` con: home → Juegos → hub → Murdoku → catálogo;
  juego desconocido → volver).

**Commit:**
```
feat(games): add puzzle hub and tab navigation
```

**Cierre:** actualizá `estado.md` a 1.3. Reportá en 3–5 líneas.

---

### 1.3 — Sobres, componentes compartidos y progreso local

**Leé:**
- `docs/plan-juegos/diseno.md` §5 (modelo y progreso), §8 (sobre), §9
  (tablero y layout), §10 (accesibilidad).
- `frontend/src/app.css` (tokens y botones).
- `frontend/src/lib/components/Icon.svelte`, `Button.svelte`, `Avatar.svelte`.
- `frontend/src/lib/i18n/es.json`.

**Hacé:**
- Completar `src/lib/games/types.ts` con `GameId`, `DifficultyKey`, `Cell`,
  `GameMeta`, `CaseMeta` y `CasePreview`.
- Crear `src/lib/games/difficulty.ts` con orden, labels i18n, colores y conteos.
- Crear `src/lib/games/progress.svelte.ts`:
  - Clave `omnisapiens.games.v1`, versión 1, parseo defensivo.
  - `getCaseProgress`, `saveCaseProgress`, `removeResume`, `clearAll`.
  - Nunca toca `localStorage` si no existe (`typeof window`).
- Crear los componentes compartidos:
  - `GameCard.svelte`: tarjeta del hub con icono, título, descripción, conteo y
    progreso.
  - `CaseEnvelope.svelte`: sobre con solapa SVG, mini-vista de regiones,
    sello de dificultad, título, `N×N`, estado y mejor tiempo. Es un único
    enlace accesible.
  - `DifficultyChips.svelte`: `Todo` + seis niveles, con conteo y estado activo.
  - `PuzzleHeader.svelte`: volver, título, dificultad y slot para el timer.
  - `PuzzleToolbar.svelte`: marcar X, deshacer, pista y reiniciar; recibe
    handlers y estados `disabled`.
- Crear `src/lib/games/murdoku/fixtures.ts` con tres `CasePreview`:
  5×5, 9×9 y 15×15. Solo necesitan regiones, víctima y metadatos para
  renderizar sobres y probar los extremos; no son casos jugables todavía.
- Usar los fixtures en `/juegos/murdoku` para renderizar el grid de sobres y
  los chips; los casos reales llegan en la fase 2.
- Agregar a `Icon.svelte` los iconos que usen los componentes (`home`, `grid`,
  `case`, `check`, `clock`, `arrow`, `x`; reutilizá los existentes).
- Agregar las claves de i18n de dificultad, estados, herramientas y conteos.
- E2E en `e2e/games.spec.ts`: el catálogo muestra 3 sobres de fixture con
  tamaños 5×5, 9×9 y 15×15; los chips filtran y muestran el conteo correcto;
  no hay overflow horizontal en 390 px.

**No toques:**
- `backend/`, el motor de trivia, `src/lib/api/`.
- El solver y el generador (fase 2). No inventes casos jugables acá.

**Verificación:**
- `cd frontend && npm run check && npm run build`.
- `npm run test:e2e`.
- Revisión visual en 390 px y 1280 px: dos columnas de sobres en móvil, cuatro
  en desktop, sin scroll horizontal.

**Commit:**
```
feat(games): add case envelopes and local progress
```

**Cierre:** actualizá `estado.md` a 2.1. Reportá en 3–5 líneas.
