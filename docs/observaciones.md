# Observaciones — auditoría del backend

> Auditoría hecha leyendo el repositorio completo (todo `backend/app`, `backend/tests`,
> las 3 migraciones, `docker-compose.yml`, `Makefile`, `pyproject.toml` y `docs/plan.md`)
> el 2026-10-17. Cada hallazgo trae **evidencia** (archivo:línea), **impacto**,
> **cómo se reproduce** y **cómo se arregla**. Los marcados 🔬 los reproduje
> ejecutando código, no leyéndolo.
>
> No es una lista de deseos: es lo que yo tocaría, en este orden, antes de escribir
> una línea del arcade.

> **Estado (2026-10-17, tarde).** Resueltos y verificados: **H-01, H-02** (los dos
> P0), **H-03, H-04, H-05, H-06** (P1), el `players` de `GET /rooms/{code}` y el
> **barrendero**. Van marcados con ✅ en su título; el resto sigue vigente tal como
> está escrito. El detalle de cada arreglo quedó en `docs/plan.md` (sección *Estado
> de sesión*).

---

## 0. Veredicto en cinco renglones

El proyecto está **muy bien construido para tener 2 días de vida**: capas limpias,
motor puro, constraints de verdad en Postgres, 419 tests que corren en ~10 segundos y
comentarios que explican el *porqué* y no el *qué*. El modo online —lo único
jugable hoy— tenía **dos defectos serios de ciclo de vida**: una reconexión podía
hacerte **perder la partida por un socket viejo**, y **cualquier error de base mataba
el reloj de la sala para siempre**. Los dos eran silenciosos, los dos eran la parte
"en vivo" del juego, y los dos se arreglaron con cambios chicos y bien acotados
(H-01 y H-02, abajo).

Y ojo con esto, que no es de código: **la respuesta correcta está en la opción B en
48% de las 60 preguntas y en D en 1,7%**. Como las opciones no se mezclan al servir,
"tocar siempre B" acierta casi la mitad. Es un problema de juego, no de software,
y aparece el primer día que alguien lo note.

---

## 1. Cómo se auditó (y qué salió)

Comandos y resultado exacto, para que sea verificable:

| Verificación | Comando | Resultado |
|---|---|---|
| Lint | `uv run ruff check .` | `All checks passed!` |
| Formato | `uv run ruff format --check .` | `78 files already formatted` |
| Tipos | `uv run mypy app` | `Success: no issues found in 47 source files` |
| Schema | `uv run alembic check` | `No new upgrade operations detected.` |
| Tests | `uv run pytest -q` | **419 passed in ~10 s**, 95 warnings (la auditoría corrió con 408; los arreglos sumaron 11) |

Los 93 warnings son todos el mismo: `InsecureKeyLengthWarning`, el `JWT_SECRET` de
dev mide 18 bytes. Está anotado en el plan y es correcto anotarlo, pero mientras
siga, cualquier warning nuevo se pierde en el ruido (ver **H-21**).

**Método.** Leí línea por línea `runtime/`, `ws/`, `api/`, `services/`, `models/`,
`game/`, `security/`, `alembic/` y los tests. Para los hallazgos de concurrencia no
me confié del razonamiento: escribí el test que falla (H-01) y el script ASGI que
prueba el orden de las cosas (H-05). Los borré después de confirmar; el informe
trae el código para volver a reproducirlos.

---

## 2. Cuánto falta para el MVP

### 2.1 Tabla por área (backend + infra local)

El peso es mi juicio sobre cuánto del MVP depende de cada área, no una medida
objetiva. El "%" es contra el backend terminado (el frontend no cuenta acá).

| Área | Estado | % | Qué falta |
|---|---|---|---|
| Capa de datos (7 tablas, 3 migraciones, guardia de schema) | completa y verificada | **100** | nada |
| Motores puros (`match_engine`, `arcade_engine`, `scoring`, `answers`) | completos, con invariantes | **100** | nada |
| Banco de preguntas + importador + semilla | completo | **95** | curación/admin de preguntas |
| API HTTP de sesión (`/auth/guest`, `/me`) | completa | **95** | `GET /me` con mejor marca y últimas partidas (Fase 4) |
| API HTTP de salas | completa | **100** | nada (vista previa con `players`) |
| WS de sala | completo | **95** | robustez de ciclo de vida verificada (H-01, H-02 resueltos) |
| Persistencia de partidas (`matches`/`match_rounds`) | completa | **70** | arcade sin persistir (no existe) |
| API HTTP de ranking (`/leaderboard/arcade`, `/me`) | no existe | **0** | endpoints + consulta §14 |
| API HTTP de admin (listado + import) | no existe | **0** | 2 endpoints y el `X-Admin-Token` |
| WS de arcade | no existe | **0** | `ws/arcade_ws.py` + persistencia de la corrida |
| Barrendero (salas vencidas, matches colgados) | completo (al arrancar) | **100** | barrido periódico (opcional) |
| Redis (ranking, rate limit, Pub/Sub) | solo historial de vistas | **15** | sorted sets, límites, multi-instancia |
| Concurrencia / ciclo de vida de sala | camino feliz, P0 y fugas corregidos | **90** | H-07 (multi-instancia) |
| Infra local (compose, Makefile, env) | completa | **70** | `README.md`, CI |
| Tests | 419 verdes, sin cobertura medida; tests de carrera para H-01/H-02 y del barrendero | **80** | cobertura, CI |
| Frontend | **fuera de alcance de este repo** | — | lo hace otra persona |

**Backend ponderado: ≈ 60 %** al cerrar la auditoría. Los arreglos de esta tarde
(H-01, H-02, H-05, H-06 y `players`) suben la calidad del camino online, pero mueven
poco el porcentaje: lo que falta es **ancho** (arcade, ranking, admin, barrendero),
no profundidad.
Si se cuenta el **producto entero** —backend + frontend + CI + e2e + PWA + deploy—
estamos en **≈ 35 %**, porque el frontend hoy es 0 % y la mitad de la "definición de
terminado" (§20 del plan) es de cara al usuario.

