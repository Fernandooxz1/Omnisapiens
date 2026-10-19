# Archivo — backend histórico

El backend está **terminado** (HTTP, WS, salas, arcade, ranking, admin, 553 tests, cobertura
94 %) y no se toca desde el frontend. Todo lo de esta carpeta es memoria de cómo quedó por
dentro. **No se lee** salvo que una tarea toque el backend o haya que responder por qué el
servidor se comporta de una manera.

| Archivo | Qué es |
|---|---|
| `backend/arquitectura.md` | Anexo A del plan: capa de datos, migraciones, decisiones irreversibles. |
| `backend/trampas.md` | Anexo B: decisiones y trampas del backend (la memoria de lo que ya costó un bug). |
| `backend/observaciones.md` | Auditoría H-01..H-25, **cerrada**. |
| `agents-backend.md` | El `AGENTS.md` que regía cuando el trabajo era backend. |

Lo que el frontend **sí** necesita del backend vive en `docs/api.md` (contrato y trampas del
cliente) y `docs/plan.md` (modos, reglas y puntajes). No hace falta venir acá.
