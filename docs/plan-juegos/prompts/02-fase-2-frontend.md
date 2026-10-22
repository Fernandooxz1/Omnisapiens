# Fase 2 — Dominio, solver y contenido

> Rol: frontend. Leé `docs/frontend.md` y `docs/plan-juegos/diseno.md` §3–§7 y
> §12. Una tarea por sesión. No toques `backend/`.

---

### 2.1 — Dominio, solver y validador

**Leé:**
- `docs/plan-juegos/diseno.md` §3 (reglas), §4 (dificultad), §5 (modelo),
  §7 (solver), §12 (verificación).
- `frontend/package.json`, `frontend/tsconfig.json`.
- `frontend/src/lib/games/types.ts` (creado en 1.3).

**Hacé:**
- Crear `frontend/src/lib/games/murdoku/types.ts`:
  - `Clue` con todos los tipos del diseño.
  - `MurdokuRegion`, `MurdokuProp`, `MurdokuSuspect`, `MurdokuCase`.
  - `PropIcon` y `SuspectColor`.
- Crear `frontend/src/lib/games/murdoku/rules.ts`:
  - `cellKey`, `cellFromKey`, `sameRegion`, `isAdjacent`, `directionDelta`.
  - `holds(clue, assignment, case)` para una asignación completa.
  - `canHold(clue, partial, case)` para poda con asignación parcial.
  - `killerOf(case, assignment)`: único sospechoso en la región de la víctima.
  - `isValidPlacement` / conflictos de fila y columna.
- Crear `solver.ts`:
  - Víctima fija; los sospechosos no usan su fila ni su columna.
  - Backtracking con máscaras de filas/columnas, MRV y forward checking.
  - `solve(case, limit = 2)` y `countSolutions(case, limit = 2)`.
  - Tope de soluciones 2; no explotar el espacio completo.
- Crear `validate.ts`:
  - `validateCase(case)` devuelve una lista de errores legibles.
  - Solución única, todas las pistas verdaderas, asesino correcto, 1–2 pistas
    por sospechoso, iniciales únicas, víctima dentro de la grilla, fila/columna
    de la víctima libres, regiones válidas y objetos dentro de la grilla.
  - `validateCatalog(cases)` agrega IDs y títulos duplicados.
- Crear `scripts/games/validate-murdoku.ts` y los scripts de `package.json`:
  - `games:generate`, `games:validate`, `test:games`.
  - `games:validate` acepta `--all`, `--id` y `--fixtures`.
- Reemplazar los preview fixtures por **dos casos reales** en
  `src/lib/games/murdoku/fixtures.ts`: uno de 5×5 y uno de 9×9, con solución
  única. El benchmark de 15×15 se hace en 2.3.
- Tests en `src/lib/games/murdoku/*.test.ts` con `node:test`:
  - Predicados de cada tipo de pista.
  - Solver: solución única, cero soluciones, múltiples.
  - Validador: detecta pista falsa, asesino incorrecto, inicial repetida.
- Los módulos puros no importan Svelte ni `window`. Para que Node ejecute
  TypeScript, usá imports relativos con extensión `.ts`; si `svelte-check` se
  queja, habilitá `allowImportingTsExtensions` en `tsconfig.json`.

**No toques:**
- `backend/`, pantallas, rutas, componentes visuales.
- El generador (tarea 2.2).

**Verificación:**
- `cd frontend && npm run test:games`.
- `npm run games:validate -- --fixtures`.
- `npm run check && npm run build`.

**Commit:**
```
feat(murdoku): add solver and validation pipeline
```

**Cierre:** actualizá `estado.md` a 2.2. Reportá en 3–5 líneas.

---

### 2.2 — Generador 5×5 a 9×9

**Leé:**
- `docs/plan-juegos/diseno.md` §4 (matriz), §6 (pistas), §7 (generador).
- `frontend/src/lib/games/murdoku/types.ts`, `rules.ts`, `solver.ts`,
  `validate.ts`.

**Hacé:**
- Crear `frontend/src/lib/games/murdoku/generate.ts`:
  - PRNG `mulberry32` con semilla.
  - Selección de víctima y permutación de personas.
  - 4–6 regiones contiguas por crecimiento aleatorio desde semillas; nombres
    temáticos; 4–10 objetos temáticos sin compartir celda con personas.
  - Enumeración de pistas candidatas verdaderas (región, negación, dirección,
    adyacencia, misma región, objeto, borde).
  - Una pista obligatoria por sospechoso; pistas extra con selección greedy
    hasta unicidad; eliminación de extras redundantes.
  - Clasificación de complejidad y nivel; reintento con otra semilla si el
    tamaño/nivel no coincide.
- Crear `frontend/src/lib/games/murdoku/themes.ts` con al menos 8 escenarios
  (estudio, biblioteca, invernadero, cocina, museo, tren, faro, teatro) con
  nombres de regiones y objetos en español neutro.
