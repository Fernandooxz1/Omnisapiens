# Omnisapiens

Trivia online. **Backend** en FastAPI + Python 3.12 (terminado: HTTP, WebSocket, salas 1v1,
arcade, ranking y panel de admin). **Frontend** en SvelteKit + TypeScript + PWA (en curso).

## Levantar el backend

Requisitos: **Docker** y **uv** (instala solo CPython 3.12 si hace falta).

```bash
cp backend/.env.example backend/.env   # configuración local (dev)
make up          # Postgres 16 + Redis 7 en Docker
make migrate     # crea las tablas (Alembic)
make seed        # carga las 72 preguntas de ejemplo
make api         # uvicorn con reload en http://localhost:8000
```

Comprobación: `GET http://localhost:8000/health` → `{"api":"ok","db":"ok","redis":"ok"}`.
Documentación interactiva: `http://localhost:8000/docs`.

## Levantar el frontend

Requisitos: **Node 22+**.

```bash
cd frontend
npm ci
npm run dev     # http://localhost:5173 (el API tiene que estar en :8000)
make front      # lo mismo, desde la raíz
```

`npm run check` corre `svelte-check` y `npm run build` deja la SPA estática en
`frontend/build/`. El cliente no tiene SSR: el token de invitado vive en `sessionStorage`.
Todas las cadenas visibles están en `frontend/src/lib/i18n/es.json`.

## Página de prueba del backend

```bash
make web   # sirve frontend/dev/ en http://localhost:5173
```

Es un sandbox para ver el contrato funcionando (login de invitado, sala 1v1, revancha,
arcade, ranking y admin), **no** el producto. Se borra cuando lobby y arcade anden en
SvelteKit. Para el 1v1 hacen falta dos pestañas con nicks distintos: no duplicar la pestaña,
compartiría la sesión.

## Comandos

| Comando | Qué hace |
|---|---|
| `make up` / `make down` | Levanta / baja Postgres y Redis |
| `make migrate` | `alembic upgrade head` |
| `make seed` | Importa `backend/seeds/questions.csv` como publicadas |
| `make import FILE=mi.csv` | Importa un CSV propio (`draft` por defecto) |
| `make api` | API en `:8000` con reload |
| `make web` | Página de prueba en `:5173` |
| `make front` | SPA real en `:5173` (`npm run dev`) |
| `make test` / `make cov` | Tests rápidos / con umbral de cobertura (85 %) |
| `make lint` | `ruff` + `mypy --strict` |
| `make check-schema` | Falla si modelos y migraciones se desincronizaron |

Los tests usan **Postgres y Redis reales** (base `trivia_test`, Redis `/1`), no SQLite ni
mocks: `make up` tiene que estar corriendo.

## API

El contrato completo (formas, códigos y trampas del cliente) está en **`docs/api.md`**.
Resumen:

- `POST /auth/guest` → alta de invitado y JWT.
- `GET`/`PATCH`/`DELETE /me` → perfil, cambio de nick y baja lógica.
- `POST /rooms` · `GET /rooms/{code}` → sala 1v1.
- `WS /ws/room/{code}?token=...` → sala en vivo.
- `WS /ws/arcade?token=...` → corrida arcade.
- `GET /leaderboard/arcade` · `GET /leaderboard/arcade/me`.
- `GET /admin/questions` · `POST /admin/questions/import` (`X-Admin-Token`).
- `GET /health`.

Errores siempre `{"error": {"code", "message"}}`.

## Decisiones que no se re-descubren

- El estado vivo de las salas está **en memoria**: el backend corre en un solo worker
  (fuera de `local` exige `SINGLE_PROCESS=1` o no arranca).
- El servidor es **autoritativo**: la respuesta correcta no viaja antes de contestar y las
  opciones se barajan al servir.
- El token del WS viaja en `?token=` (el navegador no deja headers); no loguearlo.
- Cada rol (frontend, backend) trabaja solo en su carpeta; si falta un contrato, se anota en
  `docs/api.md` y se implementa del lado que corresponde.

## Documentación

| Archivo | Qué es |
|---|---|
| `AGENTS.md` | Router: qué brief lee cada rol y reglas del árbol |
| `docs/frontend.md` | Brief del rol frontend (SvelteKit) |
| `docs/backend.md` | Brief del rol backend (FastAPI) |
| `docs/tareas.md` | Cola volátil de tareas del frontend |
| `docs/tareas-backend.md` | Cola volátil de tareas del backend |
| `docs/plan.md` | Producto, reglas del juego, pantallas y roadmap |
| `docs/api.md` | Contrato HTTP + WebSocket |
| `docs/diseno.md` | Sistema visual, componentes y accesibilidad |
| `docs/archive/` | Backend histórico (arquitectura, trampas, auditoría) |
