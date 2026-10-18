# Observaciones — auditoría del backend

> Auditoría hecha el 2026-10-17 leyendo todo `backend/` (app, tests, migraciones) contra
> `docs/plan.md`. **Cerrada de punta a punta**: H-01..H-25 resueltos y verificados con
> tests y sabotajes (H-07 incluido: guard de un solo proceso con `SINGLE_PROCESS`, más los
> dos tests de concurrencia que faltaban). Este documento quedó **comprimido a lo que sigue
> abierto**; el detalle de cada hallazgo resuelto (evidencia, reproducción y arreglo) vive en
> el historial de git, en la versión anterior de este archivo
> (`git log -p -- docs/observaciones.md`).

## Veredicto

El proyecto está muy bien construido: capas limpias, motor puro, constraints de verdad en
Postgres, tests contra servicios reales y comentarios que explican el *porqué*. Los
problemas que importaban no eran de arquitectura sino de **cierre de ciclos de vida** (el
socket que se va tarde, el reloj que muere callado, lo que nadie cierra al apagar): los dos
P0 eran silenciosos y estaban en el camino "en vivo". Ya están todos corregidos.

## Notas de implementación (nada pendiente)

Tres cosas que hoy se sostienen por una razón fina. No son bugs: son el día en que hay que
mirar de nuevo si el contexto cambia.

| # | Qué | Dónde |
|---|---|---|
| — | `open()` sin lock: el desalojo y el alta no tienen `await` en el medio → atómicos en el event loop, **pero solo por eso**. Si se agrega I/O ahí, va bajo lock. | `room_manager.py` |
| — | `_pick`/`_serve_next` toman el lock de la sala durante I/O de Postgres: una base lenta bloquea sala **y** reloj. Con 60 preguntas es irrelevante; con banco grande, se elige la pregunta **antes** de tomar el lock. | `room_manager.py` |
| — | Hasta 2 sesiones de base por transición (`_persist` y `_pick` abren la suya): con pool por defecto (5+10) y muchas salas, agotamiento del pool. | `room_manager.py` |

## Calidad de datos: lo que la base no garantiza

**Sí garantiza:** forma y valores de `config` (`IS NOT DISTINCT FROM`), coherencia
`media_type`/`media_url`, `correct_index` 0–3, longitud y `btrim` del enunciado,
`content_hash` único en hex, `options` como array de 4 strings, consistencia de
`a_correct`/`a_choice`/`a_ms`/`a_rejected` en `match_rounds` **y** `arcade_answers`, no
negatividad de puntajes, `longest_streak ≤ correct_count`, `ended_at ≥ started_at`, y el
`status` de la corrida atado a `ended_at`.

| Hueco | Riesgo |
|---|---|
| Opciones **no vacías ni repetidas**: solo en Python (`services/importer.py`), no en la base | una fila insertada a mano o por SQL pasa inválida (el `CHECK` cubre el tipo, no el contenido) |
| `questions.language` admite solo `'es'` | decisión consciente; al entrar un idioma nuevo, la migración es un `CHECK` a mano |
| `matches` sin "una sola partida `playing` por sala" | con un barrendero lento, dos filas `playing` de la misma sala son posibles (cosmético: el ranking no las usa) |
| Falta índice `(player_a_id, started_at DESC)` (y para B) | "mis últimas partidas" filtrará por dos columnas distintas |

**Sin `relationship()`** es a propósito (evita cargas implícitas en async), pero el orden de
los INSERT lo arregla el test a mano (`tests/factories.py`, `acepta()`). Cuando el
`room_manager` inserte filas relacionadas de verdad, chocará con lo mismo: no
"arreglarlo" con un `relationship()` apurado.

## Lo que está muy bien (no romper)

1. **El motor es puro y el borde es sucio a propósito**: `now_ms`, `sleep` y `rng` se
   inyectan; una partida entera corre en milisegundos con el `FakeClock`.
2. **La respuesta correcta no puede filtrarse: no está en el tipo** (`RoundQuestion`), y un
   `hasattr` lo vigila. Lo garantiza el compilador, no el reviewer.
3. **Constraints reales, con nombre propio, verificados contra el catálogo**, más la guardia
   de schema que compara texto de Postgres contra texto de Postgres.
4. **Un solo escritor por socket, con lock compartido**: dos `send` concurrentes no son
   seguros y acá está resuelto por diseño.
5. **La pausa corre el reloj en vez de regalarlo** (`room._resume`): al reconectar se
   desplazan el arranque y las respuestas ya dadas por el hueco de la pausa.
6. **El `outbox` en vez de un callback**: el vencimiento entrega sin que nadie espere del
   otro lado. Es lo que hizo arreglable H-02 sin tocar nada más.
7. **Tests contra Postgres y Redis reales**, sin SQLite, con aislamiento por savepoint, y un
   cliente WS propio en el mismo event loop (`tests/ws_client.py`).
8. **Los comentarios explican el porqué y las trampas** (Anexo B del plan): es la memoria que
   evita re-descubrir lo mismo dos veces.

## Cómo volver a verificar

```bash
make up            # Postgres 16 + Redis 7
make lint          # ruff (select) + format + mypy strict
make check-schema  # alembic check: sin drift modelos↔migraciones
make test          # verde, sin umbral de cobertura
make cov           # el gate: cobertura contra el umbral de 85 %
```

El CI (`.github/workflows/ci.yml`) corre los mismos targets con Postgres y Redis como
*services*. Tests que fijan hallazgos resueltos:
`test_the_old_socket_closing_late_does_not_abandon_the_reconnected_player` (H-01),
`test_the_clock_retries_*` (H-02), `test_the_room_row_follows_the_match_lifecycle` y
`test_a_dead_room_is_evicted_when_another_one_opens` (H-03/H-04),
`test_start_is_rejected_after_the_match_finished` (H-06),
`test_the_lifespan_refuses_a_deployment_that_did_not_declare_one_process` (H-07),
`test_two_answers_of_the_same_seat_at_once_count_once` y
`test_two_rooms_share_the_rng_and_nothing_else` (concurrencia),
`tests/test_reaper.py`,
`tests/test_logging.py` (H-08/H-12), `test_shuffle_options_breaks_the_position_bias` y
`test_serving_shuffles_the_options_and_the_correct_one_moves` (H-25).