- Generar **48 casos de 5×5 a 9×9** con esta distribución:
  - 5×5 muy fácil: 6
  - 6×6 fácil: 8
  - 7×7 fácil: 6
  - 7×7 medio: 6
  - 8×8 medio: 8
  - 9×9 medio: 10
  - 9×9 difícil: 4
- Escribir `frontend/src/lib/games/murdoku/cases/standard.ts` (array tipado,
  ordenado por número). IDs `murdoku-001` en adelante.
- Crear `cases/index.ts` que exporte `allCases`, `findCase` y
  `byDifficulty`; por ahora solo importa `standard`.
- El generador es determinista: la misma semilla produce el mismo caso. Guardá
  `meta.seed`.
- No escribas UI nueva.

**No toques:**
- `backend/`, rutas, componentes.
- Casos de 10×10 a 15×15 (tarea 2.3).

**Verificación:**
- `cd frontend && npm run games:generate -- --max-size 9`.
- `npm run games:validate -- --all`.
- `npm run test:games`.
- `npm run check && npm run build`.
- Revisá el conteo por nivel y que no haya IDs ni títulos duplicados.

**Commit:**
```
feat(murdoku): generate standard case catalog
```

**Cierre:** actualizá `estado.md` a 2.3. Reportá en 3–5 líneas con el conteo
por nivel.

---

### 2.3 — Generador 10×10 a 15×15

**Leé:**
- `docs/plan-juegos/diseno.md` §4, §7 (rendimiento), §12.
- `frontend/src/lib/games/murdoku/generate.ts`, `solver.ts`, `validate.ts`.

**Hacé:**
- Optimizar el solver y el generador para tableros grandes:
  - Evitar alocaciones por celda en el hot loop.
  - Poda temprana de pistas evaluables con una variable asignada.
  - Reintentos con semillas distintas y tope de tiempo por caso.
- Generar **14 casos de 10×10 a 15×15**:
  - 10×10 difícil: 6
  - 12×12 muy difícil: 4
  - 14×14 hardcore: 2
  - 15×15 hardcore: 2
- Escribir `cases/large.ts` e importarlo desde `cases/index.ts`.
- Mantener el determinismo y guardar `meta.seed`.
- Agregar un benchmark al script de generación o de validación:
  - tiempo por caso de 15×15,
  - tiempo total del batch grande,
  - cantidad de reintentos.
- Si un caso no se valida dentro del presupuesto, no se publica: reducí el
  conteo y reportá el faltante. No bajes la calidad de la validación.
- No escribas UI nueva.

**No toques:**
- `backend/`, rutas, componentes.
- Los 48 casos estándar ya generados, salvo que el generador compartido cambie
  y haya que regenerarlos (en ese caso, validá los 62).

**Verificación:**
- `cd frontend && npm run games:generate -- --min-size 10`.
- `npm run games:validate -- --all`.
- `npm run test:games`.
- `npm run check && npm run build`.
- Reportá tiempos del benchmark y conteo real por nivel.

**Commit:**
```
feat(murdoku): generate large and hardcore cases
```

**Cierre:** actualizá `estado.md` a 2.4. Reportá en 3–5 líneas.

---

### 2.4 — Curaduría y tutorial

**Leé:**
- `docs/plan-juegos/diseno.md` §4, §6 (textos), §11 (contenido).
- `frontend/src/lib/games/murdoku/cases/` completo.
- `frontend/src/lib/i18n/es.json` (claves de pistas).

**Hacé:**
- Revisar los 62 casos:
  - Gramática y naturalidad de cada pista en español neutro.
  - Sin voseo, sin emojis, sin violencia explícita.
  - Sin pistas tautológicas, ambiguas o que revelen al asesino.
  - Títulos únicos y escenarios coherentes con las regiones/objetos.
  - Iniciales únicas y colores legibles.
- Corregir plantillas o datos y regenerar si hace falta; volver a validar.
- Marcar el primer caso 5×5 como tutorial (`tutorial: true` en `CaseMeta`) y
  escribir el texto de los 3 pasos del panel "Cómo jugar" en `es.json`:
  1. una persona por fila y columna,
  2. leer las pistas,
  3. el asesino es quien queda a solas con la víctima.
- Publicar el catálogo definitivo en `cases/index.ts` y verificar los conteos
  de la matriz.
- No implementes el panel visual: eso es 3.3.

**No toques:**
- `backend/`.
- El motor de partida y las pantallas (fase 3).

**Verificación:**
- `cd frontend && npm run games:validate -- --all`.
- `npm run test:games`.
- `npm run check && npm run build`.
- Reportá: casos publicados por nivel, total, y cualquier tamaño que no haya
  llegado al objetivo.

**Commit:**
```
feat(murdoku): curate catalog and add tutorial
```

**Cierre:** actualizá `estado.md` a 3.1. Reportá en 3–5 líneas.
