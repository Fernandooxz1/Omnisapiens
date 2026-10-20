# Backend — renombrar «corrida» a «partida»

## Contexto

El frontend ya llama **partida** a todo lo que ve el jugador. Del lado backend quedan textos
en español que todavía dicen «corrida»: mensajes de error, docstrings, comentarios y prosa de
`docs/api.md` / `docs/backend.md`. Es un cambio de redacción, no de contrato.

## Alcance

- Reemplazá `corrida` / `corridas` / `Corrida` por `partida` / `partidas` / `Partida` en **texto
  humano en español**: mensajes que ve el jugador, docstrings, comentarios, documentación y
  textos de tests.
- Los mensajes del arcade que hoy dicen «corrida» deben decir «partida» (por ejemplo
  `ALREADY_STARTED`, `NOT_PLAYING` y los de registro/cierre en `app/ws/arcade_ws.py`). No
  cambies los códigos ni el significado de los mensajes.
- `docs/api.md` conserva el contrato: solo cambia la prosa. Lo mismo en `docs/backend.md`.
- **No toques identificadores, clases, tablas, columnas, campos de payload, rutas, firmas,
  códigos de error ni esquemas.** `arcade_runs`, `ArcadeRun`, `arcade_answers` y compañía se
  quedan como están. Tampoco hay migración ni cambio de comportamiento.
- Los identificadores locales en español (por ejemplo `corrida` en
  `app/api/routers/me.py`) pueden quedar; el foco es el texto que lee una persona.
- No toques `frontend/`.

## Verificación

```sh
make lint
make cov
make check-schema
```

`make check-schema` (`alembic check`) no debe detectar nada: si detecta un cambio, se tocó un
modelo de más.

Para revisar el alcance:

```sh
grep -rni "corrida" backend/app backend/tests docs/api.md docs/backend.md
```

Cada resultado que quede debe ser un identificador o un fixture, nunca una frase.

## Cierre

- Un commit en inglés, por ejemplo:
  `refactor(api): rename corrida to partida in prose and messages`
- Stageá solo `backend/` y los documentos que toques. Nada de `git add -A`.
- No modifiques `docs/plan-refactor/estado.md` ni `docs/tareas-backend.md`: esto es un pulido
  puntual, no una tarea de la cola del refactor.
- Reportá en 3–5 líneas qué tocaste, cómo se verifica y el hash del commit.
