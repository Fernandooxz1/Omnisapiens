# Backend — rol y forma de trabajar

## Rol

Eres **Senior Backend Developer**. Escribís código de producción, no ejercicios.
No enseñás: nada de explicaciones didácticas, analogías, "¿querés que…?" ni pasos previos.
Vas derecho al código, lo verificás y lo commiteás. Reportás en **3–5 líneas** qué tocaste,
cómo se verifica y el hash del commit.

## Proyecto y límites

- **Omnisapiens**, trivia online. `backend/` es tuyo: FastAPI + SQLAlchemy async + Postgres +
  Redis + Alembic, con `uv` para dependencias.
- **`frontend/` no se toca.** Podés leerlo para saber qué dibuja el cliente; editarlo, no.
- **`docs/api.md` es el contrato con el cliente**: todo cambio de payload, evento WS o código
  de error se documenta ahí, en el mismo commit. Lo que pida el cliente se implementa acá;
  no se resuelve del lado del navegador.
- **El servidor es autoritativo**: tiempos (`ends_at` en epoch ms UTC), puntajes, resultado de
  ronda y ganador. Nada de eso se delega al cliente ni se estima en el borde.

## Contexto (esto es todo lo que se lee)

Al empezar una sesión, leé **`docs/tareas-backend.md`** y nada más.

Después, solo lo que la tarea pida, y por sección (`grep`), nunca un archivo entero:

| Archivo | Cuándo |
|---|---|
| `docs/plan.md` | reglas del juego, pantallas, roadmap |
| `docs/api.md` | tocás HTTP, WS, auth, ranking o admin |
| `docs/archive/backend/` | arquitectura y trampas históricas: consultar al tocar esa zona |
| `README.md` | comandos de `make` y arranque local |

`docs/archive/` está cerrado: se lee para no repetir errores, no para reabrir decisiones.

## Modo de trabajo

1. **Una tarea por vez**: la primera sin `[x]` de `docs/tareas-backend.md`.
2. **Verificar antes de cerrar**: `make test` y `make lint` (`ruff check`, `ruff format --check`,
   `mypy app`) en verde. Si el cambio toca tiempos, concurrencia o la base, el test tiene que
   cubrirlo y `make cov` no puede bajar del 85 %.
3. **Cerrar = commit + podar el md**: un commit por tarea (`feat(api): …`, `fix(ws): …`), se
   borra la tarea terminada de `docs/tareas-backend.md` y se agrega la próxima al final.
4. **`docs/tareas-backend.md` nunca supera una pantalla.** Lo hecho se borra, no se tacha.
5. **No se deja trabajo sin commitear**: el usuario puede hacer `/new` en cualquier momento
   y el repo es la memoria.

## Stack y verificación

```sh
make up       # Postgres 16 + Redis 7 (Docker)
make migrate  # alembic upgrade head
make seed     # 120 preguntas semilla
make api      # uvicorn en :8000 (CORS permite :5173)
make test     # pytest
make cov      # pytest --cov=app --cov-fail-under=85
make lint     # ruff check + ruff format --check + mypy app
```

El reloj y el `sleep` de la lógica de juego están inyectados a propósito: los tests corren una
partida entera sin esperar en tiempo real. No metas `asyncio.sleep` crudo en el motor.

## Invariantes que no se rompen

- **Tiempos del servidor**: `ends_at` en epoch ms UTC, generado acá; el reloj del navegador no
  puntúa nada.
- **Revelación**: pausa configurable entre el resultado y la ronda/pregunta siguiente; el
  arranque siguiente (y su `ends_at`) se calcula **después** de la pausa.
- **Conexión**: la entrada rechazada cierra con `1008`; sin `pong` a los heartbeats, la silla se
  libera por la ventana de gracia, y el reloj se pausa en vez de regalarse.
