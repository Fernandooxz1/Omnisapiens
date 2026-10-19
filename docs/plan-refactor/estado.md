# Estado del refactor

> **Fuente de verdad del progreso.** Lo actualiza el agente al cerrar cada tarea.
> No se edita a mano. Si hay conflicto entre este archivo y un prompt, manda este.

```yaml
activo: true
fase: 1
tarea: "1.2"
rol: backend
estado: pendiente        # pendiente | en curso | hecho | bloqueado
ultimo_commit: 8edbec9
fecha: 2026-10-19
bloqueo: ""
```

## Fases

| Fase | Nombre | Rol | Tareas | Estado |
|---|---|---|---|---|
| 0 | Red de seguridad | backend | 0.1 | hecho |
| 1 | Núcleo de reglas | backend | 1.1 – 1.3 | pendiente |
| 2 | Contenido genérico | backend | 2.1 – 2.4 | pendiente |
| 3 | Sesiones, ranking y barrendero | backend | 3.1 – 3.5 | pendiente |
| 4 | Port del arcade | backend | 4.1 – 4.3 | pendiente |
| 5 | Port del 1v1 | backend | 5.1 – 5.3 | pendiente |
| 6 | Registro y rutas genéricas | backend | 6.1 – 6.3 | pendiente |
| 7 | Frontend multi-modo | frontend | 7.1 – 7.3 | pendiente |
| 8 | Rosco (**opcional**) | backend + frontend | 8.1 – 8.5 | pendiente |
| 9 | Medios (**opcional**) | backend + frontend | 9.1 – 9.4 | pendiente |
| 10 | Cierre | backend | 10.1 – 10.2 | pendiente |

## Historial

| Fecha | Tarea | Commit | Nota |
|---|---|---|---|
| 2026-10-19 | — | `fce8ce0` | Diseño y flujo creados. Próxima: 0.1. |
| 2026-10-19 | 0.1 | `2f3a018` | Transcripts de arcade, 1v1 y reconexión congelados; guardia de fuga. Próxima: 1.1. |
| 2026-10-19 | 1.1 | `8edbec9` | `ServedItem`, `Submission`, `Verdict` y `settle` con ventana y `grade` por modo. Próxima: 1.2. |
