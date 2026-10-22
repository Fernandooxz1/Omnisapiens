# Fase 3 — Motor, tablero y partida

> Rol: frontend. Leé `docs/frontend.md` y `docs/plan-juegos/diseno.md` §9–§10.
> Una tarea por sesión. No toques `backend/`.

---

### 3.1 — Motor de partida y persistencia

**Leé:**
- `docs/plan-juegos/diseno.md` §3 (reglas), §5 (progreso), §9 (semántica de
  partida), §10 (accesibilidad).
- `frontend/src/lib/games/murdoku/types.ts`, `rules.ts`, `solver.ts`.
- `frontend/src/lib/games/progress.svelte.ts`.
- `frontend/src/lib/match/live.svelte.ts` (patrón de estado reactivo).

**Hacé:**
- Crear `frontend/src/lib/games/murdoku/engine.ts` (puro, sin Svelte):
  - Estado: `placements`, `marks`, `history`, `selectedId`, `mode`
    (`place` | `mark`), `hintsUsed`, `startedAt`, `elapsedMs`, `status`
    (`idle` | `playing` | `solved`), `attempts`, `lastError`.
  - Acciones: seleccionar sospechoso, colocar, mover, marcar/desmarcar X,
    deshacer, pista, reiniciar, comprobar.
  - Reglas:
    - No se permite otra persona en la misma fila o columna.
    - Colocar mueve al sospechoso si ya estaba en otra celda.
    - Colocar limpia la X de la celda y de su fila/columna; deshacer restaura.
    - Pista: coloca correctamente a un sospechoso sin ubicar o mal ubicado e
      incrementa `hintsUsed`.
    - Comprobar: solo con todos colocados; valida pistas y asesino; si falla,
      `attempts++` y `lastError` genérico; si acierta, `status: solved`.
  - Historial acotado (por ejemplo, 200 acciones) para no crecer sin límite.
- Crear `engine.svelte.ts`:
  - Estado reactivo con runas sobre el motor puro.
  - Timer: arranca con la primera acción; se pausa con `visibilitychange`;
    formato `mm:ss` y `hh:mm:ss` si hace falta.
  - Persistencia: carga `resume`, guarda con debounce de 300 ms, borra al
    resolver; no toca `localStorage` si no existe.
  - Derivados: `filled`, `canSubmit`, `isSolved`, `killer`.
- Tests en `engine.test.ts` con `node:test`: colocar, mover, conflicto,
  marcar/auto-limpiar, deshacer, pista, comprobar correcto/incorrecto.

**No toques:**
- `backend/`, componentes visuales, rutas.
- El solver (solo lo consumís).

**Verificación:**
- `cd frontend && npm run test:games`.
- `npm run check && npm run build`.

**Commit:**
```
feat(murdoku): add game engine and persistence
```

**Cierre:** actualizá `estado.md` a 3.2. Reportá en 3–5 líneas.

---

### 3.2 — Tablero, tokens y viewport

**Leé:**
- `docs/plan-juegos/diseno.md` §9 (tablero, viewport, layout), §10
  (accesibilidad).
- `frontend/src/app.css` (tokens, foco, reduced motion).
- `frontend/src/lib/games/murdoku/types.ts`, `engine.svelte.ts`.
- `frontend/src/lib/components/Icon.svelte`.

**Hacé:**
- Agregar a `app.css` los tokens de región (`--region-1..6`, `--region-line`)
  y lo necesario para el tablero.
- Crear `PropIcon.svelte` con al menos 8 iconos SVG propios (estantería, piano,
  planta, silla, lámpara, cuadro, reloj, caja, televisor, alfombra). Trazo 2.5,
  `currentColor`, sin emojis.
- Crear `SuspectToken.svelte`: inicial, color de familia, base sólida, estado
  seleccionado; la víctima usa un token "V" con borde de peligro.
- Crear `MurdokuBoard.svelte`:
  - Grilla `repeat(var(--size), 1fr)` con `aspect-ratio: 1`.
  - Tinte de región, borde grueso entre regiones, etiqueta/leyenda.
  - Objetos, víctima, sospechosos, X, celda seleccionada y conflictos.
  - Roles `grid`/`row`/`gridcell` y `aria-label` completo.
- Crear `BoardViewport.svelte`:
  - Modo ajustar y zoom `-`/`+` (32, 40, 48 px) con scroll en ambos ejes.
  - La celda enfocada se mantiene visible con `scrollIntoView`.
  - En móvil, el tablero queda sticky arriba; el expediente va debajo.
- Crear la ruta `frontend/src/routes/juegos/murdoku/[case]/+page.svelte`
  mínima: resuelve el caso, muestra un back al catálogo y monta el tablero.
  La pantalla completa (header, expediente, herramientas, victoria) es 3.3.
- Navegación por teclado: flechas, `Enter` para colocar, `X` para marcar,
  `Backspace` para borrar, `Ctrl/Cmd+Z` para deshacer, `H` para pista.
