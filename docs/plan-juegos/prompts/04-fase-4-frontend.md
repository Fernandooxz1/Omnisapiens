# Fase 4 — Cierre de v1

> Rol: frontend. Última tarea del plan. No toques `backend/`.

---

### 4.1 — Pulido, accesibilidad y cierre

**Leé:**
- `docs/plan-juegos/diseno.md` §9–§12.
- `docs/plan.md` (sección de juegos).
- `docs/diseno.md` (tab bar, sobres, tablero).
- `frontend/e2e/games.spec.ts`.
- `frontend/src/service-worker.ts`.

**Hacé:**
- **Accesibilidad:**
  - Recorrido completo con teclado: tab bar, hub, chips, sobres, tablero,
    expediente, herramientas, comprobar y victoria.
  - Foco visible y orden lógico; `aria-live` para colocaciones, conflictos y
    resolución.
  - Revisar contraste AA y que las regiones no dependan solo del color.
  - `prefers-reduced-motion` en sobres, tablero, errores y confetti.
- **Offline/PWA:**
  - Verificar que el catálogo y los casos ya visitados funcionan sin red.
  - Confirmar que el service worker no rompe los deep links.
- **Performance:**
  - Medir el caso 15×15: abrir, hacer zoom, colocar y comprobar sin tirones.
  - Revisar el tamaño del chunk del catálogo y la carga diferida.
- **Copy:**
  - Revisar textos de hub, catálogo, pistas, herramientas, errores y victoria.
  - Español neutro, sin voseo, sin emojis.
  - Confirmar que el nombre visible de Murdoku es una clave de i18n.
- **Docs:**
  - Actualizar `docs/plan.md` y `docs/diseno.md` si la implementación se
  desvió de lo escrito.
  - Actualizar `README.md` del repo solo si la sección de juegos cambia lo que
    el README describe como producto.
  - Dejar `docs/plan-juegos/estado.md` con `activo: false`, `estado: hecho` y
    la fecha de cierre.
- **Verificación final:**

```bash
cd frontend
npm run test:games
npm run games:validate -- --all
npm run check
npm run build
npm run test:e2e
```

- Reportá: casos publicados por nivel, total, tiempos del benchmark de 15×15,
  resultado de la suite e2e y cualquier cosa que haya quedado fuera.

**No toques:**
- `backend/`.
- Casos ya validados, salvo correcciones de copy que no cambien la solución.

**Commit:**
```
feat(games): polish puzzle section and document v1
```

**Cierre:** `estado.md` con `activo: false`, `fase: 4`, `tarea: "—"`,
`estado: hecho`. Reportá en 3–5 líneas y avisá que el plan cerró.
