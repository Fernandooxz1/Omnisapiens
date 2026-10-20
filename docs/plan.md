# Omnisapiens — plan del producto (frontend)

> Refactor multi-modo en curso: el diseño y el flujo diario viven en
> [`docs/plan-refactor/`](plan-refactor/README.md). Este archivo sigue siendo la
> especificación del producto; las reglas de juego no cambian por el refactor.

> Especificación viva del MVP. Es **estable**: la cola de trabajo vive en `docs/tareas.md`.
> El contrato técnico (WS, HTTP, auth, ranking, admin) está en `docs/api.md`; el sistema
> visual, en `docs/diseno.md`. Este archivo se consulta por sección (`grep`), no entero.

## Estado

El **backend está terminado** (HTTP, WS, salas, arcade, ranking, panel de admin, 553 tests,
cobertura 94 %) y no se toca. El **frontend cubre el MVP** en `frontend/` (SvelteKit +
TypeScript): inicio, creación y unión de salas, partida 1v1, arcade, ranking, panel de admin,
sonido, teclado, PWA instalable, suite e2e y tratamiento de errores (`+error.svelte`, `Toast`
con el código de la API y aviso de API caída). La página histórica de prueba (`frontend/dev/`)
ya no existe.

**La próxima tarea está en `docs/tareas.md`.** El detalle del backend quedó archivado en
`docs/archive/` (no se lee).

## Producto

**Dos modos.**

1. **Sala privada 1v1 por código:** dos jugadores, pregunta a la vez, ambos responden
   simultáneo, gana quien más puntos junta.
2. **Arcade:** un jugador solo, dificultad y tiempo progresivos hasta quedarse sin vidas;
   ranking global y semanal.

### Modos

No es lo mismo el contenido, el formato y el modo:

- **Contenido** (`quiz`, y en el futuro `rosco`, `song`, `movie`): cómo se guarda, valida,
  importa y sirve un ítem.
- **Formato** (`arcade`, `versus`, `fixed_solo`, `board_solo`): cómo corre una sesión
  (sillas, reloj, progresión, final).
- **Modo**: la combinación registrada que el jugador elige.

| `mode` | Contenido | Formato | Jugadores | Ranking |
|---|---|---|---|---|
| `trivia_arcade` | `quiz` | `arcade` | solo | sí |
| `trivia_versus` | `quiz` | `versus` | 1v1 | no |

`GET /modes` publica el catálogo (nombre, formato, input, medios, ranking y esquema de
configuración). El menú del cliente sale de ahí; agregar un modo es registrarlo en el
backend, no tocar dos listas.

Las tres piezas se combinan sin acoplarse: `trivia_arcade` y `trivia_versus` comparten el
contenido `quiz` y cambian el formato; un formato nuevo (`fixed_solo`, `board_solo`) puede
reusar `quiz` sin tocar el motor compartido. El cliente consume cualquier modo con el mismo
par de rutas según `players`: `POST /sessions` + `WS /ws/session/{id}` para `solo`,
`POST /rooms` + `WS /ws/room/{code}` para `versus`. El detalle del contrato está en
`docs/api.md` §`GET /modes`, §Sesiones y §WebSocket.

Los alias del cliente histórico (`/leaderboard/arcade`, `/admin/questions`, `/ws/arcade`)
siguen vivos mientras convivan con las rutas nuevas; su ventana está en
`docs/api.md` §Compatibilidad.

**Fuera del MVP:** matchmaking público o salas abiertas; salas de más de 2; modo por turnos;
preguntas con imagen/audio/video (campos listos, sin usar); cuentas reales; chat, amigos,
notificaciones, bots; monetización; despliegue en la nube (queda preparado).

**Escala:** 100–200 concurrentes, una instancia. **Autoridad:** el servidor decide todo; la
respuesta correcta nunca viaja antes de contestar; los puntajes se calculan en el servidor
con su propio reloj. **Idioma:** interfaz en español neutro (sin vos ni tú); código, tablas,
endpoints y variables en inglés.

**Arquitectura:** navegador (SvelteKit, PWA) ⇄ HTTP/JSON + WS/JSON ⇄ API FastAPI con motor de
juego en memoria y autoritativo. El frontend no guarda estado de juego propio que el servidor
no pueda reponer.

## Reglas del juego

### Constantes

