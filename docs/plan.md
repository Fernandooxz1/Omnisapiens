# Omnisapiens — plan del producto (frontend)

> Especificación viva del MVP. Es **estable**: la cola de trabajo vive en `docs/tareas.md`.
> El contrato técnico (WS, HTTP, auth, ranking, admin) está en `docs/api.md`; el sistema
> visual, en `docs/diseno.md`. Este archivo se consulta por sección (`grep`), no entero.

## Estado

El **backend está terminado** (HTTP, WS, salas, arcade, ranking, panel de admin, 547 tests,
cobertura 94 %) y no se toca. Lo que falta es el producto: el frontend arranca de cero en
`frontend/` (SvelteKit + TypeScript). `frontend/dev/` es la página de prueba del backend, no
el producto, y se borra cuando lobby y arcade anden de verdad.

**La próxima tarea está en `docs/tareas.md`.** El detalle del backend quedó archivado en
`docs/archive/` (no se lee).

## Producto

**Dos modos.**

1. **Sala privada 1v1 por código:** dos jugadores, pregunta a la vez, ambos responden
   simultáneo, gana quien más puntos junta.
2. **Arcade:** un jugador solo, dificultad y tiempo progresivos hasta quedarse sin vidas;
   ranking global y semanal.

**Fuera del MVP:** matchmaking público o salas abiertas; salas de más de 2; modo por turnos;
preguntas con imagen/audio/video (campos listos, sin usar); cuentas reales; chat, amigos,
notificaciones, bots; monetización; despliegue en la nube (queda preparado).

**Escala:** 100–200 concurrentes, una instancia. **Autoridad:** el servidor decide todo; la
respuesta correcta nunca viaja antes de contestar; los puntajes se calculan en el servidor
con su propio reloj. **Idioma:** interfaz en español; código, tablas, endpoints y variables
en inglés.

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
  los dos abren el WS. Con los dos conectados, el host manda `start`. Una sala `waiting`
  sin arrancar expira a los 10 minutos.
- **Ronda:** se elige una pregunta publicada no usada en la partida, categoría al azar,
  dificultad por tramo (rondas 0–1 → 1–2, 2–3 → 2–3, 4–5 → 3–4, 6+ → 4–5). Se manda
  `round_start` con `ends_at`. La ronda se resuelve cuando **los dos** contestaron o al
  vencer el plazo, lo primero. `round_result` trae la correcta, qué eligió cada uno,
  ms, puntos y el marcador. No contestar = incorrecta, cero puntos.
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
| Inicio | Dos botones (jugar 1v1 / arcade), nick e ingreso como invitado |
| Jugar | Crear sala (rondas y segundos) o unirse por código |
| Lobby | Código gigante, jugadores conectados, botón `start` solo para el host |
| Partida | Pregunta, 4 `AnswerTile`, `TimerRing`, marcador y aviso de rival |
| Revelación | Correcta, qué eligió cada uno, puntos y explicación |
| Fin | Ganador, resumen ronda a ronda y revancha |
| Arcade | Pregunta, vidas (`LifeStrip`), racha, puntaje y tiempo |
| Fin de arcade | Puntaje, aciertos, mejor racha, mejor marca y posición |
| Ranking | Global / semanal |
| Admin | Token, listado con filtros y paginación, subida de CSV/JSON con informe |

Componentes, tokens y reglas visuales: `docs/diseno.md`.

## Frontend

- **Mobile first**, columna máx. 480 px, sin scroll en partida, táctiles ≥ 44 px.
- **Estado:** stores `sessionStore` / `matchStore` / `arcadeStore` como máquinas de estados;
  `ws.ts` con reconexión y heartbeat.
- **PWA:** manifest + service worker (`generateSW`), cachea el app shell; el juego **no**
  funciona offline.
- **i18n:** todas las cadenas en `app/i18n/es.json`; ninguna cadena visible en un componente.
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
| 1 Identidad y contenido | invitado + token, nicks, import, panel, 72 semilla | ✅ backend |
| 2 Salas y presencia | dos navegadores por código, sala llena, host cae, expira | ✅ backend |
| 3 Partida online | rondas cronometradas, revelación, puntajes, desempate, gracia, revancha | ✅ backend |
| 4 Arcade y ranking | 3 vidas, progresión, corte semanal, récord personal | ✅ backend |
| 5 Identidad visual | 9 componentes, SVG propios, sonido, teclado, sin scroll, ≤250 KB JS | ← ahora |
| 6 PWA, e2e y docs | instalable, Playwright en CI, plan y README al día | pendiente |
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