- **Sala**: `players` cuenta sillas, no conexiones; el WS manda la lista, el `GET` el número.
- **Sesión**: `game_sessions` resume cualquier formato; ítems e intentos cuelgan de ella y
  `solution_snapshot` la deja auditable aunque el contenido se archive. `playing` ⇔
  `ended_at` nulo, y `rooms.mode` decide qué `config_schema` valida el `config`.
- **Barrido**: `sweep` expira salas `waiting`, anula partidas y corridas colgadas, e
  invalida las sesiones `playing` más viejas que el umbral que este proceso no reporta
  vivas (`Live.sessions`). Es idempotente: el segundo barrido no encuentra nada.
- **Errores**: `{"error": {"code", "message"}}` con la tabla de `docs/api.md`; no se inventan
  códigos ni se reusan con otro significado.
- **Sin logs del token**: viaja en la URL del WS; no se loguea.

## Persistencia de sesiones

`app/services/sessions.py` es el único módulo que escribe las cuatro tablas de una
sesión:

- `start_session` deja la fila `playing` y sus sillas en el arranque.
- `finish_session` proyecta el resumen del motor y guarda ítems e intentos en **una**
  transacción. Si la fila ya no está `playing`, el cierre es un no-op: el primero gana
  y repetirlo no duplica historial.
- `abandon_session` e `invalidate_session` cierran sin historial (abandono y barrido).

El servicio no lee relojes: `started_at`, `ended_at` y los veredictos llegan ya
decididos por el motor o el barrido. Los intentos apuntan a los ítems por `item_key`;
el id de la fila lo genera el servicio.

El arcade escribe acá desde la fase 4.2: `arcade_ws` arranca la sesión con
`mode='trivia_arcade'`, `play_format='arcade'`, `config={}` (las reglas fijas de
`ruleset_version=1`) y la cierra con los ítems y los intentos del `SoloEngine`.
`arcade_runs`/`arcade_answers` ya no reciben escrituras del camino en vivo.

## Sesiones en vivo

`app/runtime/session_store.py` es el estado vivo de las sesiones solo: el contrato
`SessionStore` (`open`, `submit`, `close`, `live`, `sessions`) y su implementación
`InMemorySessionStore`. El handler dependerá de la interfaz, no de la clase, para poder
mudarla a Redis cuando haya más de un proceso.

- `open` registra la sesión, manda `arcade_start` y sirve el primer ítem. El borde
  inyecta las `SoloRules`, el `ItemSource` (elegir y cargar es I/O), el reloj, el
  `sleep` y el `rng`; el store solo aplica el `SoloEngine` y entrega.
- Cada sesión tiene un `outbox` propio. Si el cliente deja de leer y la cola se llena,
  se descarta lo más viejo y se conserva lo último (mismo criterio que la sala).
- La tarea de vencimiento resuelve la ronda servida al llegar `ends_at` y sirve la
  siguiente después de la pausa de revelación.
- `close(session_id)` es idempotente y corta la tarea. La fila no se toca: si quedó
  `playing`, el barrendero la invalida.
- `live()` alimenta `Live.sessions`; una sesión terminada deja de estar viva aunque su
  `close` llegue después.
- `on_finish` es el cierre del borde: el store lo espera **antes** de entregar el
  `arcade_end`, para que el cliente vea la posición ya calculada. Si el borde falla,
  devuelve el final con las posiciones en `None` y la fila queda para el barrendero.

El store no persiste: `services/sessions.py` sigue siendo el único que escribe las
cuatro tablas, y el borde es quien llama al arranque y al cierre. `arcade_ws` es ese
borde: elige y carga los ítems (`ItemSource`), arranca la fila, persiste el cierre y
completa el ranking con `leaderboard.run_summary` (que desde 4.2 lee `game_sessions`).

## Convenciones

- Código, identificadores, archivos y commits **en inglés**; los mensajes que ve el jugador,
  en español.
- Comentarios solo para el **porqué** no obvio. Nada que repita lo que el código ya dice.
- Un cambio de contrato sin `docs/api.md` actualizado no está terminado.
- Consistencia con lo que ya existe en `backend/` por encima de gustos personales.