### 2.2 Contra la definición de terminado del MVP (§20)

| # | Criterio | Estado |
|---|---|---|
| 1 | Dos personas juegan 1v1 completo entrando por código | backend ✅ (falta frontend) |
| 2 | Empate/desempate, revancha, gracia de 20 s | ✅ (gracia corregida: H-01) |
| 3 | Arcade con dificultad/tiempo/3 vidas y ranking global y semanal | 35 % (motor ✅, WS y ranking ❌) |
| 4 | El cliente no conoce la respuesta antes de contestar; puntajes en el servidor | ✅ (garantizado por el *tipo*, ver 8.1) |
| 5 | ≥ 60 preguntas de las 6 categorías | ✅ 60/60, 10 por categoría |
| 6 | CI verde incluidas las e2e | ❌ no hay CI |
| 7 | UI sin gradientes/emojis, SVG propios | frontend |
| 8 | Levantar el proyecto en ≤ 5 comandos documentados | ❌ no hay `README.md` |

Cumplidos a nivel backend: **3,5 de 6** (el 1 y el 3 esperan al frontend/arcade).

---

## 3. Datos del repositorio

| Métrica | Valor | Comentario |
|---|---|---|
| Commits | 30, en **2 días** (16–17 oct 2026) | ritmo altísimo, un commit = un paso testeado |
| LOC `app/` | 3.994 en 47 módulos (mypy) | razonable para el alcance |
| LOC `tests/` | 5.006 | **ratio test:código 1,25:1** — excelente |
| Tests | 419, ~10 s, contra Postgres y Redis reales | sin SQLite, sin mocks de base |
| Tablas | 7 (users, questions, rooms, matches, match_rounds, arcade_runs, arcade_answers) | 1:1 con §8 del plan |
| Migraciones | 3 (`0001`–`0003`), **sin drift** | `alembic check` limpio |
| Dependencias | 12 runtime + 5 dev | 2 son código muerto (H-16) |
| Semilla | 60 preguntas, 10 por categoría | sesgo de posición (H-25) |
| Plan | `docs/plan.md`, 1.357 líneas | documento único, como se acordó |
| CI / README / cobertura | 0 / 0 / no se mide | los tres agujeros de calidad |
| Warnings | 93 (100 % idénticos, PyJWT key length) | ver H-21 |

Lectura rápida: **la base es sólida y la verificación también; lo que falta es
ancho, no profundidad**. Lo que hay está bien hecho y lo que no está, no está
empezado — eso es mejor que lo contrario.

---

## 4. Hallazgos P0 — correctitud del modo online

### 🔬 H-01 — ✅ RESUELTO. Reconectar te puede hacer **perder la partida**: el cierre del socket viejo pisa la conexión nueva

**Síntoma.** Un jugador se queda sin red (no hay FIN), el cliente reconecta antes de
que el servidor lo note, entra bien… y 20 segundos después la partida se abandona
**en su contra**, con el socket nuevo todavía conectado.

**Por qué pasa.** `join` y `disconnect` del `RoomStore` no dicen de qué conexión
hablan; la identidad del jugador es la única llave.

- `room_manager.py:164-178` — `join` **pisa** la cola: `entry.outboxes[user_id] = outbox`.
- `room_manager.py:208-224` — `disconnect` sólo recibe `code` y `user_id`.
- `room_ws.py:112-117` — el `finally` del handler viejo llama
  `store.disconnect(code, user_id)` sin más contexto.

Secuencia real (y es *el* camino que atiende el timeout de inactividad, no un caso
raro): el socket viejo no terminó, su lector sigue esperando hasta los 45 s de
`ws_idle_timeout_seconds`; mientras tanto el cliente ya reconectó y se sentó. A los
45 s el handler viejo pasa por su `finally` y marca la silla como desconectada:
abre una gracia falsa y, cuando vence, `room.expire` ve `gone=[Player.B]` y llama
`_abandon`, que le da la partida al rival.

**Reproducción (confirmada).** Test contra Postgres real, con el harness existente:

```python
# 1) el jugador reconecta con socket nuevo (el server todavía no notó el corte)
nuevo = Outbox()
await h.store.join(code=fila.code, user_id=str(beto.id), nick="beto", outbox=nuevo)
assert h.store.player_count(fila.code) == 2

# 2) recién ahora se desmonta el socket viejo
await h.store.disconnect(code=fila.code, user_id=str(beto.id))
# -> player_count pasa a 1 aunque beto sigue conectado

# 3) corre la gracia
await correr(h, 20_000)
# -> MatchEnd(winner='you', reason='abandoned')  ← partida perdida por el jugador conectado
```

Salida textual del run: `player_count tras el disconnect viejo: 1`,
`MatchEnd recibido: [MatchEnd(winner='you', scores=Scores(you=0, opponent=0), rounds=[], reason='abandoned')]`.

**Impacto.** Alto. Rompe el criterio 2 de §20 y el único camino de reconexión que
promete el plan (§9.2). Es una **pérdida de partida injusta**: lo peor que puede
hacer un juego online.

**Arreglo recomendado (mínimo y sin tocar la máquina de estados).** Que el cierre
declare *su* cola y el store ignore el cierre si esa cola ya no es la vigente:

```python
# room_manager.py — RoomStore
async def disconnect(self, *, code: str, user_id: str, outbox: Outbox) -> None: ...
```

```python
# room_manager.py — InMemoryRoomStore.disconnect
async with entry.lock:
    if entry.outboxes.get(user_id) is not outbox:
        # Otra conexión más nueva ya se sentó: este cierre es de un socket viejo.
        return
    entry.outboxes.pop(user_id, None)
    await self._step(...)
```

