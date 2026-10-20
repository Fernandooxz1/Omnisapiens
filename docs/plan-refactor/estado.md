# Estado del refactor

> **Fuente de verdad del progreso.** Lo actualiza el agente al cerrar cada tarea.
> No se edita a mano. Si hay conflicto entre este archivo y un prompt, manda este.

```yaml
activo: false
fase: 10
tarea: "10.2"
rol: backend
estado: hecho            # pendiente | en curso | hecho | bloqueado
ultimo_commit: e56ed15
fecha: 2026-10-20
bloqueo: ""
```

## Fases

| Fase | Nombre | Rol | Tareas | Estado |
|---|---|---|---|---|
| 0 | Red de seguridad | backend | 0.1 | hecho |
| 1 | Núcleo de reglas | backend | 1.1 – 1.3 | hecho |
| 2 | Contenido genérico | backend | 2.1 – 2.4 | hecho |
| 3 | Sesiones, ranking y barrendero | backend | 3.1 – 3.5 | hecho |
| 4 | Port del arcade | backend | 4.1 – 4.3 | hecho |
| 5 | Port del 1v1 | backend | 5.1 – 5.3 | hecho |
| 6 | Registro y rutas genéricas | backend | 6.1 – 6.3 | hecho |
| 7 | Frontend multi-modo | frontend | 7.1 – 7.3 | hecho |
| 8 | Rosco (**opcional**) | backend + frontend | 8.1 – 8.5 | no se hizo (opcional) |
| 9 | Medios (**opcional**) | backend + frontend | 9.1 – 9.4 | no se hizo (opcional) |
| 10 | Cierre | backend | 10.1 – 10.2 | hecho |

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
| 2026-10-19 | 4.3 | `3859e78` | Borrados `arcade_engine`, `arcade_session` y `services/arcade_runs`; `ARCADE_RULES` en `modes/arcade.py`, tests portados al motor/store. Tag `refactor-fase-4`. Próxima: 5.1. |
| 2026-10-19 | 5.1 | `f6a8651` | `versus_engine` puro (partida, sillas, gracia, pausa, revancha) y sesiones versus en `InMemorySessionStore` con outbox por silla y vencimientos; tests de `match_engine`/`room` portados. Próxima: 5.2. |
| 2026-10-19 | 5.2 | `9c30ee6` | `/ws/room` corre sobre el store directo: el borde elige y carga la pregunta, persiste `game_sessions` con ítems/intentos/participantes y sigue escribiendo `matches`/`rooms`; `room_manager` eliminado. Golden y e2e de 1v1 sin cambios. Próxima: 5.3. |
| 2026-10-20 | 5.3 | `cc62f9f` | Borrados `match_engine` y `runtime/room` con sus tests ya portados; `matches`/`match_rounds` quedan de solo lectura y `rooms` sigue en el borde. Golden y e2e de 1v1 sin cambios. Tag `refactor-fase-5`. Próxima: 6.1. |
| 2026-10-20 | 6.1 | `45c4042` | `trivia_arcade` y `trivia_versus` registrados con reglas/progresión/scoring, `config_schema` y `public_schema`; `GET /modes` y el ranking salen de `mode.ranking`. `GameMode` gana `name`/`input`/`media`. Próxima: 6.2. |
| 2026-10-20 | 6.2 | `892070d` | `POST /sessions` valida modo, formato solo y `config_schema`; `WS /ws/session/{id}` juega con el protocolo canónico (`session_start`/`item_start`/`item_result`/`session_end`/`session_state`) sobre el mismo store, con presentador inyectable. El arcade viejo queda como adaptador y el golden no cambia. Próxima: 6.3. |
| 2026-10-20 | 6.3 | `7d994a1` | Contrato multi-modo documentado (catálogo, `POST /sessions`, protocolo canónico, ranking por modo y errores), matriz de compatibilidad con la ventana de cada alias y tests de paridad en `test_api_compat.py`; `dual-write` eliminado de `api.md`. Tag `refactor-fase-6`. Próxima: 7.1. |
| 2026-10-20 | 7.1 | `db10e8d` | `fetchModes()` y registry por `code` (ruta, renderer, orden y textos); la home arma los botones desde `GET /modes`, deshabilita los modos sin renderer y muestra el ranking solo si alguno publica tabla. Próxima: 7.2. |
| 2026-10-20 | 7.2 | `a36ee38` | `/play/[mode]` monta el renderer del registry: `ArcadeScreen` y `VersusScreen` (lobby + sala) viven en `src/lib/modes/`; `/arcade` y `/play` redirigen y la sala sigue en `/room/{code}`. Próxima: 7.3. |
| 2026-10-20 | 7.3 | `498c87d` | Arcade sobre el canal canónico (`POST /sessions` + `WS /ws/session/{id}`) sin badge de categoría; e2e nuevas de catálogo y rutas `/play/trivia_*`; `/arcade` y `/play` retiradas. Tag `refactor-fase-7`. Próxima: 8.1 (opcional). |
| 2026-10-20 | — | `2c52e3e` | Pulido frontend: «partida» en la copia, repaso final plegable, corte de sesión honesto, esqueleto/reintento del catálogo y redirects viejos restaurados. Brief backend en `docs/prompts/backend-partida.md`. Próxima: 8.1 (opcional). |
| 2026-10-20 | 10.1 | `9f9d084` | Migración `0006` dropea `questions`, `matches`, `match_rounds`, `arcade_runs` y `arcade_answers`; `/me`, el barrendero y el ranking leen `game_sessions`. Próxima: 10.2. |
| 2026-10-20 | 10.2 | `e56ed15` | Cierre verificado desde base limpia: migraciones `0001`–`0006`, tres seeds, 689 tests al 92 %, `svelte-check` y build en Node 24, 11 e2e; test de aceptación de un modo nuevo. Tag `refactor-multimodo`. Refactor cerrado. |
