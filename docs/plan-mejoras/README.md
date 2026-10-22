# Plan de mejoras: Juiciness, UI/UX y Contenido — Cómo se trabaja

> Este directorio gobierna la etapa de mejoras de experiencia y sensaciones de juego.
> El agente lo lee al empezar cada sesión cuando el usuario escribe **`comenzemos`**.

## El flujo diario en OpenCode

1. Abrís OpenCode en el proyecto y escribís **`comenzemos`** (o "arrancamos", "dale").
2. El agente lee [`estado.md`](estado.md), ve el rol y la tarea, y **anuncia en ≤5 líneas**
   qué va a hacer, cómo se verifica y qué commit va a generar.
3. Implementa **una sola tarea**, corre la verificación (`npm run check && npm run build` o `make test`) y commitea.
4. Actualiza `estado.md` y los docs que la tarea indique.
5. Te reporta en 3–5 líneas y te pregunta:
   **"¿Seguimos con la tarea X o terminamos por hoy?"**
6. Si decís `seguimos`, arranca la siguiente (si es del mismo rol). Si decís `terminamos`, cierra con el árbol limpio.

El prompt que gobierna todo esto es [`prompts/00-comenzemos.md`](prompts/00-comenzemos.md).

## Reglas del flujo

- **Un rol por sesión.** La tarea declara `frontend` o `backend`. El agente lee el brief
  de ese rol (`docs/frontend.md` o `docs/backend.md`) y **no toca el otro lado**.
- **Una tarea por vez.** La fuente de verdad es `estado.md`. No se salta el orden ni se mezclan tareas.
- **Un commit por tarea**, con el mensaje exacto que especifica la tarea.
- **Verificación obligatoria** antes de commitear:
  - Frontend: `cd frontend && npm run check && npm run build`
  - Backend: `make lint && make test` (y `make check-seeds` si toca preguntas)
- **Los docs se actualizan en el mismo commit** que el cambio: `estado.md` siempre.

## Estructura

```
docs/plan-mejoras/
  README.md            ← este archivo: el flujo de trabajo
  diseno.md            ← diseño técnico de animaciones, haptics y contenido
  estado.md            ← fase, tarea, rol y último commit (lo actualiza el agente)
  prompts/
    00-comenzemos.md   ← el router diario de comandos
    01-fase-1-frontend.md ← F1, F2, F3 (juiciness, feedback, confetti)
    02-fase-2-backend.md  ← B1 (batch 4 de preguntas)
    03-fase-3-frontend.md ← F4, F5 (avatares, tensión, copys)
```