```python
# room_ws.py — finally
await store.disconnect(code=codigo, user_id=user_id, outbox=outbox)
```

`Outbox` ya es único por conexión (`asyncio.Queue` nueva en `room_ws.py:81`), así que
la comparación por identidad es exacta y no hace falta un contador de generación.

**Test que lo fija.** El de arriba, pero afirmando lo correcto:
`player_count == 2` y `MatchEnd` ausente. Aislado, sin reloj real.

**✅ Implementado (2026-10-17).** `RoomStore.disconnect` recibe el `outbox` de la
conexión; `InMemoryRoomStore` ignora el cierre si `entry.outboxes[user_id] is not
outbox`; el `finally` del handler pasa su cola. Test:
`test_the_old_socket_closing_late_does_not_abandon_the_reconnected_player`
(saboteado: sin el guard, `player_count` baja a 1).

---

### 🔬 H-02 — ✅ RESUELTO. Un error de base mata el reloj de la sala **para siempre** (y en silencio)

**Síntoma.** Una excepción transitoria (una conexión del pool caída, un deadlock,
un `IntegrityError` al cerrar la partida) y la sala se queda sin vencimientos **hasta
que se reinicie el proceso**. La ronda servida ya no la cierra el reloj: si nadie
contesta, la partida cuelga.

**Por qué pasa.** `room_manager.py:402-433`: la tarea de vencimientos es un
`while True` envuelto en un `try/except Exception` que **loguea y retorna**.

```python
except Exception:
    logger.exception("la sala %s quedó sin vencimientos", entry.state.code)
    # ← la corrutina termina acá; nadie la vuelve a crear
```

El `except` atrapa tanto errores transitorios como bugs propios
(`InvalidTransition` de `room.serve`), y el barrendero —la red de seguridad que el
propio plan declara— **todavía no existe** (`docs/plan.md`: “Próximos pasos”). O
sea: hoy no hay ninguna red.

**Impacto.** Alto. Fallo silencioso de liveness en el corazón del modo online. El
estado en memoria vuelve atrás correctamente (`_step` lo hace bien, `room_manager.py:279-281`),
así que **reintentar es seguro**: es cuestión de no rendirse.

**Arreglo recomendado.** No morir; reintentar con backoff y avisar:

```python
fallos = 0
while True:
    try:
        ...cuerpo actual...
        fallos = 0
    except asyncio.CancelledError:
        raise
    except Exception:
        fallos += 1
        logger.exception("la sala %s falló al vencer (intento %d)", entry.state.code, fallos)
        if fallos >= MAX_FALLOS:            # p.ej. 5
            await _deliver(entry, _error_to_seats(entry.state, "ROOM_CLOCK_DOWN",
                "La sala perdió el reloj. Se corta la partida."))
            return
        await self._sleep(BACKOFF_S)        # p.ej. 1 s, inyectado como el resto
```

Dos decisiones que importan:
1. **Avisar a los clientes** antes de rendirse (`_error_to_seats` ya existe): una sala
   sin reloj tiene que cortar, no quedarse muda.
2. **No reintentar infinito**: 5 intentos y se rinde, porque si la base está caída,
   el reloj girando en vacío empeora el problema. Es el criterio que el propio
   comentario del código ya elige — sólo hay que agregar el reintento antes.

**Test que lo fija.** Un `session_factory` que falla **una** vez y después anda:
el vencimiento ocurre igual y la sala sigue viva.

**✅ Implementado (2026-10-17).** `_expiry_loop` reintenta con backoff
(`MAX_EXPIRY_FAILURES = 5`, `EXPIRY_BACKOFF_S = 1.0`, inyectables) y, agotado,
`_surrender` entrega `ROOM_CLOCK_DOWN`. La vuelta del reloj se aisló en `_tick`, y
`retry_serve` cubre el fallo al cargar la **próxima pregunta** (si no, la sala
quedaría debiendo la ronda sin plazo). Tres tests con `session_factory` que falla a
pedido; sabotajes: volver a "morir" rompe los tres, quitar `retry_serve` rompe uno.

---

## 5. Hallazgos P1 — serios

### H-03 — ✅ RESUELTO. Las salas vivas nunca se liberan (fuga de memoria por código)

`InMemoryRoomStore._rooms` (`room_manager.py:150`) sólo se limpia entero en
`close()` (`:246-251`), que corre al apagar el proceso. No hay desalojo en régimen:
cada sala abierta por un WS queda en el diccionario **para toda la vida del proceso**,
con su `RoomState`, sus `outboxes` y su tarea.

**Impacto.** Medio-alto según uso: un servidor de horas pierde memoria proporcional a
las salas creadas, aunque estén muertas hace rato.

**Arreglo.** Desalojar cuando la sala no puede revivir: `status is WAITING`,
`match is None` y ninguna silla conectada — cancelando su tarea — con un pequeño
retardo para no matar una sala que está en plena reconexión. Alternativa más simple
y más honesta: un TTL (`last_activity_ms` en `_Room`) que el `_expiry_loop` usa como
deadline adicional. En condiciones normales el barrendero de salas (§próximos pasos)
es el lugar natural de esto.

**✅ Implementado (2026-10-17).** Se tomó el TTL, pero **sin tocar el reloj**: `_Room`
guarda `last_activity_ms` (se actualiza en cada transición) y `RoomStore.open`
desaloja, antes de crear una sala, las que no tienen `outbox`, no están `playing` y
llevan más de `ROOM_IDLE_TIMEOUT_SECONDS` inactivas. Como el mapa crece con las
altas, una barrida por alta lo mantiene acotado. Test:
`test_a_dead_room_is_evicted_when_another_one_opens` (saboteado: sin desalojo,
`room_count` queda en 2).

### H-04 — ✅ RESUELTO. `rooms.expires_at` no se refresca: el barrendero que viene puede matar partidas vivas

