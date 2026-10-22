# Prompt — `comenzemos`

> Este es el router diario. El usuario escribe **`comenzemos`**, **`seguimos`**,
> **`terminamos`** o **`¿cómo vamos?`**. Seguí este protocolo al pie de la letra.
> No diseñes nada nuevo: si falta una decisión, pará y preguntá.

## 0. Contexto que manda

- **El plan de mejoras está activo** mientras `docs/plan-mejoras/estado.md` diga `activo: true`.
- Durante este plan, la cola de trabajo es `docs/plan-mejoras/estado.md`, **no** `docs/tareas.md` ni `docs/tareas-backend.md`.
- El diseño técnico está en `docs/plan-mejoras/diseno.md`.
- Las reglas del monorepo (`AGENTS.md`) siguen vigentes: un rol por sesión, no tocar el otro
  lado, un commit por tarea, nada de `git add -A` / `checkout` / `restore` / `stash`.

## 1. Arranque (`comenzemos`)

1. `git status --short`.
   - Si hay cambios sin commitear: **pará**. Decí qué archivos están sucios y preguntá
     si son de una tarea anterior. No uses `stash`, `checkout` ni `restore`.
2. Leé `docs/plan-mejoras/estado.md`.
   - Si `activo: false`: volvé al flujo normal de `AGENTS.md` y avisá que el plan terminó.
   - Si `estado: bloqueado`: leé `bloqueo`, reportalo y preguntá cómo seguir.
3. Leé el archivo de la fase en `docs/plan-mejoras/prompts/`: el que corresponda a la fase
   (ej. fase 1 → `01-fase-1-frontend.md`) y ubicá el encabezado de la tarea
   `### <tarea>`. Si no existe, pará y avisá que el estado está desincronizado.
4. Verificá que el `rol` de la tarea coincida con el `rol` de `estado.md`. Si no, pará.
5. Leé el brief del rol:
   - `backend` → `docs/backend.md`
   - `frontend` → `docs/frontend.md`
   Y **solo** los archivos que la tarea lista en `Leé:`. No releas todo el proyecto.
   Durante este plan, **ignorá** la instrucción del brief de leer `docs/tareas*.md`:
   la cola es `estado.md`.

## 2. Anuncio (≤5 líneas)

Antes de tocar nada, decí:

```
Hoy: <rol> · fase <fase> · tarea <tarea> — <título>.
Voy a: <1–2 líneas>.
Verificación: <comando>.
Commit: <mensaje>.
```

No empieces a editar hasta que el anuncio esté hecho.

## 3. Ejecución

- Implementá **exactamente** el alcance de `Hacé:`.
- Respetá `No toques:` (el otro lado, archivos fuera de alcance).
- Si aparece una decisión no prevista: **pará y preguntá**.
- Si la tarea no entra en una sesión: pará, proponé el corte y no dejes trabajo a medias.

## 4. Verificación

- **backend**: `make lint && make test` (y `python -m tools.check_seeds` si toca semillas).
- **frontend**: `cd frontend && npm run check && npm run build`.

Si algo falla:
1. Si es un test o verificación del cambio, arreglalo dentro del alcance.
2. Si el arreglo exige cambiar el diseño o tocar el otro lado: **no commitees**, reportá
   el fallo y preguntá.

## 5. Cierre de la tarea

1. Stageá **solo** las rutas de la tarea (las de `Hacé:` + los docs que indique).
2. Commit con el mensaje exacto de `Commit:`. Un commit por tarea.
3. Actualizá `docs/plan-mejoras/estado.md`:
   - `ultimo_commit: <hash>`
   - `fase`, `tarea`, `rol` → la siguiente tarea
   - `estado: pendiente`
   - agregá una fila al historial con fecha, tarea, hash y una nota corta.
4. Reportá en 3–5 líneas:
   ```
   Hecho: <qué>.
   Verificado: <comandos y resultado>.
   Commit: <hash>.
   Próxima: <fase>.<tarea> — <título> (<rol>).
   ```
5. Preguntá: **"¿Seguimos con <fase>.<tarea> o terminamos por hoy?"**

## 6. `seguimos`

- Si la próxima tarea es del **mismo rol**, volvé al paso 1 con esa tarea.
- Si es del **otro rol**, no la arranques en esta sesión: decí
  "La próxima es <rol>. Abrí una sesión nueva con ese rol y escribí `comenzemos`."
  (Regla del repo: un rol por sesión.)
- Si no hay próxima tarea, cerrá el plan en `estado.md` con `activo: false`.

## 7. `terminamos`

- Decí: "Listo por hoy. El árbol quedó limpio en `<hash>`. La próxima sesión arranca en `<fase>.<tarea>`."

## 8. `¿cómo vamos?`

- Mostrá el contenido de `docs/plan-mejoras/estado.md` en formato resumido y decí cuál es la
  próxima tarea.
