# Plan de juegos de lógica — Murdoku

> Este directorio gobierna la sección nueva de juegos. Mientras
> [`estado.md`](estado.md) diga `activo: true`, el flujo diario sale de acá.

## Qué se construye

Una sección `/juegos` separada de los modos de trivia, con un hub de tarjetas y
un catálogo de casos. La v1 incluye **solo Murdoku**: un puzzle de deducción
sobre una grilla donde se colocan sospechosos, se leen pistas y se descubre al
asesino.

- **Sin backend nuevo.** Los casos viven en el frontend y el progreso en
  `localStorage`.
- **Sin cuenta ni red para jugar.** El temporizador es local; no hay ranking ni
  puntaje competitivo.
- **62 casos** de 5×5 a 15×15, en seis niveles: muy fácil, fácil, medio,
  difícil, muy difícil y hardcore.
- **Arquitectura lista para sumar Sudoku** después, sin reescribir el shell.

## El flujo diario

1. Abrís OpenCode en el proyecto y escribís **`comencemos`** (o `comenzemos`).
2. El agente lee [`estado.md`](estado.md), ve la tarea y **anuncia en ≤5 líneas**
   qué va a hacer, cómo se verifica y qué commit va a generar.
3. Implementa **una sola tarea** y corre la verificación que pide el prompt.
4. Actualiza `estado.md` y commitea.
5. Te reporta en 3–5 líneas y pregunta:
   **"¿Seguimos con la tarea X o terminamos por hoy?"**
6. Si decís `seguimos`, arranca la siguiente. Si decís `terminamos`, cierra con
   el árbol limpio.

El router que gobierna esto es
[`prompts/00-comenzemos.md`](prompts/00-comenzemos.md).

## Reglas del flujo

- **Un rol por sesión.** Todas las tareas de este plan son `frontend`; el
  backend no se toca. Si una tarea parece necesitar backend, se para y se
  pregunta.
- **Una tarea por vez.** La fuente de verdad es `estado.md`. No se salta el
  orden ni se mezclan tareas.
- **Un commit de código por tarea**, con el mensaje exacto que especifica el
  prompt. `estado.md` se registra en un commit aparte de bookkeeping
  (`docs(plan): record task X completion`), como en el plan anterior.
- **Verificación obligatoria**:
  - Frontend: `cd frontend && npm run check && npm run build`
  - Dominio/contenido: además `npm run test:games` y `npm run games:validate`
  - Pantallas: además la e2e de Playwright que corresponda.
- **Los docs se actualizan en el mismo commit** que el cambio. `estado.md` se
  actualiza siempre al cerrar.
- **Nada de `git add -A`, `git checkout`, `git restore` ni `git stash`.**

## Estructura del plan

```
docs/plan-juegos/
  README.md                 ← este archivo
  diseno.md                 ← spec técnica y visual (fuente de verdad del diseño)
  estado.md                 ← fase, tarea, rol y último commit
  prompts/
    00-comenzemos.md        ← router diario
    01-fase-1-frontend.md   ← 1.1–1.3: sección, navegación y sistema visual
    02-fase-2-frontend.md   ← 2.1–2.4: dominio, solver y contenido
    03-fase-3-frontend.md   ← 3.1–3.4: motor, tablero y partida
    04-fase-4-frontend.md   ← 4.1: cierre de v1
```

## Fases

| Fase | Nombre | Tareas | Estado |
|---|---|---|---|
| 1 | Sección, navegación y sistema visual | 1.1 – 1.3 | pendiente |
| 2 | Dominio, solver y contenido | 2.1 – 2.4 | pendiente |
| 3 | Motor, tablero y partida | 3.1 – 3.4 | pendiente |
| 4 | Cierre de v1 | 4.1 | pendiente |

## Criterio de terminado

Se entra desde la tab bar, se ve el hub, se elige Murdoku, se filtra por
dificultad, se abre un caso por deep link, se resuelve con ratón o teclado, se
guarda el progreso, se puede reanudar y el caso siguiente se abre sin volver al
inicio. Los casos de 5×5 a 15×15 se validan con solución única y las suites
`check`, `build`, `test:games`, `games:validate` y `test:e2e` quedan en verde.

## Fuera de alcance de la v1

Sudoku, Nonogram, ranking de juegos, cuentas, sincronización en la nube,
multijugador, editor de casos, caso diario, monetización y cualquier cambio en
`backend/`.

## Relación con los otros planes

- `docs/plan-mejoras/` cerró el 2026-10-22 (`activo: false`).
- `docs/tareas.md` y `docs/tareas-backend.md` quedan congeladas mientras este
  plan esté activo.
- Cuando `docs/plan-juegos/estado.md` pase a `activo: false`, vuelve el flujo
  normal de `AGENTS.md`.
