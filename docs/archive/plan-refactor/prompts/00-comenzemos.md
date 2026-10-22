# Prompt — `comenzemos`

> Este es el router diario. El usuario escribe **`comenzemos`**, **`seguimos`**,
> **`terminamos`** o **`¿cómo vamos?`**. Seguí este protocolo al pie de la letra.
> No diseñes nada nuevo: si falta una decisión, pará y preguntá.

## 0. Contexto que manda

- **El refactor está activo** mientras `docs/plan-refactor/estado.md` diga `activo: true`.
- Durante el refactor, la cola de trabajo es `estado.md`, **no** `docs/tareas.md` ni
  `docs/tareas-backend.md`.
- El diseño está en `docs/plan-refactor/diseno.md`. Las decisiones cerradas están en su
  §1 y no se reabren.
- Las reglas del repo (`AGENTS.md`) siguen vigentes: un rol por sesión, no tocar el otro
  lado, un commit por tarea, nada de `git add -A` / `checkout` / `restore` / `stash`.

## 1. Arranque (`comenzemos`)

1. `git status --short`.
   - Si hay cambios sin commitear: **pará**. Decí qué archivos están sucios y preguntá
     si son de una tarea anterior. No uses `stash`, `checkout` ni `restore`.
2. Leé `docs/plan-refactor/estado.md`.
   - Si `activo: false`: volvé al flujo normal de `AGENTS.md` y avisá que el refactor
     terminó.
   - Si `estado: bloqueado`: leé `bloqueo`, reportalo y preguntá cómo seguir.
3. Leé el archivo de la fase en `docs/plan-refactor/prompts/`: el que termina en
   `-fase-<fase>.md` (ej. fase 3 → `04-fase-3.md`) y ubicá el encabezado de la tarea
   `### <tarea>`. Si no existe, pará y avisá que el estado está desincronizado.
4. Verificá que el `rol` de la tarea coincida con el `rol` de `estado.md`. Si no, pará.
5. Leé el brief del rol:
   - `backend` → `docs/backend.md`
   - `frontend` → `docs/frontend.md`
   Y **solo** los archivos que la tarea lista en `Leé:`. No releas todo el proyecto.
   Durante el refactor, **ignorá** la instrucción del brief de leer `docs/tareas*.md`:
   la cola es `estado.md`.
6. Si la fase es **opcional** (8 o 9) y es la primera tarea de esa fase, preguntá:
   "La fase N es opcional. ¿La hacemos o cerramos el refactor acá?"

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
- Respetá `No toques:` (el otro lado, archivos fuera de alcance, tablas viejas).
- Escribí o actualizá los tests que la tarea pida. Si no pide tests y el cambio toca
  lógica, agregalos: no hay tarea cerrada sin red.
- Si aparece una decisión no prevista: **pará y preguntá**. No inventes arquitectura.
- Si la tarea no entra en una sesión: pará, proponé el corte y no dejes trabajo a medias.

## 4. Verificación

- **backend**: `make lint && make cov && make check-schema`
- **frontend**: `cd frontend && npm run check && npm run build`
- **e2e** (si la tarea lo pide): `make up && make migrate && make seed`, API en `:8000`,
  y `cd frontend && npm run test:e2e`.

Si algo falla:
1. Si es un test del cambio, arreglalo dentro del alcance.
2. Si el arreglo exige cambiar el diseño o tocar el otro lado: **no commitees**, reportá
   el fallo y preguntá.

## 5. Cierre de la tarea

1. Stageá **solo** las rutas de la tarea (las de `Hacé:` + los docs que indique).
2. Commit con el mensaje exacto de `Commit:`. Un commit por tarea.
3. Actualizá los docs de `Documentá:` y `docs/plan-refactor/estado.md`:
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
- Si no hay próxima tarea, decí que el refactor terminó y ofrecé la fase 10 o cerrar.

## 7. `terminamos`

1. Verificá que el árbol esté limpio (`git status --short`).
2. Confirmá que `estado.md` apunta a la próxima tarea y tiene el último hash.
3. Resumí el día: tareas hechas, commits, próxima tarea y rol.
4. No dejes trabajo sin commitear ni procesos corriendo (API, frontend, Playwright).

## 8. `¿cómo vamos?`

Leé `estado.md` y respondé en ≤6 líneas: fase, tarea actual, rol, último commit, próxima
tarea y cualquier bloqueo. No implementes nada.

## 9. Señales de alto

Pará y preguntá si:

- el árbol está sucio al arrancar;
- la tarea no coincide con `estado.md`;
- falta una decisión de diseño;
- la verificación falla por algo fuera del alcance;
- la tarea no entra en la sesión;
- hay que tocar el otro lado;
- hay que cambiar un contrato (`docs/api.md`) sin tarea que lo autorice.

## 10. Recordatorio

El objetivo no es "escribir mucho código": es que **cada tarea deje el repo en verde y
la siguiente sea obvia**. Si dudás, elegí la opción que mantiene el árbol limpio y el
diseño intacto.