`expires_at` se calcula **una sola vez** al crear la sala (`services/rooms.py:34-35`:
`now + room_idle_timeout_seconds`, 600 s). Nunca se extiende.

Una partida de 7 rondas × 30 s son 210 s, pero **el desempate no tiene tope** (H-24)
y el **rematch arranca otra partida completa**, y otra. Dos jugadores enganchados
cruzando los 10 minutos **tienen `expires_at` en el pasado**.

Hoy no pasa nada porque el barrendero no existe. El día que exista (es el próximo
paso de la cola) el riesgo es concreto: si el barrido es
`WHERE expires_at < now() → status='expired'`, **mata partidas en curso**.

**Arreglo.**
1. El barrendero filtra `AND status = 'waiting'` (el índice `(status, expires_at)`
   ya está pensado para eso, `models/match.py:90`).
2. Extender `expires_at` cuando la partida arranca y en cada revancha
   (`_write_match`, `room_manager.py:365-380`), o directamente pasar `expires_at` a
   `now() + techo_de_partida`.
3. De paso: la vista previa deja de mentir (`api/routers/rooms.py:35` devuelve un
   `expires_at` que ya no representa nada).

**✅ Implementado (2026-10-17).** El barrendero (`services/reaper.py`) filtra
`status='waiting'` y, además, `rooms.status` se sincroniza con la vida de la sala
(hasta hoy la fila se quedaba en `waiting` para siempre): `playing` al arrancar y en
cada revancha, `finished` al cerrar, `waiting` cuando se va alguien de una sala
terminada. Al arrancar la partida `expires_at` pasa a
`now + rounds × (seconds + gracia) + 60 s`, así la vista previa tampoco miente.
Tests: `test_the_room_row_follows_the_match_lifecycle` y el barrido con una sala
`playing` de fecha vieja, los dos saboteados.

### 🔬 H-05 — ✅ RESUELTO. El commit corre **después** de que el cliente recibe la respuesta

El plan lo dice así: *"el borde del pedido es el borde de la transacción"*
(`api/deps.py:20-22`). **No es lo que pasa.**

Lo medí con la versión instalada (FastAPI 0.143.3). En
`.venv/.../fastapi/routing.py:148-155`:

```python
async with AsyncExitStack() as request_stack:      # ← acá vive get_session
    ...
    response = await f(request)
    await response(scope, receive, send)           # ← la respuesta ya salió
# al salir del stack recién corre el `await session.commit()` del dependency
```

Script ASGI mínimo que lo prueba: el cuerpo de la respuesta se emite **antes** de que
corra el código posterior al `yield`.

```
mensajes ASGI enviados antes de la excepción: ['http.response.start', 'http.response.body']
¿el cuerpo ya salió?: True
orden de eventos: ['commit']
```

**Impacto.** Un `commit` que falla (constraint diferido, conexión que se corta entre
el flush y el commit) **ya devolvió 201/200 con datos que nunca se guardaron**. El
cliente cree que creó la sala; el WS después contesta `ROOM_NOT_FOUND`. Es raro, pero
es exactamente el tipo de bug que se busca durante horas porque el log no lo
relaciona con nada.

**Arreglo.** Dos caminos, elegir uno y escribirlo en el plan:
- **(a) Simple y explícito**: que los endpoints de escritura hagan
  `await session.commit()` ellos (`POST /auth/guest`, `POST /rooms`, `PATCH /me`,
  `DELETE /me`) y `get_session` quede para lectura. Es el patrón que ya usa la CLI
  (`cli.py:52-56`) y el `room_manager`: **el que sabe que escribió, commitea**.
- **(b) Ideal pero más trabajo**: un middleware que envuelva la respuesta y cierre la
  transacción antes de emitirla.

Recomiendo **(a)** ahora (4 líneas) y (b) el día que haya más de una docena de
endpoints de escritura.

**✅ Implementado (2026-10-17).** Se tomó **(a)**: `/auth/guest` (solo el alta),
`POST /rooms`, `PATCH /me` y `DELETE /me` hacen `await session.commit()` antes de
responder. `get_session` queda como red de seguridad y su docstring ya dice la
verdad. No se agregó un test artificial: en el harness la fila se ve por el `flush`
aunque falte el commit; el arreglo es estructural.

### H-06 — ✅ RESUELTO. Después de una partida terminada, el host arranca otra **salteando la revancha**

`room.start` (`runtime/room.py:162-173`) sólo rechaza `status is PLAYING`. Con la
sala en `FINISHED`, la validación pasa, `_new_match` corre y **el invitado recibe un
`match_start` sin haber apretado revancha**.

Tenés entonces dos caminos para lo mismo: el acuerdo de revancha
(`room.rematch`, `:323-340`, el que se arregló hace dos commits) y este atajo que lo
esquiva, con la misma escritura de fila (`_persist`, `room_manager.py:349-363`).

**Impacto.** Bajo en daño, alto en confusión: dos verdades para el mismo estado, y la
que gana es la que menos piensa. Si la revancha requiere acuerdo, `start` debe
rechazar `FINISHED`.

**Arreglo.** `if state.status is not RoomStatus.WAITING: → ALREADY_PLAYING`
(o un código nuevo `NOT_WAITING`). Nótese que `disconnect` ya devuelve la sala a
`WAITING` (`room.py:272-283`), así que el flujo "se fue uno, entra otro, arrancamos"
sigue funcionando.

**✅ Implementado (2026-10-17).** `start` rechaza todo lo que no sea `WAITING` con
`ALREADY_PLAYING`. Test: `test_start_is_rejected_after_the_match_finished`
(saboteado: con el chequeo viejo, el `start` sobre `finished` arrancaba otra partida).

### H-07. Nada impide arrancar con dos workers y partir la verdad en dos

