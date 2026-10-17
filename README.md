# Omnisapiens

Trivia online. Backend en **FastAPI + Python 3.12**, PostgreSQL 16 y Redis 7.
El frontend (SvelteKit) lo hace otra persona: este repo es el backend.

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

## Comandos

| Comando | Qué hace |
|---|---|
| `make up` / `make down` | Levanta / baja Postgres y Redis |
| `make migrate` | `alembic upgrade head` |
| `make seed` | Importa `backend/seeds/questions.csv` como publicadas |
| `make import FILE=mi.csv` | Importa un CSV propio (queda en `draft` si no se publica) |
| `make api` | API en `:8000` con reload |
| `make test` | Tests (rápido, sin umbral de cobertura) |
| `make cov` | Tests con cobertura y umbral de 85 % (el gate del CI) |
| `make lint` | `ruff check` + `ruff format --check` + `mypy --strict` |
| `make check-schema` | Falla si los modelos y las migraciones se desincronizaron |

Los tests usan **Postgres y Redis reales** (base `trivia_test` y Redis `/1`), no
SQLite ni mocks. Por eso `make up` tiene que estar corriendo.

## API

- `POST /auth/guest` → alta de invitado y token JWT.
- `GET`/`PATCH`/`DELETE /me` → perfil, cambio de nick y baja lógica.
- `POST /rooms` → crea una sala 1v1 y devuelve el código.
- `GET /rooms/{code}` → vista previa (estado, config, `players`, vencimiento).
- `WS /ws/room/{code}?token=...` → sala en vivo (`hello`, `start`, `answer`,
  `rematch`, `ping`; el servidor manda `room_state`, `round_start`, `round_result`,
  `match_end`, `error`).
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
