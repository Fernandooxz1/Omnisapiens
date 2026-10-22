# Plan del refactor multi-modo — cómo se trabaja

> Este directorio es la memoria del refactor. El agente lo lee al empezar cada sesión.
> **No se diseña sobre la marcha**: el diseño está en [`diseno.md`](diseno.md) y las
> decisiones cerradas en la §1 de ese archivo.

## El flujo diario

1. Abrís OpenCode en el proyecto y escribís **`comenzemos`** (o "arrancamos", "dale").
2. El agente lee [`estado.md`](estado.md), ve el rol y la tarea, y **anuncia en ≤5 líneas**
   qué va a hacer y cómo se verifica.
3. Implementa **una sola tarea**, corre la verificación y commitea.
4. Actualiza `estado.md` y los docs que la tarea indique.
5. Te reporta en 3–5 líneas y te pregunta:
   **"¿Seguimos con la tarea X o terminamos por hoy?"**
6. Si decís `seguimos`, arranca la siguiente. Si decís `terminamos`, cierra el día con
   el árbol limpio y deja anotada la próxima tarea.

El prompt que gobierna todo esto es
[`prompts/00-comenzemos.md`](prompts/00-comenzemos.md). Está pensado para que el agente
lo siga sin improvisar.

## Reglas del flujo

- **Un rol por sesión.** La tarea declara `backend` o `frontend`. El agente lee el brief
  de ese rol (`docs/backend.md` o `docs/frontend.md`) y **no toca el otro lado**.
- **Una tarea por vez.** La fuente de verdad es `estado.md`. No se salta el orden ni se
  mezclan tareas.
- **Una tarea entra en una sesión.** Si no entra, se parte antes de empezar: el agente
  avisa y propone el corte. No se deja trabajo a medias sin commitear.
- **Un commit por tarea**, con el mensaje exacto que dice la tarea. Se stagean solo las
  rutas de la tarea. Nunca `git add -A`, `git checkout`, `git restore` ni `git stash`.
- **Verificación obligatoria** antes de commitear:
  - backend: `make lint && make cov && make check-schema`;
  - frontend: `npm run check && npm run build`; e2e si la tarea lo pide.
- **Los docs se actualizan en el mismo commit** que el cambio: `docs/api.md` si cambia
  el contrato, `docs/plan.md` si cambian reglas, `estado.md` siempre.
- **Si falta una decisión, se para y se pregunta.** No se inventa arquitectura.
- **Si algo falla y no se arregla dentro del alcance, no se commitea.** Se reporta y se
  pregunta.

## Estructura

```
docs/plan-refactor/
  README.md            ← este archivo: el flujo
  diseno.md            ← el diseño y las decisiones cerradas
  estado.md            ← fase, tarea, rol, último commit (lo actualiza el agente)
  prompts/
    00-comenzemos.md   ← el router diario
    01-fase-0.md       ← red de seguridad
    02-fase-1.md       ← núcleo de reglas
    03-fase-2.md       ← contenido genérico
    04-fase-3.md       ← sesiones y ranking
    05-fase-4.md       ← port del arcade
    06-fase-5.md       ← port del 1v1
    07-fase-6.md       ← registro y rutas
    08-fase-7.md       ← frontend
    09-fase-8.md       ← rosco (opcional)
    10-fase-9.md       ← medios (opcional)
    11-fase-10.md      ← cierre
```

## Cómo se lee una tarea

Cada tarea tiene este formato:

```
### 3.2 — Servicio de sesiones
Rol: backend · Depende de: 3.1 · Sesión: 1
Leé: ...
Hacé: ...
No toques: ...
Verificá: ...
Documentá: ...
Commit: ...
Hecho cuando: ...
```

El agente lee **solo** la tarea actual y los archivos que lista. No relee todo el
proyecto: para eso está el diseño y el brief del rol.

## Cuándo termina el refactor

**Cerró el 2026-10-20** (`activo: false` en `estado.md`). Terminó cuando la tarea 10.2
verificó:

- las tablas viejas dropeadas en la migración `0006`;
- `make lint`, `make cov`, `make check-schema` y e2e en verde desde una base limpia;
- `activo: false` en `estado.md`;
- el flujo normal de `AGENTS.md` vuelve a mandar (`docs/tareas.md` y
  `docs/tareas-backend.md`).

Este directorio queda como historial del diseño; no se reabre.

## Si el refactor se pausa

`estado.md` queda con la próxima tarea. Al retomar, `comenzemos` continúa exactamente
donde quedó. No hay estado en la cabeza de nadie.
