# Estado del refactor

> **Fuente de verdad del progreso.** Lo actualiza el agente al cerrar cada tarea.
> No se edita a mano. Si hay conflicto entre este archivo y un prompt, manda este.

```yaml
activo: true
fase: 4
tarea: "4.3"
rol: backend
estado: pendiente        # pendiente | en curso | hecho | bloqueado
ultimo_commit: be75081
fecha: 2026-10-19
bloqueo: ""
```

## Fases

| Fase | Nombre | Rol | Tareas | Estado |
|---|---|---|---|---|
| 0 | Red de seguridad | backend | 0.1 | hecho |
| 1 | Núcleo de reglas | backend | 1.1 – 1.3 | pendiente |
| 2 | Contenido genérico | backend | 2.1 – 2.4 | hecho |
| 3 | Sesiones, ranking y barrendero | backend | 3.1 – 3.5 | hecho |
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
| 2026-10-19 | 1.2 | `ed73f0a` | `SoloRules`/`SoloEngine` parametrizan vidas y curvas; `arcade_engine` queda como fachada. Próxima: 1.3. |
| 2026-10-19 | 1.3 | `8cadbf7` | `GameMode`, protocolos, tipos de contenido y registro vacío; conformance lista. Tag `refactor-fase-1`. Próxima: 2.1. |
| 2026-10-19 | 2.1 | `a6e9353` | `content_items`/`content_solutions`, migración `0004` y constraints con tests. Próxima: 2.2. |
| 2026-10-19 | 2.2 | `56775c9` | `backfill-content --kind quiz` idempotente, mismo UUID y hash; `make backfill-content`. Próxima: 2.3. |
| 2026-10-19 | 2.3 | `591c512` | `QuizContent` (payload/solución versionados, candidates/load); import dual-write, CLI `import-content` y admin `/admin/content/{kind}`. Próxima: 2.4. |
| 2026-10-19 | 2.4 | `dee81e3` | Banco lee `content_items`/`content_solutions`; se corta el dual-write; `0004b` repunta las FK del historial. Tag `refactor-fase-2`. Próxima: 3.1. |
| 2026-10-19 | 3.1 | `5afa1da` | `game_sessions`/`game_participants`/`session_items`/`session_attempts`, `rooms.mode` y `0005`; el `CHECK` de `rooms.config` se relaja y valida en Python. Próxima: 3.2. |
| 2026-10-19 | 3.2 | `6088b98` | `services/sessions.py`: arranque, cierre atómico e idempotente con ítems e intentos, abandono e invalidación; sin relojes propios. Próxima: 3.3. |
| 2026-10-19 | 3.3 | `fab2814` | `backfill-sessions` reconstruye arcade y 1v1 con el mismo puntaje y secuencia; salta `playing` y tolera contenido huérfano. Próxima: 3.4. |
| 2026-10-19 | 3.4 | `b7791dd` | Ranking por modo sobre `game_sessions` (`finished` + dueño), `/leaderboard/{mode}`, alias `arcade` y `404 MODE_WITHOUT_RANKING`; `run_summary` sigue en `arcade_runs` hasta 4.2. Próxima: 3.5. |
| 2026-10-19 | 3.5 | `a751b30` | `Live.sessions` y barrido de `game_sessions` `playing` viejas → `invalid`; los tres barridos viejos siguen. Tag `refactor-fase-3`. Próxima: 4.1. |
| 2026-10-19 | 4.1 | `9e380c1` | `SessionStore`/`InMemorySessionStore` para solo: outbox, reloj inyectado, vencimientos, cierre idempotente y `live.sessions`; el borde inyecta el `ItemSource`. Próxima: 4.2. |
| 2026-10-19 | 4.2 | `be75081` | `arcade_ws` vive sobre el store y el `SoloEngine`: escribe `game_sessions`/ítems/intentos, `run_summary` lee `game_sessions`, `on_finish` completa el ranking antes del `arcade_end`; golden y e2e de arcade sin cambios. Próxima: 4.3. |
