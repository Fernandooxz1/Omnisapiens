# Fase 2 — Expansión de Contenido (Backend)

> Rol: **backend**. Incorporación de un nuevo lote masivo de preguntas curadas con explicaciones interesantes.

---

### 2.1 — Lote de preguntas Batch 4 (+150 preguntas)

**Rol:** backend · **Depende de:** 1.3 · **Sesión:** 1

**Leé:**
- `docs/preguntas.md` (formato y validaciones)
- `docs/plan-mejoras/diseno.md` §3
- `backend/seeds/questions.csv` y `backend/seeds/questions_batch_3.csv`
- `backend/tools/check_seeds.py`

**Hacé:**
- Crear `backend/seeds/questions_batch_4.csv` con un mínimo de 150 preguntas nuevas, distribuidas en las 6 categorías (`geography`, `history`, `science`, `art`, `entertainment`, `sports`) con dificultades balanceadas de 1 a 5.
- Incluir explicaciones claras y datos curiosos en la columna `explanation`.
- En `backend/tools/check_seeds.py` (o en `Makefile`), incluir `questions_batch_4.csv` en la lista de semillas por defecto.
- Ejecutar `make check-seeds` para certificar que no haya duplicados, columnas faltantes ni errores de formato.
- Probar la migración y carga local con `make seed`.

**No toques:** `frontend/`.

**Verificá:** `python -m tools.check_seeds && make test`.

**Documentá:** `docs/plan-mejoras/estado.md`.

**Commit:** `feat(seeds): add questions batch 4 with 150+ verified items and explanations`

**Hecho cuando:** `make check-seeds` y `make seed` cargan las nuevas preguntas limpiamente sin duplicados.
