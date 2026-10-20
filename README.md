# Omnisapiens

Trivia online con dos modos de juego: **duelo 1v1** en salas privadas identificadas por un
código de seis caracteres y **arcade individual** con dificultad y tiempo progresivos,
ranking global y semanal. La interfaz se instala como PWA, pero el juego necesita conexión:
todo el estado de una partida vive en el servidor.

El principio de diseño es que **el servidor es la única autoridad**. El cliente no calcula
puntajes, no conoce la respuesta correcta antes de responder y no decide el resultado de una
ronda: recibe eventos, dibuja el estado y envía la elección del jugador.

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy asíncrono, Alembic, PostgreSQL 16 y Redis 7 |
| Frontend | SvelteKit 3, Svelte 5, TypeScript, Vite 8 y PWA con `adapter-static` |
| Infraestructura local | Docker Compose + `uv` + Node.js |

## Cómo funciona

### Sesión

El primer acceso crea un **usuario invitado** (`POST /auth/guest`) y devuelve un JWT. El token
se guarda en `sessionStorage`: dura lo que dura la pestaña y no se comparte entre pestañas, lo
que permite abrir dos jugadores distintos en el mismo navegador. El backend exige el token en
`Authorization: Bearer …`; los WebSocket lo reciben en `?token=` porque el navegador no permite
cabeceras en ese transporte.

El perfil (`GET /me`) permite cambiar el nick (`PATCH /me`) y darse de baja (`DELETE /me`).

### Duelo 1v1

1. El host crea una sala (`POST /rooms`) y comparte el código.
2. Ambos jugadores abren `WS /ws/room/{code}`. Con las dos sillas ocupadas, el host envía
   `start`.
3. El servidor elige una pregunta publicada no usada en la partida y emite `round_start` con
   `ends_at`.
4. La ronda se resuelve cuando **los dos** respondieron o cuando vence el plazo, lo primero
   que ocurra. `round_result` incluye la opción correcta, la elección de cada jugador, los
   milisegundos, los puntos y el marcador.
5. Hay una pausa de revelación (`REVEAL_SECONDS`, 2,5 s) y luego comienza la ronda siguiente.
6. Gana quien suma más puntos. Un empate abre hasta tres rondas de desempate; si persiste,
   la partida termina en empate.

Los puntos de una ronda correcta combinan una base fija con un bono por velocidad. No
responder equivale a una respuesta incorrecta. Si un jugador se desconecta, el reloj se pausa
y el rival espera una gracia de 20 segundos; al volver, la partida continúa desde el mismo
estado. Si no vuelve, el jugador presente gana. Al finalizar, ambos pueden pedir revancha en
la misma sala.

### Arcade

La corrida comienza con tres vidas, dificultad 1 y 20 segundos por pregunta. Cada acierto
acumulado sube la dificultad y reduce el tiempo disponible; una racha de aciertos suma un
bono adicional. Un error o una pregunta sin responder descuenta una vida, y la corrida termina
al quedarse sin vidas. El resultado incluye puntaje, aciertos, mejor racha, dificultad máxima
y posición en el ranking global y semanal.

Las corridas con tiempos imposibles se marcan como inválidas y no entran al ranking.

### Comunicación

- **HTTP/JSON** para autenticación, perfil, ciclo de vida de las salas, ranking y panel de
  administración.
- **WebSocket/JSON** para el estado vivo de la partida y del arcade.
- Todos los errores tienen la forma `{"error": {"code", "message"}}`.

El estado de las salas y de las corridas activas está en memoria del proceso de la API. Esto
mantiene el MVP simple, pero obliga a correr **un solo worker** y a declararlo con
`SINGLE_PROCESS=1` fuera del entorno local.

### PWA y modo offline

El service worker cachea el shell de la aplicación y los recursos estáticos. La partida, el
ranking y el alta de usuario requieren red: no hay modo offline del juego.

## Arquitectura

```text
Navegador (SvelteKit SPA + PWA)
    │  HTTP/JSON  ·  autenticación, salas, ranking, admin
    │  WS/JSON    ·  /ws/room/{code}, /ws/arcade
    ▼
API FastAPI (un proceso, estado vivo en memoria)
    ├── PostgreSQL 16 · usuarios, preguntas, partidas, ranking
    └── Redis 7       · rate limiting y preguntas ya vistas
```

### Backend (`backend/`)