Todo el estado vivo es de proceso (`room_store`, `room_manager.py:519-522`; el mismo
patrón que `engine` y `redis_client`). Es una decisión consciente y está documentada
(`room_manager.py:128-134`), pero **no está defendida**: `uvicorn --workers 2` —o
cualquier plataforma que escale— levanta sin chistar y produce dos salas distintas
con el mismo código, cada una con la mitad de los jugadores.

**Arreglo barato.** Un guard en el `lifespan`
(`main.py:15-22`): si `settings.env != "local"` y el store es el en memoria, loguear
en `error` una advertencia explícita de una sola instancia —o negarse a arrancar—.
Es la misma idea que la validación de `JWT_SECRET` pendiente: **los invariantes de
despliegue también se declaran**.

---

## 6. Hallazgos P2 — seguridad, observabilidad, escala

### H-08. El token viaja en el query string y termina en los logs

`ws/room_ws.py:121` lee `?token=`. No es una decisión cuestionable —el navegador no
deja mandar headers en `new WebSocket`— pero **uvicorn loguea la URL completa**, así
que cada conexión escribe el JWT (válido 30 días) en el access log.

**Arreglo.** Lo más simple: subprotocolo (`new WebSocket(url, ["bearer", token])`), o
un ticket de un solo uso por HTTP antes de abrir el socket. Mientras tanto: filtro de
access log para `/ws/`. Y hoy es peor de lo que parece, porque **no hay logging
configurado** (H-12): el día que se prenda, se prende esto también.

### H-09. No hay rate limiting, aunque §5 del plan lo promete

`POST /auth/guest` crea usuarios sin tope (invitados ilimitados en la base);
`GET /rooms/{code}` y `WS /ws/room/{code}` permiten **fuerza bruta de códigos**
(32⁶ ≈ 1.000 millones, pero el alfabeto sacó los ambiguos y el código es corto).
El plan lista "rate limiting" en Redis: no está.

**Arreglo.** Un contador por IP+ventana en Redis en `/auth/guest` y en el fallo de
`ROOM_NOT_FOUND`. No necesita ser elegante.

### H-10. `GET /rooms/{code}` sin autenticación, y sin filtrar salas vencidas

`api/routers/rooms.py:23-36` devuelve `host_nick` a cualquiera que acierte el código.
Y ni acá ni en `room_ws._load_room` (`:127-132`) se mira `status`/`expires_at`: se
puede abrir el WS de una sala ya `expired` y el store la revive en memoria.
Es parte del mismo agujero de H-04.

### H-11. La barra de calidad está en el mínimo por defecto

- **mypy sin configuración**: no hay `[tool.mypy]` en `pyproject.toml` (sólo está
  listado como dependencia, línea 26). "Success: no issues" con mypy por defecto no
  dice casi nada: `--strict` es otro programa.
- **ruff sin `select`**: sólo `E`/`F` por defecto (flake8 base). No hay bugbear
  (`B`), simplificaciones (`SIM`), `ASYNC` (crítico acá), upgrades (`UP`) ni bandit
  (`S`) — y este código maneja tokens, paths y SQL.
- **Cobertura**: no se mide; no hay `pytest-cov`. Con ratio 1,25:1 de tests yo
  esperaría 85 %+, pero eso hay que **medirlo**, no suponerlo.
- **CI**: no existe (`.github` no está). El plan lo pone en Fase 0.

**Arreglo (una hora, retorno altísimo):**

```toml
[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "SIM", "ASYNC", "RUF", "PT"]

[tool.mypy]
strict = true

[tool.pytest.ini_options]
addopts = "--cov=app --cov-report=term-missing --cov-fail-under=85"
filterwarnings = ["ignore::jwt.warnings.InsecureKeyLengthWarning"]
```

(y un workflow que corra `make lint && make test && make check-schema`, con Postgres
y Redis como *services*). Empezar por `ASYNC` y `B`, que son los que hubieran
encontrado cosas de esta clase.

### H-12. Sin configuración de logging, el tiempo real es ciego

`room_ws.py:151` loguea `logger.info("la sala %s cortó a %s por inactividad")`,
`room_manager.py:333` y `:388` loguean `warning`, y `:433` un `exception`. **Nada de
eso se ve**: no hay `logging.basicConfig`/`dictConfig` en `main.py` ni en el arranque.
El nivel efectivo queda en `WARNING` del root y la mitad de la observabilidad del
modo online no existe.

**Arreglo.** Configurar logging en `main.py` (o un `logging.yaml` leído en el
lifespan) con formato que incluya hora y logger. Es la contraparte barata de H-02:
si el reloj de una sala se muere, quiero verlo.

### H-13. Outbox sin tope y banco de preguntas completo en cada ronda

- El `outbox` es un `asyncio.Queue` **ilimitado** (`room_ws.py:81`) y el escritor
  puede quedar bloqueado en `send_json` por un cliente que no lee (backpressure de
  TCP). Los productores siguen `put` y nadie los frena. Con pocos mensajes por
  partida es teórico; conviene un tope (`maxsize=64`) y cerrar la conexión si se
  llena, que es el comportamiento correcto.
- `question_bank.candidates()` (`:61-76`) trae **todas** las publicadas y filtra en
  memoria, **en cada ronda y por sala** (`room_manager._pick`, `:326-331`). Está
  anotado como riesgo de escala y es correcto con 60 preguntas. Con 10.000 preguntas
  y 50 salas concurrentes son ~500.000 filas por ronda. El arreglo natural: mover el
  filtro de dificultad a la consulta (`WHERE difficulty BETWEEN :low AND :high`) y
  usar `ORDER BY random() LIMIT 1`, o materializar el pool por tramo.

### H-14. El 422 pierde `loc`: el frontend no sabe qué campo falló

`api/errors.py:36` arma el mensaje con `"; ".join(error["msg"])`. Sin `loc`, "Input
should be a valid integer" no dice de qué campo. Es gratis incluirlo:

```python
detalle = "; ".join(f"{'.'.join(str(p) for p in e['loc'][1:])}: {e['msg']}" for e in exc.errors())
```

### H-15. Sin límites de tamaño en tres bordes

- `schemas/auth.py:9`: `nick: str | None` sin `max_length` → un cuerpo de 10 MB se
  parsea y después se rechaza. Poner `max_length` en el schema (defensa en el borde,
  no sólo en `clean_nick`).
- No hay límite de tamaño de cuerpo global: un middleware simple o el límite de
  uvicorn.
- `importer._insert` (`:283-309`) arma **un INSERT con todas las filas** y lee el
  archivo entero a memoria. Un CSV de 100.000 filas = sentencia gigante. Cortar en
  lotes de ~500.

---

## 7. Hallazgos P3 — menores, pero deuda real

| # | Hallazgo | Evidencia | Arreglo |
|---|---|---|---|
| H-16 | Dependencias y config muertas: `orjson` y `python-multipart` declaradas y **nunca usadas**; `admin_token` en `Settings` sin ningún consumidor | `pyproject.toml:8-19`, `config.py:13`, `grep` sin resultados | borrar `orjson`/`python-multipart`; dejar `admin_token` sólo si se hace el admin ya (si no, también sale y vuelve con el endpoint) |
| H-17 | El lookup de sala está **tres veces**: `rooms.py:25-28`, `room_ws.py:127-132` y el `Room(...)` de creación | ídem | un `services/rooms.get_by_code(session, code)` que normaliza y valida; los dos bordes lo usan |
| H-18 | `GET /` devuelve un texto improvisado con typo ("Prueba que de que el metodo GET...") | `main.py:46-52` | borrar la ruta o devolver `{name, version}` en serio |
| H-19 | `/health` responde **200 degradado** (db/redis en `error`) | `routers/health.py:28` | 503 si algo está mal; si no, ningún balanceador va a reaccionar |
| H-20 | Mezcla de idiomas: handlers `crear_sala`/`vista_previa` en español, el resto en inglés | `rooms.py:16,24` | §15 del plan dice código en inglés; renombrar |
| H-21 | 93 warnings idénticos tapan cualquier warning nuevo | `pytest` output | `JWT_SECRET` de dev a ≥ 32 bytes en `.env.example`; y `filterwarnings` para el caso de test |
| ✅ H-22 | Drift de docs: el plan y `.env.example` quedaron al día (419 tests, ~10 s; `WS_IDLE_TIMEOUT_SECONDS` y `STALE_MATCH_MINUTES` listados) | `plan.md:16`, `.env.example` | mantener los números al día en el mismo paso |
| H-23 | `GET /me` hace un `flush` por lectura (pisa `last_seen_at`) | `routers/me.py:19-20` | correcto, pero es una escritura por cada GET; si el frontend lo llama seguido, conviene un `UPDATE ... WHERE last_seen_at < now() - interval '1 minute'` |
| H-24 | **El desempate no tiene tope**: si los dos siguen empatando, la partida no termina nunca (cada ronda de desempate es de `seconds//2` y suma más rondas) | `match_engine.py:207-217`, `:109-114` | un máximo de rondas de desempate (p.ej. 3) y, agotado, gana quien tenga mejor tiempo acumulado o se declara empate |
| H-25 | **Sesgo de posición en la semilla**: correcta en B 48,3 %, C 28,3 %, A 21,7 %, D 1,7 % (n=60). Y las opciones **no se mezclan al servir** (`room.py:429`, `list(question.question.options)`) | `seeds/questions.csv` | (a) barajar opciones al servir, recalculando `correct_index` en el servidor —arregla el problema para siempre y también el banco futuro—; (b) rebalancear la semilla |

H-25 merece un comentario aparte porque **no es un bug de software y es el que más
rápido se va a notar jugando**: "toco siempre la segunda" acierta casi la mitad.
Barajar al servir es una función pura de 5 líneas en el motor (o en `LoadedQuestion`)
y elimina la clase entera de problemas.

---

## 8. Lo que está muy bien (y conviene no romper)

Un informe que sólo lista defectos miente por omisión. Estas decisiones son de
senior y son las que hacen que el resto sea barato de arreglar:

1. **El motor es puro y el borde es sucio a propósito.** `game/` no conoce Postgres,
   ni sockets, ni `time.time()`. `now_ms`, `sleep` y `rng` se inyectan
   (`room_manager.py:136-149`): una partida entera corre en milisegundos en los tests
   con el `FakeClock`. Esa decisión sola explica los 419 tests en ~10 s.
2. **La respuesta correcta no puede filtrarse: no está en el tipo.** `RoundQuestion`
   (`question_bank.py:39-50`) no tiene `correct_index`; el `match_end` con
   `RoundResult` es lo único que lo expone. Un test con `hasattr` lo vigila. Esto es
   la forma correcta de garantizar el criterio 4 de §20: **el compilador, no el
   reviewer**.
3. **Constraints reales, con nombre propio, verificados contra el catálogo.** El
   `naming_convention` (`models/base.py`), los `CHECK` derivados de las constantes
   del motor, `IS NOT DISTINCT FROM` para las claves ausentes de `jsonb`, el único
   parcial sobre `lower(nick)`… y encima la **guardia de schema** que aplica el DDL
   de los modelos en un schema descartable y compara el texto de Postgres contra el
   texto de Postgres. Eso es más de lo que hace la mayoría de los equipos pagos.
4. **Un solo escritor por socket, con lock compartido** (`room_ws.py:12-14, 223-226,
   259-271`). Dos `send` concurrentes sobre un WS no son seguros y acá eso está
   resuelto por diseño, no por suerte.
5. **La pausa que corre el reloj en vez de regalarlo** (`room._resume`, `:393-419`):
   al reconectar se desplazan el arranque **y las respuestas ya dadas** por el hueco.
   Es el detalle que separa una reconexión justa de una trampa.
