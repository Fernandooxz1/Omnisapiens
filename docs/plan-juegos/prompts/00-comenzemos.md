# Prompt — `comencemos` / `comenzemos`

> Router diario del plan de juegos. El usuario escribe **`comencemos`**,
> **`comenzemos`**, **`seguimos`**, **`terminamos`** o **`¿cómo vamos?`**.
> Seguí este protocolo al pie de la letra. No diseñes nada nuevo: si falta una
> decisión, pará y preguntá.

## 0. Contexto que manda

- **El plan de juegos está activo** mientras `docs/plan-juegos/estado.md` diga
  `activo: true`.
- La cola de trabajo es `docs/plan-juegos/estado.md`, **no** `docs/tareas.md` ni
  `docs/tareas-backend.md`.
- La spec está en `docs/plan-juegos/diseno.md`; los prompts de fase, en
  `docs/plan-juegos/prompts/`.
- Las reglas del monorepo (`AGENTS.md`) siguen vigentes: un rol por sesión, no
  tocar el otro lado, un commit de código por tarea, nada de `git add -A` /
  `checkout` / `restore` / `stash`.
- Todas las tareas de este plan son **frontend**. Si una tarea parece necesitar
  backend, pará y preguntá.

## 1. Arranque (`comencemos` / `seguimos`)

1. `git status --short`.
   - Si hay cambios sin commitear: **pará**. Decí qué archivos están sucios y
     preguntá si son de una tarea anterior. No uses `stash`, `checkout` ni
     `restore`.
2. Leé `docs/plan-juegos/estado.md`.
   - Si `activo: false`: volvé al flujo normal de `AGENTS.md` y avisá que el plan
     terminó.
   - Si `estado: bloqueado`: leé `bloqueo`, reportalo y preguntá cómo seguir.
   - Si `estado: hecho` y `activo: true`: el estado está desincronizado; pará y
     preguntá cuál es la próxima tarea.
3. Leé el archivo de la fase en `docs/plan-juegos/prompts/`:
   - fase 1 → `01-fase-1-frontend.md`
   - fase 2 → `02-fase-2-frontend.md`
   - fase 3 → `03-fase-3-frontend.md`
   - fase 4 → `04-fase-4-frontend.md`
   Ubicá el encabezado `### <tarea>`. Si no existe, pará y avisá que el estado
   está desincronizado.
4. Verificá que el `rol` de la tarea coincida con el rol de `estado.md`. Si no,
   pará.
5. Leé el brief del rol: `docs/frontend.md`. Después, **solo** los archivos que
   la tarea lista en `Leé:`. Durante este plan, ignorá la instrucción del brief
   de leer `docs/tareas.md`: la cola es `docs/plan-juegos/estado.md`.
6. Si la tarea toca diseño, leé la sección de `docs/plan-juegos/diseno.md` que
   indique el prompt. No releas el archivo entero si no hace falta.

## 2. Anuncio (≤5 líneas)

Antes de tocar nada, decí:

```
Hoy: frontend · fase <fase> · tarea <tarea> — <título>.
Voy a: <1–2 líneas>.
Verificación: <comando>.
Commit: <mensaje>.
```

No empieces a editar hasta que el anuncio esté hecho.

## 3. Ejecución

- Implementá **exactamente** el alcance de `Hacé:`.
- Respetá `No toques:`.
- Si aparece una decisión no prevista: **pará y preguntá**.
- Si la tarea no entra en una sesión: pará, proponé el corte y no dejes trabajo
  a medias.
- No agregues dependencias nuevas salvo que la tarea lo autorice.
- No toques `backend/`.
- No uses `git add -A`. Stageá solo las rutas de la tarea.

## 4. Verificación

La base para toda tarea de frontend:

```bash
cd frontend && npm run check && npm run build
```

Según la tarea:

```bash
npm run test:games
npm run games:validate -- --all
npm run test:e2e
```

Si algo falla:

1. Si es un test o verificación del cambio, arreglalo dentro del alcance.
2. Si el arreglo exige cambiar el diseño, tocar el backend o salir del alcance:
   **no commitees**, reportá el fallo y preguntá.

## 5. Cierre de la tarea

1. Stageá **solo** las rutas de la tarea (las de `Hacé:` + los docs que indique).
2. Commit con el mensaje exacto de la tarea.
3. Sacá el hash corto del commit: `git rev-parse --short HEAD`.
4. Actualizá `docs/plan-juegos/estado.md`:
   - `ultimo_commit: <hash>`
   - `fase`, `tarea`, `rol` → la siguiente tarea
   - `estado: pendiente` (o `hecho` si era la última)
   - agregá una fila al historial con fecha, tarea, hash y una nota corta
   - si el plan terminó, `activo: false`
5. Stageá **solo** `docs/plan-juegos/estado.md` y commiteá el bookkeeping:
   ```
   docs(plan): record task <tarea> completion
   ```
   Son dos commits: el de la tarea y el del estado. El plan anterior usa la misma
   convención.
6. Reportá en 3–5 líneas:

```
Hecho: <qué>.
Verificado: <comandos y resultado>.
Commit: <hash>.
Próxima: <fase>.<tarea> — <título>.
```

7. Preguntá: **"¿Seguimos con <fase>.<tarea> o terminamos por hoy?"**

## 6. `terminamos`

- No empieces una tarea nueva.
- Verificá que el árbol quede limpio.
- Reportá el último commit y la próxima tarea.
- No borres el plan: queda `activo: true` con la próxima tarea pendiente.
