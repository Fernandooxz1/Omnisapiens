# Omnisapiens

Trivia online. Backend en **FastAPI + Python 3.12**, PostgreSQL 16 y Redis 7.
El frontend real (SvelteKit) lo hace otra persona: `frontend/dev/` es una página de
prueba del backend, no el producto.

## Levantarlo en cinco comandos

Requisitos: **Docker** y **uv** (instala solo CPython 3.12 si hace falta).

```bash
cp backend/.env.example backend/.env   # configuración local (dev)
make up          # Postgres 16 + Redis 7 en Docker
make migrate     # crea las tablas (Alembic)
make seed        # carga las 60 preguntas de ejemplo
make api         # uvicorn con reload en http://localhost:8000
```

Comprobación: `GET http://localhost:8000/health` devuelve
`{"api":"ok","db":"ok","redis":"ok"}`. La documentación interactiva queda en
`http://localhost:8000/docs`.

## Probar a ojo (sala y arcade)

Con `make api` corriendo, en otra terminal:

```bash
make web   # sirve frontend/dev/ en http://localhost:5173
```

Abrí `http://localhost:5173`. Para el 1v1 hacen falta **dos pestañas con nicks
distintos** (no dupliques la pestaña: las dos compartirían la sesión). La página
muestra el log crudo de los mensajes WebSocket y no es el frontend del producto.

### Notas de la página de prueba

- Es **solo para desarrollo**: no reemplaza al frontend SvelteKit ni invierte en estilos.
- La sesión va en `sessionStorage`. Si duplicás la pestaña, el navegador puede copiarla
  y las dos serían el mismo jugador: abrí una pestaña nueva y entrá a la URL.
- **No reconecta sola al recargar**: la sala se retoma entrando de nuevo con el código;
  el arcade no (una corrida cortada queda `playing` y el barrendero la invalida).
- Al reconectar a mitad de partida, el marcador local vuelve a `0-0` hasta el próximo
  resultado: `room_state` no lleva puntajes.
- `players` en `room_state` incluye sillas desconectadas, así que `2/2` puede adelantarse
  unos segundos; el servidor igual rechaza `start` con `NOT_READY`.

## Comandos

| Comando | Qué hace |
|---|---|
| `make up` / `make down` | Levanta / baja Postgres y Redis |
| `make migrate` | `alembic upgrade head` |
| `make seed` | Importa `backend/seeds/questions.csv` como publicadas |
| `make import FILE=mi.csv` | Importa un CSV propio (queda en `draft` si no se publica) |
| `make api` | API en `:8000` con reload |
| `make web` | Página de prueba en `:5173` (sirve `frontend/dev/`) |
| `make test` | Tests (rápido, sin umbral de cobertura) |
| `make cov` | Tests con cobertura y umbral de 85 % (el gate del CI) |
| `make lint` | `ruff check` + `ruff format --check` + `mypy --strict` |
| `make check-schema` | Falla si los modelos y las migraciones se desincronizaron |

Los tests usan **Postgres y Redis reales** (base `trivia_test` y Redis `/1`), no
SQLite ni mocks. Por eso `make up` tiene que estar corriendo.

## API

- `POST /auth/guest` → alta de invitado y token JWT.
- `GET`/`PATCH`/`DELETE /me` → perfil (con mejor marca e historial de arcade y 1v1),
  cambio de nick y baja lógica.
- `POST /rooms` → crea una sala 1v1 y devuelve el código.
- `GET /rooms/{code}` → vista previa (estado, config, `players`, vencimiento).
- `WS /ws/room/{code}?token=...` → sala en vivo (`hello`, `start`, `answer`,
  `rematch`, `ping`; el servidor manda `room_state`, `round_start`, `round_result`,
  `match_end`, `error`).
- `WS /ws/arcade?token=...` → corrida flash (`start`, `answer`, `ping`; el servidor
  manda `arcade_start`, `arcade_question`, `arcade_result`, `arcade_end`).
- `GET /leaderboard/arcade?period=all|week&limit=50` → tabla del ranking.
- `GET /leaderboard/arcade/me` → posición y marca del jugador en ambos períodos.
- `GET /health` → 503 si falta Postgres o Redis.

Los errores tienen siempre la forma `{"error": {"code", "message"}}`.

## Decisiones que conviene no olvidar

- El **estado vivo de las salas está en memoria**: hoy el backend corre en **una
  sola instancia** (el código asume un proceso).
- El servidor es **autoritativo**: la respuesta correcta no viaja al cliente antes
  de contestar, y las opciones se barajan al servir.
- El token del WS viaja en `?token=` (el navegador no deja headers en
  `new WebSocket`); los logs filtran ese renglón.
- `docs/plan.md` es la memoria del proyecto: estado de sesión, plan del MVP y
  diseño de la capa de datos. `docs/observaciones.md` es la auditoría (cerrada).
