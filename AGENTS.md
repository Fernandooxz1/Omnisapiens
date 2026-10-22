# AGENTS.md — Omnisapiens

Monorepo de trivia online y juegos de lógica: `backend/` (FastAPI) y `frontend/` (SvelteKit + PWA).

## Flujo activo: sección de juegos (Murdoku)

Mientras `docs/plan-juegos/estado.md` diga `activo: true`, el flujo diario es el de
`docs/plan-juegos/README.md`:

- Si el usuario escribe **`comencemos`**, **`comenzemos`**, **`seguimos`** o **`terminamos`**,
  seguí `docs/plan-juegos/prompts/00-comenzemos.md` al pie de la letra.
- La cola del plan es `docs/plan-juegos/estado.md`. `docs/tareas.md` y
  `docs/tareas-backend.md` quedan congeladas hasta que este plan cierre.
- El rol, la tarea, la verificación y el mensaje de commit salen de la tarea, no de
  este archivo.
- Las reglas de abajo siguen vigentes.

El plan de mejoras cerró el 2026-10-22 (`docs/plan-mejoras/estado.md` con `activo: false`).
Cuando el plan de juegos cierre, vuelve el flujo normal de este archivo.

## Flujo normal

**Cada sesión tiene un rol y no cambia de lado.** Al empezar, leé el brief de tu rol y nada más:

| Rol | Brief | Cola de tareas |
|---|---|---|
| Frontend | `docs/frontend.md` | `docs/tareas.md` |
| Backend | `docs/backend.md` | `docs/tareas-backend.md` |

## Reglas del árbol (valen para los dos)

- **Una tarea por vez**: la primera sin `[x]` de la cola de tu rol.
- **`frontend/` y `backend/` no se tocan cruzado.** Leer el otro lado está bien; editarlo, no.
  Si falta contrato, se anota en `docs/api.md` y se implementa del lado que corresponde.
- **El servidor es autoritativo**: tiempos, puntajes, resultado de ronda y ganador salen de
  él. El cliente solo dibuja. En los juegos de lógica no hay puntaje competitivo: el
  cronómetro es local y no se publica.
- **Un commit de código por tarea, en inglés.** El estado del plan activo se registra en un
  commit de bookkeeping aparte. Los docs compartidos (`api.md`, `plan.md`, `diseno.md`)
  se actualizan en el mismo commit que los cambia.
- **Nunca `git add -A`, `git checkout`, `git restore` ni `git stash`**: puede haber otra sesión
  con trabajo sin commitear en el mismo árbol. Stageá y commiteá solo tus rutas.
- **El repo es la memoria**: no se cierra la sesión con trabajo sin commitear.