6. **El `outbox` en vez de un callback** (`room_manager.py:20-21`): el vencimiento
   entrega sin que haya nadie esperando del otro lado. Es la decisión que hace que
   H-02 sea arreglable sin tocar nada más.
7. **Tests contra Postgres y Redis reales, sin SQLite, con aislamiento por savepoint**
   (`tests/conftest.py:7-12`), y un cliente WS propio en el mismo event loop
   (`tests/ws_client.py`) porque `TestClient` no cruza de loop. Nada de eso es
   estándar; es trabajo pensado.
8. **Los comentarios explican el porqué y las trampas** (`plan.md:49-108`): "un
   `CHECK` que evalúa a `NULL` no viola nada", "una migración que agrega una columna
   NOT NULL sin default falla a propósito". Es la clase de memoria que evita
   re-descubrir lo mismo dos veces.

El corolario: **los hallazgos P0/P1 de esta auditoría no son de arquitectura, son de
ciclo de vida**. La arquitectura está bien; lo que falta es cerrar los bordes que
nadie miró todavía porque el camino feliz pasa.

---

## 9. Concurrencia: el mapa completo

Como se pidió explícitamente, acá va el análisis de concurrencia de punta a punta.
El resumen: **el modelo es correcto** (un `asyncio.Lock` por sala, estado inmutable,
transiciones puras, un escritor por socket, reloj por tarea y `Event`) y los defectos
están en las **transiciones de ciclo de vida** de ese modelo, no en el modelo.

### 9.1 Lo que está bien y por qué

| Pieza | Mecanismo | Por qué es correcto |
|---|---|---|
| Exclusión por sala | `entry.lock` (`room_manager.py:120, 262`) | serializa transiciones y entrega; el estado no se puede leer a medias |
| Consistencia del estado | dataclasses `frozen` + `replace` (`room.py:52-99`) | no hay mutación compartida: o se ve el estado viejo entero o el nuevo entero |
| Estado vs. base | `_step` aplica, persiste, y **revierte el estado si la base falla** (`:274-281`) | nadie vio nada todavía: el rollback en memoria es coherente con el de Postgres |
| Escritura del socket | un solo drenador + `send_lock` (`room_ws.py:83, 223-271`) | dos `send` concurrentes en el mismo WS están prohibidos por el protocolo |
| Reloj | tarea por sala que duerme al próximo plazo y se despierta con `Event` (`:402-449`) | sin polling; el `clear()` antes de leer y el re-chequeo bajo el lock cubren la carrera despertar/tomar-lock |
| Cierre limpio | `close()` cancela y `gather` con `return_exceptions` (`:246-251`) | no quedan tareas colgadas al apagar |

### 9.2 Lo que falta cerrar

| # | Ruta de carrera | Consecuencia | Prioridad |
|---|---|---|---|
| H-01 | **cierre del socket viejo vs. `join` del nuevo** (confirmada) | pérdida de partida injusta | **P0 — ✅ resuelto** |
| H-02 | error en `_step` dentro del `_expiry_loop` | sala sin reloj para siempre | **P0 — ✅ resuelto** |
| H-03 | `_rooms` sin desalojo | fuga de memoria | P1 — ✅ resuelto |
| — | **`open()` sin lock**: `open` y el desalojo no tienen `await` en el medio → atómicos en el event loop, **pero sólo por eso**. Si alguna vez se agrega I/O ahí, hay que meterlo bajo un lock. | latente | P3 |
| — | **`_pick` + `_serve_next` toman el lock de la sala durante I/O de Postgres**: una base lenta bloquea la sala *y* su reloj. Con 60 preguntas y una instancia, irrelevante; con el banco grande, se soluciona eligiendo la pregunta **antes** de tomar el lock (el id ya se conoce) | latente | P3 |
| — | **hasta 2 sesiones de base por transición** (`_persist` y `_pick` abren la suya, `:326, 378, 385`): con pool por defecto (5+10) y muchas salas, agotamiento del pool | contención | P2 |
| — | **`outbox` ilimitado** (H-13) | memoria | P2 |
| — | **multi-worker / multi-instancia** (H-07) | dos verdades con el mismo código de sala | P1 |

### 9.3 Pruebas de concurrencia

Los tests son de **caminos de a uno**, con cuatro huecos dirigidos. Ya cerrados:

- ✅ un test que ejecuta el cierre del socket viejo **después** de la reconexión
  (el que cazó H-01): `test_the_old_socket_closing_late_does_not_abandon_the_reconnected_player`;
- ✅ tests que fuerzan un fallo de base dentro de una transición (H-02): los tres
  `test_the_clock_retries_*` con un `session_factory` que falla a pedido.

Faltan todavía:

- un test de dos `answer` simultáneos de la misma silla (idempotencia ya implementada
  en `room.answer:231-233`, pero sin prueba);
- un test de dos salas concurrentes compartiendo el `Random` inyectado.

No hace falta una suite de estrés: un par más de tests dirigidos con
`asyncio.gather` cubren lo que hoy no está cubierto.

---

## 10. Calidad de datos: lo que la base garantiza y lo que no

**Garantizado por la base (bien):** forma y valores de `config` en `rooms`/`matches`
(`IS NOT DISTINCT FROM`), coherencia `media_type`/`media_url`, `correct_index` en
0..3, longitud y `btrim` del enunciado, `content_hash` único en hexadecimal,
`options` con forma de array de 4 strings, `a_correct`/`a_choice`/`a_ms`/`a_rejected`
consistentes entre sí en `match_rounds` **y** `arcade_answers`, no negatividad de
puntajes, `longest_streak ≤ correct_count`, `ended_at ≥ started_at`, y el `status` de
la corrida atado a `ended_at`. Las FK tienen índice (Postgres no lo crea solo).

**No garantizado, a propósito o por olvido:**