- `prefers-reduced-motion`: sin sacudidas ni transiciones largas.

**No toques:**
- `backend/`, el motor puro, el catálogo.
- La pantalla completa de partida (3.3).

**Verificación:**
- `cd frontend && npm run check && npm run build`.
- E2E mínima en `e2e/games.spec.ts`: abrir un caso 9×9, contar las celdas,
  enfocar con teclado y colocar un sospechoso; smoke de un 15×15 con zoom.
- Revisión visual en 390 px y 1280 px.

**Commit:**
```
feat(murdoku): add responsive board viewport
```

**Cierre:** actualizá `estado.md` a 3.3. Reportá en 3–5 líneas.

---

### 3.3 — Pantalla de caso completa

**Leé:**
- `docs/plan-juegos/diseno.md` §8 (catálogo y sobre), §9 (layout, partida), §10.
- `frontend/src/lib/games/murdoku/engine.svelte.ts`.
- `frontend/src/lib/components/Confetti.svelte`, `TimerBadge.svelte`,
  `Icon.svelte`, `Button.svelte`.
- `frontend/src/lib/sound.svelte.ts`, `haptics.ts`, `toast.svelte.ts`.
- `frontend/src/lib/i18n/es.json`.

**Hacé:**
- Completar `/juegos/murdoku/[case]`:
  - `PuzzleHeader`: volver al catálogo, título, dificultad, timer y botón de
    pausa si corresponde.
  - `CaseFile`: tarjetas de sospechosos con su(s) pista(s) y la tarjeta de la
    víctima; en desktop, rail lateral; en móvil, solapas `Sospechosos`/`Pistas`.
  - `PuzzleToolbar`: marcar X, deshacer, pista, reiniciar.
  - Botón `Comprobar` habilitado con todos colocados.
  - Estado de error: "Algo no cierra", sacudida del tablero, sin revelar qué
    pista falla.
  - Victoria: asesino, región, tiempo, pistas usadas, `Siguiente caso` y
    `Volver al catálogo`; confetti solo en el primer caso resuelto o nuevo
    mejor tiempo; sonido y haptics existentes.
  - Panel "Cómo jugar" para el caso tutorial (3 pasos).
  - Reanudar: si hay `resume`, ofrecer continuar; si no, empezar de cero.
- Integrar `progress.svelte.ts`: guardar al cerrar y al resolver; borrar el
  resume al resolver.
- Agregar las claves de i18n que falten.
- E2E: resolver el tutorial 5×5 de punta a punta, ver la victoria y volver al
  catálogo; comprobar que el sobre queda resuelto.

**No toques:**
- `backend/`, el motor puro, el solver.
- El catálogo (3.4), salvo lo mínimo para volver.

**Verificación:**
- `cd frontend && npm run check && npm run build`.
- `npm run test:e2e`.
- Revisión visual en 390 px y 1280 px: sin scroll horizontal, tablero legible,
  expediente usable.

**Commit:**
```
feat(murdoku): add case screen and victory flow
```

**Cierre:** actualizá `estado.md` a 3.4. Reportá en 3–5 líneas.

---

### 3.4 — Catálogo definitivo de sobres

**Leé:**
- `docs/plan-juegos/diseno.md` §8 (catálogo y sobre), §5 (progreso).
- `frontend/src/lib/games/murdoku/cases/index.ts`.
- `frontend/src/lib/games/components/CaseEnvelope.svelte`,
  `DifficultyChips.svelte`.
- `frontend/src/routes/juegos/[game]/+page.svelte`.

**Hacé:**
- Reemplazar los fixtures del catálogo por los 62 casos reales.
- `/juegos/murdoku`:
  - Header con volver, título y resumen "X de 62 resueltos".
  - Chips `Todo` + seis niveles, con conteo real.
  - Con `Todo`, secciones por nivel con encabezado y conteo; con un nivel
    elegido, solo esa sección.
  - Grid de sobres con estado (`sin abrir`, `en curso`, `resuelto` + mejor
    tiempo) y `Continuar` cuando hay `resume`.
  - Orden por número; deep links; sin bloqueos.
  - Estado vacío por filtro y estado de error si el catálogo no carga.
- Hub `/juegos`: conteo real de casos y progreso.
- Eliminar el uso de fixtures en producción; los fixtures quedan solo para
  tests.
- E2E: filtros y conteos, abrir un caso por sobre, resolver el tutorial,
  volver y ver el sobre como resuelto con mejor tiempo, deep link directo.

**No toques:**
- `backend/`, el motor, el solver.
- La pantalla de partida (3.3).

**Verificación:**
- `cd frontend && npm run check && npm run build`.
- `npm run test:e2e`.
- Revisión visual en 390 px, 768 px y 1280 px.

**Commit:**
```
feat(murdoku): add envelope catalog and filters
```

**Cierre:** actualizá `estado.md` a 4.1. Reportá en 3–5 líneas.