```
CATEGORIES = geography, history, science, art, entertainment, sports
DIFFICULTY_MIN = 1 ; DIFFICULTY_MAX = 5

ONLINE_ROUNDS_OPTIONS = [3, 5, 7]      # default 5
ONLINE_SECONDS_OPTIONS = [10, 20, 30]  # default 20
ONLINE_BASE_POINTS = 100
ONLINE_TIME_BONUS_MAX = 50
MAX_TIEBREAK_ROUNDS = 3

ARCADE_LIVES = 3
ARCADE_SECONDS_START = 20 ; ARCADE_SECONDS_FLOOR = 5 ; ARCADE_SECONDS_STEP_EVERY = 3
ARCADE_DIFFICULTY_TIERS = [0, 4, 10, 18, 28]   # aciertos necesarios para dificultad 1..5
ARCADE_STREAK_BONUS_STEP = 10 ; ARCADE_STREAK_BONUS_MAX = 50

RECONNECT_GRACE_SECONDS = 20 ; ROOM_IDLE_TIMEOUT_SECONDS = 600
ROOM_CODE_LENGTH = 6
ROOM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # sin O, 0, I, 1
```

### Online (1v1)

- **Lobby:** el host crea la sala (`POST /rooms`, estado `waiting`) y comparte el código;
  los dos abren el WS. Con las dos sillas ocupadas, el host manda `start`. Una sala `waiting`
  sin arrancar expira a los 10 minutos.
- **Ronda:** se elige una pregunta publicada no usada en la partida, categoría al azar,
  dificultad por tramo (rondas 0–1 → 1–2, 2–3 → 2–3, 4–5 → 3–4, 6+ → 4–5). Se manda
  `round_start` con `ends_at`. La ronda se resuelve cuando **los dos** contestaron o al
  vencer el plazo, lo primero. `round_result` trae la correcta, qué eligió cada uno,
  ms, puntos y el marcador. No contestar = incorrecta, cero puntos.
- **Revelación:** 2,5 s (`REVEAL_SECONDS`) con la correcta, qué eligió cada uno y los puntos.
  La pantalla no explica la respuesta. El servidor pausa ese tiempo antes de servir la
  próxima ronda y calcula su `ends_at` después de la pausa.
- **Puntaje de ronda:** solo si acertó → `BASE + round(TIME_BONUS_MAX * ratio)`, con
  `ratio = clamp(1 - ms / (seconds * 1000), 0, 1)`. Con 20 s: acertar en 1 s da 148;
  al límite, 100.
- **Fin:** gana el que más puntos tiene. Empate → **rondas de desempate** a mitad de
  tiempo y dificultad 4–5, hasta `MAX_TIEBREAK_ROUNDS = 3`; agotado el tope, empate
  final (`winner_id` nulo). `match_end` trae ganador, puntajes y resumen ronda a ronda.
- **Abandono:** al desconectarse un jugador se pausa el reloj, el rival ve el aviso y
  corre una gracia de 20 s; si vuelve, sigue desde el mismo estado; si no, gana el que
  quedó y la partida queda `abandoned`. Si se van los dos, `void` (no cuenta).
- **Revancha:** al terminar, cuando los dos la piden, arranca una partida nueva en la
  misma sala con la misma config y preguntas nuevas; si uno no la pide, la sala vuelve a
  `waiting` y el host puede arrancar de nuevo con el mismo código.

### Arcade

- Arranca con 3 vidas, dificultad 1, racha 0, puntaje 0 y 20 s por pregunta.
- Dificultad por aciertos acumulados: 0–3 → 1, 4–9 → 2, 10–17 → 3, 18–27 → 4, 28+ → 5.
- Segundos: 20 al inicio, −1 cada 3 aciertos, piso 5.
- `puntos = BASE + round(TIME_BONUS_MAX * ratio) + min(STREAK_BONUS_STEP * streak, MAX)`,
  con `streak` = aciertos consecutivos **antes** de esta pregunta.
- Un error (o no contestar) descuenta vida; a 0 vidas termina. `arcade_end` trae puntaje,
  aciertos, dificultad máxima, mejor racha y la posición en ranking global y semanal.
- **Ranking por modo:** solo `trivia_arcade` publica ranking. `GET /leaderboard/trivia_arcade`
  ordena por mejor puntaje y desempata por el `ended_at` más temprano; `/leaderboard/arcade`
  sigue como alias para el cliente actual.
- **Revelación:** 2,5 s, igual que el 1v1; el servidor pausa antes de la próxima pregunta.
- Anti-trampa: puntajes y tiempos siempre del servidor; una corrida con tiempos
  imposibles se marca `invalid` y no entra al ranking.

### Categorías y color

Cada categoría tiene su color y **manda** en el badge y en el feedback de acierto
(`docs/diseno.md` los define). Las etiquetas visibles salen de `es.json`:

| `category` | etiqueta |
|---|---|
| `geography` | Geografía |
| `history` | Historia |
| `science` | Ciencia |
| `art` | Arte |
| `entertainment` | Entretenimiento |
| `sports` | Deportes |

## Pantallas

| Pantalla | Contenido |
|---|---|
| Inicio | Nick obligatorio (1–16), dos botones (arcade como modo principal, después 1v1), enlace al ranking y elección del **color del jugador** |
| Jugar | Una pantalla: crear sala (rondas y segundos) o unirse con el código |
| Lobby | Código gigante, las dos sillas (sin estado de conexión), botón `start` solo para el host |
| Partida | Marca arriba, pregunta, 4 `AnswerTile` en columna, `TimerBadge` + barra de tiempo, cápsulas de ronda, marcador abierto y aviso de rival |
| Revelación | Correcta, qué eligió cada uno y puntos; el paso siguiente flota al pie sin mover el tablero |
| Fin | Ganador, resumen ronda a ronda y revancha |
| Arcade | Pregunta, vidas (`LifeStrip`), racha, puntaje y tiempo |
| Fin de arcade | Puntaje, aciertos, mejor racha, mejor marca y posición |
| Ranking | Global / semanal |
| Admin | Solo por URL `/admin`: token, listado con filtros y paginación, subida de CSV/JSON con informe |

Componentes, tokens y reglas visuales: `docs/diseno.md`.

## Frontend

- **Mobile first**, columna máx. 480 px, sin scroll en partida, táctiles ≥ 44 px.
- **Un solo estilo** (pizarra cálida; `docs/diseno.md`): relleno liso, volumen por base sólida
  y bisel, sin degradados de color. El jugador elige su **color de acento** (5 swatches,
  `data-accent` sobre `<html>` + `localStorage`, clave `omni-accent`).
- **Estado:** `session` (`src/lib/api/session.svelte.ts`), `createLiveMatch`
  (`src/lib/match/live.svelte.ts`) y `createArcadeRun` (`src/lib/arcade/live.svelte.ts`) como
  máquinas de estados; `ws.ts` con reconexión y heartbeat.
- **PWA:** manifest + service worker nativo (`src/service-worker.ts`), cachea el app shell;
  el juego **no** funciona offline.
- **i18n:** todas las cadenas en `src/lib/i18n/es.json`; ninguna cadena visible en un componente.
- **Sonido:** efectos en `src/lib/sound.svelte.ts`, con preferencia de silencio persistida.
- **Presupuesto:** JS por debajo de 250 KB.

## Testing (frontend)

- `svelte-check` en verde y build que no avise.
- **Playwright:** una partida 1v1 completa (dos contextos) y un arcade hasta el final.
- Las e2e corren contra el backend real levantado (`make up && make migrate && make seed`),
  no contra mocks.

## Fases (roadmap)

| Fase | Entregable | Estado |
|---|---|---|
| 0 Esqueleto | monorepo, compose, CI, `/health`, inicio con tokens | ✅ backend |
| 1 Identidad y contenido | invitado + token, nicks, import, panel, 120 semilla | ✅ backend |
| 2 Salas y presencia | dos navegadores por código, sala llena, host cae, expira | ✅ backend |
| 3 Partida online | rondas cronometradas, revelación, puntajes, desempate, gracia, revancha | ✅ backend |
| 4 Arcade y ranking | 3 vidas, progresión, corte semanal, récord personal | ✅ backend |
| 5 Identidad visual | componentes propios, SVG, sonido, teclado, sin scroll, ≤250 KB JS | ✅ frontend |
| 6 PWA, e2e y docs | instalable, Playwright en CI, plan y README al día | ✅ |
| 7 (opcional) Publicar | `docker-compose.prod.yml`, `docs/deploy.md` | pendiente |

## Definición de terminado del MVP

1. Dos navegadores juegan un 1v1 completo entrando por código: rondas cronometradas,
   revelación, marcador y ganador.
2. Hay desempate, revancha y desconexión con 20 s de gracia.
3. El arcade sube dificultad, baja tiempo, pierde las 3 vidas y entra al ranking global y
   semanal.
4. El cliente no puede conocer la respuesta antes de contestar y todo puntaje sale del servidor.
5. ≥ 60 preguntas cargadas por el importador, repartidas entre las 6 categorías.
6. El CI pasa en verde, incluidas las e2e.
7. La interfaz no tiene gradientes decorativos ni emojis, y todos los íconos son SVG propios.
8. Levantar el proyecto desde cero toma a lo sumo cinco comandos documentados.