| Hueco | Dónde | Riesgo |
|---|---|---|
| Opciones **no vacías ni repetidas**: sólo en Python (`services/importer.py:157-165`) y en el importador, no en la base | `questions.options` | una fila insertada a mano o por SQL pasa inválida; el `CHECK` cubre el tipo, no el contenido |
| `questions.language` sólo admite `'es'` | `models/question.py:68` | es una decisión, pero va a doler cuando entre el primer idioma nuevo (el día que pase, la migración es un `CHECK` a mano) |
| `matches` sin "una sola partida `playing` por sala" | `matches` | si el barrendero tarda, dos filas `playing` de la misma sala son posibles; el ranking no lo usa, así que es cosmético |
| Índice para "mis últimas partidas" | `matches` tiene `(player_a_id)`, `(player_b_id)`, `(status, started_at)` | la consulta del ranking 1v1 filtrará por dos columnas distintas; conviene `(player_a_id, started_at DESC)` y lo mismo para B (o un `UNION`) |
| **Sesgo de posición de la respuesta correcta** | semilla | ver H-25 |
| `arcade_*` sin usar | las 2 tablas están listas y no hay código que las escriba | correcto por ahora; es el próximo módulo |

**Sin `relationship()` en los modelos** es una decisión explícita y bien fundada
(evita cargas implícitas en async), pero tiene un costo anotado en el plan: el orden
de los INSERT los arregla el test a mano (`tests/factories.py`, `acepta()`). Cuando
el `room_manager` inserte filas relacionadas de verdad, va a chocar con lo mismo.
Vale la pena tenerlo presente y no "arreglarlo" con un `relationship()` apurado.

---

## 11. Plan de acción propuesto

Ordenado por **riesgo × costo**. Los cuatro primeros son el bloqueante del modo
online; nada de eso debería esperar al arcade.

| # | Acción | Por qué primero | Tamaño |
|---|---|---|---|
| ✅ 1 | **H-01** reconexión (colapsar `disconnect` con el `outbox` de la conexión) + el test de carrera | es pérdida de partida, y es el camino que atiende el timeout de inactividad | chico |
| ✅ 2 | **H-02** el reloj de la sala no muere: reintento con backoff, aviso a los clientes y rendición acotada + test | fallo silencioso de liveness sin red de seguridad (el barrendero no existe) | chico |
| ✅ 3 | `players` en `GET /rooms/{code}` con `room_store.player_count` | ya está en la cola del plan, es una línea, y cierra Fase 2 | trivial |
| ✅ 4 | **H-05** commit en los 4 endpoints de escritura (+ corregir el principio en el plan) | el principio documentado hoy es falso; 4 líneas y un test | chico |
| ✅ 5 | **H-04 + H-03 + barrendero**: `UPDATE ... WHERE status='waiting' AND expires_at < now()`, refresco de `expires_at` al arrancar y desalojo de salas muertas | el barrendero es el próximo paso y **hacerlo mal mata partidas vivas** | medio |
| ✅ 6 | **H-06** `start` sólo desde `WAITING` | dos verdades para el mismo estado | trivial |
| 7 | **H-11** `mypy strict`, `ruff select`, `pytest-cov`, CI | convierte a los puntos 1-6 en algo que no puede volver a pasar | chico |
| 8 | **H-12** logging + **H-08** sacar el token de los logs | sin logs, el punto 2 es invisible | chico |
| 9 | **H-25** barajar opciones al servir + rebalancear la semilla | es lo que más rápido se va a notar jugando, y es una función pura | chico |
| 10 | Fase 4: WS de arcade + persistencia + ranking + binario de Redis | el resto del MVP | grande |

Los puntos 1-6 ya están **hechos**. Siguen el 7 (**H-11**: `mypy strict`, `ruff`,
cobertura y CI) y el 8 (logging y token fuera de los logs).

---

## 12. Anexo — cómo volver a verificar todo esto

```bash
make up                      # Postgres 16 + Redis 7
cd backend
uv run ruff check . && uv run ruff format --check . && uv run mypy app
uv run alembic check         # sin drift entre modelos y migraciones
uv run pytest -q             # 419 verdes, ~10 s
```

Para H-01: `test_the_old_socket_closing_late_does_not_abandon_the_reconnected_player`
(reconectar con `Outbox` nuevo y después cerrar el viejo) — pasaba a fallar sin el guard.
Para H-05: el arreglo es estructural (los endpoints commitean antes de responder); se
verifica leyendo `routers/auth.py`, `routers/rooms.py` y `routers/me.py`.
Para el barrendero: `tests/test_reaper.py` (salas y partidas) más
`test_the_room_row_follows_the_match_lifecycle` y
`test_a_dead_room_is_evicted_when_another_one_opens` en `test_room_manager.py`.
Para H-25:

```bash
python3 - <<'PY'
import csv, collections
rows = list(csv.DictReader(open("backend/seeds/questions.csv", encoding="utf-8-sig")))
c = collections.Counter(r["correct"] for r in rows); n = len(rows)
print({k: f"{c[k]/n:.1%}" for k in "ABCD"})
PY
# {'A': '21.7%', 'B': '48.3%', 'C': '28.3%', 'D': '1.7%'}
```

---

## 13. Cierre

El proyecto va bien: **≈60 % del backend** y **≈35 % del producto**, con la mitad
difícil (datos, reglas, tiempo real del 1v1) hecha y verificada. Los problemas que
importaban no eran de arquitectura sino de **cierre de ciclos de vida**, y aparecían
justamente donde todavía no hay nadie mirando: el socket que se va tarde, el reloj
que se muere callado y lo que nadie cierra al apagar. Ya están corregidos, con sus
tests y sabotajes.

Lo que sigue, en orden: **H-11** (`mypy strict`, `ruff select`, cobertura y CI),
después **H-12 + H-08** (logging y token fuera de los access logs) y recién ahí el
arcade.