| Ruta | Responsabilidad |
|---|---|
| `app/api/routers/` | Endpoints HTTP de auth, perfil, salas, ranking, admin y health |
| `app/ws/` | Protocolo WebSocket de sala y arcade |
| `app/game/` | Reglas puras: puntajes, dificultad, selección de preguntas |
| `app/runtime/` | Salas y corridas vivas, en memoria |
| `app/services/` | Persistencia, ranking, importación y barrido de partidas huérfanas |
| `app/models/` · `alembic/` | Modelos SQLAlchemy y migraciones |
| `seeds/questions.csv` | 120 preguntas base listas para importar |
| `seeds/questions_new.csv` | 120 preguntas adicionales generadas y revisadas |
| `seeds/questions_batch_3.csv` | 68 preguntas adicionales revisadas (dificultad recalibrada) |

La respuesta correcta nunca se envía antes de que la ronda se resuelva y las opciones se
barajan al servir cada pregunta. El servidor también descarta las corridas de arcade con
tiempos inconsistentes.

### Frontend (`frontend/`)

| Ruta | Responsabilidad |
|---|---|
| `src/routes/` | Inicio, jugar, sala, ranking y admin |
| `src/lib/api/` | Cliente HTTP, sesión y WebSocket; no hay `fetch` ni `WebSocket` fuera de aquí |
| `src/lib/match/` · `src/lib/arcade/` | Máquinas de estado de la partida y de la corrida |
| `src/lib/components/` | Componentes propios, sin librería de UI |
| `src/lib/i18n/es.json` | Todas las cadenas visibles |
| `src/lib/sound.svelte.ts` | Efectos de sonido y preferencia de silencio |
| `src/service-worker.ts` · `static/manifest.webmanifest` | Instalación y caché del shell |

La SPA no tiene SSR (`ssr = false`): se compila como archivos estáticos y necesita un rewrite
de todas las rutas hacia `index.html`.

## Puesta en marcha

### Requisitos

- Docker con Compose.
- `uv` (gestiona Python 3.12 y las dependencias del backend).
- Node.js 22 o superior.

### Backend

```bash
cp backend/.env.example backend/.env

make up          # PostgreSQL 16 y Redis 7 en Docker
make migrate     # crea o actualiza el esquema
make seed        # importa las 308 preguntas semilla
make import FILE=mi-archivo.csv  # importa un archivo propio como borrador
make api         # API con reload en http://localhost:8000
```

La API se comprueba con `GET http://localhost:8000/health`, que devuelve el estado de la base
y de Redis. La documentación interactiva está en `http://localhost:8000/docs`.

Los mismos pasos sin `make`:

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run python -m app.cli seed
uv run uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

La aplicación queda en `http://localhost:5173` y usa `http://localhost:8000` como API por
defecto. Para apuntar a otro backend se define `PUBLIC_API_URL` en el entorno antes de
compilar o de iniciar el servidor de desarrollo.

`CORS_ORIGINS` del backend debe incluir el origen del frontend. El valor de ejemplo ya habilita
`http://localhost:5173`.

### Configuración

`backend/.env.example` documenta las variables disponibles. Las principales son:

| Variable | Uso |
|---|---|
| `DATABASE_URL` · `REDIS_URL` | Conexiones a PostgreSQL y Redis |
| `JWT_SECRET` · `JWT_TTL_DAYS` | Firma y vigencia del token de invitado |
| `ADMIN_TOKEN` | Pase de `X-Admin-Token` para el panel de preguntas |
| `CORS_ORIGINS` | Orígenes permitidos por el navegador |
| `ENV` · `SINGLE_PROCESS` | Entorno y declaración de worker único |
| `REVEAL_SECONDS` · `RECONNECT_GRACE_SECONDS` | Pausa de revelación y gracia por desconexión |
| `RATE_LIMIT_*` | Límites por IP y minuto |
| `ROOM_IDLE_TIMEOUT_SECONDS` · `STALE_MATCH_MINUTES` | Expiración de salas y partidas huérfanas |

Fuera de `local`, `JWT_SECRET` y `ADMIN_TOKEN` deben medir al menos 32 bytes, y la API se niega
a arrancar si el estado vivo está en memoria sin `SINGLE_PROCESS=1`.

## Comandos

