# Fase 3 — Personalidad y Tensión (Frontend)

> Rol: **frontend**. Avatares con emblemas, copys con personalidad y tensión en los últimos segundos.

---

### 3.1 — Emblemas e íconos de avatar

**Rol:** frontend · **Depende de:** 2.1 · **Sesión:** 1

**Leé:**
- `frontend/src/lib/components/Avatar.svelte`
- `frontend/src/lib/components/AccentPicker.svelte`
- `frontend/src/lib/accent.ts`
- `frontend/src/lib/components/Icon.svelte`

**Hacé:**
- Permitir al jugador elegir un emblema o accesorio para su avatar (ej: cerebro, rayo, corona, fuego, anteojos, estrella).
- Persistir la preferencia en `localStorage` junto con el acento de color.
- Renderizar el emblema de forma armónica dentro o junto al avatar en todas las pantallas.

**No toques:** `backend/`.

**Verificá:** `cd frontend && npm run check && npm run build`.

**Documentá:** `docs/plan-mejoras/estado.md`.

**Commit:** `feat(ui): add avatar emblem customization alongside accent colors`

**Hecho cuando:** el jugador puede elegir y ver su emblema distintivo en su avatar en toda la interfaz.

---

### 3.2 — Tensión visual de tiempo y copys dinámicos

**Rol:** frontend · **Depende de:** 3.1 · **Sesión:** 1

**Leé:**
- `frontend/src/lib/components/TimerBadge.svelte`
- `frontend/src/lib/i18n/es.json`
- `frontend/src/app.css`

**Hacé:**
- Agregar un pulso perimetral sutil (`@keyframes danger-pulse`) en la tarjeta de pregunta y el marco de la pantalla cuando restan menos de 4 segundos.
- Enriquecer los copys en `es.json` con frases más ingeniosas y divertidas para victorias, derrotas y rachas.

**No toques:** `backend/`.

**Verificá:** `cd frontend && npm run check && npm run build`.

**Documentá:** `docs/plan-mejoras/estado.md`.

**Commit:** `feat(ui): add last-seconds danger pulse and lively localized copy`

**Hecho cuando:** la cuenta regresiva transmite tensión visual genuina y los textos tienen chispa y humor.
