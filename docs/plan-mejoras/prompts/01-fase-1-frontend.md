# Fase 1 — Juiciness y Feedback de Combate (Frontend)

> Rol: **frontend**. Respuestas elásticas, vibración táctil, rachas vivas y festejo de victoria.

---

### 1.1 — Pop de acierto, pérdida de vida dramática y haptics

**Rol:** frontend · **Depende de:** — · **Sesión:** 1

**Leé:**
- `docs/plan-mejoras/diseno.md` §2.1 y §2.2
- `frontend/src/app.css` (clases `.tile` y `@keyframes tile-shake`)
- `frontend/src/lib/components/AnswerTile.svelte`
- `frontend/src/lib/components/LifeStrip.svelte`
- `frontend/src/lib/sound.svelte.ts`

**Hacé:**
- Crear `frontend/src/lib/haptics.ts` con funciones seguras para `tap()`, `success()` y `error()` usando `navigator.vibrate` si está soportado.
- En `AnswerTile.svelte` / `app.css`:
  - Agregar `@keyframes tile-pop` para la clase `.tile.is-correct` (escalado sutil 1.04 y retorno con resorte elástico en 0.22s).
  - Al dispararse la resolución de respuesta, ejecutar `haptics.success()` si fue acierto o `haptics.error()` si fue error.
- En `LifeStrip.svelte` / `app.css`:
  - Agregar `@keyframes heart-break` al pasar un corazón a `.is-off` (sacudida horizontal rápida y salto antes de atenuarse a gris).
- Respetar `@media (prefers-reduced-motion: reduce)`.

**No toques:** `backend/`.

**Verificá:** `cd frontend && npm run check && npm run build`.

**Documentá:** `docs/plan-mejoras/estado.md`.

**Commit:** `feat(ui): add correct tile pop, heart-break animation and haptic feedback`

**Hecho cuando:** al responder correctamente la opción salta alegremente con feedback táctil en móvil, y al fallar el corazón tiembla y se rompe dramáticamente.

---

### 1.2 — Racha en llamas y puntos flotantes (+pts)

**Rol:** frontend · **Depende de:** 1.1 · **Sesión:** 1

**Leé:**
- `docs/plan-mejoras/diseno.md` §2.3
- `frontend/src/lib/components/Icon.svelte`
- `frontend/src/lib/modes/arcade/ArcadeScreen.svelte`
- `frontend/src/app.css`

**Hacé:**
- En `Icon.svelte`: agregar el ícono SVG `flame` (grid 24, trazo 2.5, trazo cerrado para colorear).
- En `ArcadeScreen.svelte`:
  - Cuando `run.streak >= 2`, mostrar el ícono de llama y un badge dinámico de racha con pulso alegre.
  - Al recibir los puntos de la ronda (`result.you.points`), mostrar un flotador temporal `.points-floater` con el texto `+{puntos}` que asciende y se desvanece suavemente.
  - Interpolar el contador numérico de puntaje en el HUD para que aumente rápidamente de forma fluida en vez de cambiar en seco.

**No toques:** `backend/`.

**Verificá:** `cd frontend && npm run check && npm run build`.

**Documentá:** `docs/plan-mejoras/estado.md`.

**Commit:** `feat(ui): add flame streak indicator and floating points animation`

**Hecho cuando:** acumular racha enciende la llama y los puntos ganados flotan hacia arriba en cada acierto.

---

### 1.3 — Fin de partida épico (conteo y confetti)

**Rol:** frontend · **Depende de:** 1.2 · **Sesión:** 1

**Leé:**
- `docs/plan-mejoras/diseno.md` §2.4
- `frontend/src/lib/modes/arcade/ArcadeScreen.svelte`
- `frontend/src/lib/modes/versus/VersusScreen.svelte`
- `frontend/src/app.css`

**Hacé:**
- Crear componente ligero `frontend/src/lib/components/Confetti.svelte` que renderice una lluvia suave de partículas geométricas sobre un canvas temporal (sin bibliotecas externas pesadas).
- En `ArcadeScreen.svelte`:
  - Si `end.isNewBest`, disparar `Confetti.svelte` y animar el puntaje final con un conteo ascendente desde 0.
- En `VersusScreen.svelte`:
  - Si el jugador gana la partida 1v1, disparar `Confetti.svelte` para festejar la victoria.

**No toques:** `backend/`.

**Verificá:** `cd frontend && npm run check && npm run build`.

**Documentá:** `docs/plan-mejoras/estado.md`.

**Commit:** `feat(ui): add victory confetti and end-game score counting animation`

**Hecho cuando:** lograr un nuevo récord o ganar una partida 1v1 se festeja con confetti y el puntaje final se revela con emoción.