| Comando | Acción |
|---|---|
| `make up` / `make down` | Levanta o baja PostgreSQL y Redis |
| `make migrate` | Aplica las migraciones de Alembic |
| `make seed` | Importa las preguntas de ejemplo como publicadas |
| `make import FILE=archivo.csv` | Importa un CSV propio (borrador por defecto) |
| `make check-seeds` | Valida los CSV de semilla (o `FILE=...`) sin tocar la base |
| `make api` | API en `:8000` con reload |
| `make front` | Frontend en `:5173` |
| `make test` | Tests del backend |
| `make cov` | Tests con cobertura mínima del 85 % |
| `make lint` | `ruff` + `mypy --strict` |
| `make check-schema` | Verifica que modelos y migraciones coincidan |

En `frontend/`: `npm run dev`, `npm run build`, `npm run preview`, `npm run check`
(`svelte-check`) y `npm run test:e2e` (Playwright, con la API levantada).

### Cargar preguntas

[`docs/preguntas.md`](docs/preguntas.md) reúne el formato CSV/JSON, la plantilla descargable,
las reglas de autoría y las fuentes (Wikidata, manual). También se importa desde el panel
`/admin` (`/admin/content/quiz`, con `/admin/questions` como alias); por terminal,
`make import FILE=...` carga borradores, `uv run python -m app.cli import-content --kind quiz
FILE` es el comando nuevo (con `import-questions` como alias) y los dos aceptan
`--status published`.

## Pruebas y calidad

- El backend se prueba contra PostgreSQL y Redis reales, no contra mocks; `make up` debe estar
  corriendo. `make cov` exige una cobertura mínima del 85 %.
- `make lint` aplica `ruff` y `mypy --strict`; `make check-schema` detecta modelos sin migrar.
- El frontend pasa `svelte-check` y un build de producción sin advertencias.
- La suite e2e con Playwright juega un 1v1 completo (dos contextos) y un arcade hasta el final
  contra el backend real, no contra mocks: necesita `make up && make migrate && make seed` y la
  API en `:8000`. Se corre con `npm run test:e2e` desde `frontend/`; Playwright levanta la SPA
  en `:5173`.
- El CI ejecuta lint, migraciones, cobertura del backend, `check` + `build` del frontend y la
  suite e2e.

## API

El contrato completo, con formas, códigos de error y detalles del protocolo WebSocket, está en
[`docs/api.md`](docs/api.md).

| Endpoint | Descripción |
|---|---|
| `POST /auth/guest` | Alta de invitado y emisión del JWT |
| `GET` · `PATCH` · `DELETE /me` | Perfil, cambio de nick y baja lógica |
| `POST /rooms` · `GET /rooms/{code}` | Creación y vista previa de una sala 1v1 |
| `WS /ws/room/{code}` | Partida 1v1 en vivo |
| `WS /ws/arcade` | Corrida de arcade en vivo |
| `GET /leaderboard/arcade` · `GET /leaderboard/arcade/me` | Ranking global y semanal |
| `GET` · `POST /admin/content/{kind}` | Listado e importación de contenido (alias `/admin/questions`) |
| `GET /health` | Estado de la API, PostgreSQL y Redis |

## Estructura del repositorio

```text
.
├── backend/              API, migraciones, pruebas y semillas
├── frontend/             SPA SvelteKit y PWA
├── docs/                 Producto, API, diseño, colas de trabajo y archivo histórico
├── docker-compose.yml    PostgreSQL y Redis para desarrollo
├── Makefile              Atajos de desarrollo
└── .github/workflows/    Integración continua
```

## Documentación

| Archivo | Contenido |
|---|---|
| [`docs/plan.md`](docs/plan.md) | Producto, reglas del juego, pantallas y roadmap |
| [`docs/api.md`](docs/api.md) | Contrato HTTP y WebSocket |
| [`docs/diseno.md`](docs/diseno.md) | Sistema visual, componentes y accesibilidad |
| [`docs/frontend.md`](docs/frontend.md) | Convenciones de trabajo del frontend |
| [`docs/backend.md`](docs/backend.md) | Convenciones de trabajo del backend |
| [`docs/archive/`](docs/archive/) | Decisiones y auditorías históricas del backend |

## Despliegue

El frontend se compila con `npm run build` en `frontend/build/` y puede servirse desde
cualquier CDN o servidor estático, con fallback a `index.html`. El backend requiere PostgreSQL,
Redis y un único proceso; las credenciales y secretos se inyectan por entorno. El
`docker-compose.prod.yml` y la guía de despliegue todavía no forman parte del repositorio.
