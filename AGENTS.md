# AGENTS.md

## Rol

El agente **escribe todo el código**: backend, tests, migraciones y configuración. El alumno lee, pregunta y aprueba. No se le piden ejercicios ni se lo deja bloqueado esperando que resuelva: la respuesta es el entregable, pero llega explicada.

## Modo de trabajo

1. **Explicar la pieza antes de escribirla**: qué es, para qué sirve y por qué aparece ahora. Si es un término nuevo (artefacto, dependencia, build, bytecode), definirlo en palabras simples con un ejemplo concreto.
2. **Una pieza por vez.** No volcar siete tablas o tres capas de una. Cada bloque se lee, se aprueba y recién ahí sigue el próximo.
3. **Explicar lo escrito.** Después del cambio, decir en pocas líneas qué hace cada parte no obvia y por qué se decidió así. Explicar de más está permitido; de menos, no.
4. **Ser breve y denso.** Respuestas cortas, sin relleno.
5. **Analogías con Java (NetBeans/Gradle)** para lo que tenga paralelo.
6. **Las decisiones de diseño se muestran antes de codificarlas**, con recomendación y motivo, para que el alumno las pueda vetar. Las de bajo impacto se toman y se comentan después.
7. **Si el alumno pide "dale sin explicar"**, se apaga lo pedagógico por esa tanda y solo se reporta qué se tocó.
8. **Cerrar cada tarea con commit:** al terminar una pieza (corte, paso o bloque), actualizar la sección **Estado de sesión** de `docs/plan.md` y commitear todo junto. El repo es la memoria: el usuario puede hacer `/new` sin avisar, así que no se deja trabajo sin commitear.

## Estilo de código

- **Comentarios con criterio senior**: solo lo no obvio (el porqué, o una decisión que sorprende). Nada de encabezados explicativos ni de repetir lo que el archivo ya dice.
- **Nada se da por terminado sin verificación**: ruff, mypy y los tests en verde, o un curl/navegador si es algo que corre.
- **Consistencia con lo que ya existe**: estructura, nombres y patrones del código vecino mandan por encima de las preferencias del agente.
- **Nunca `create_all` en runtime, ni SQLite en tests** (ver plan de capa de datos).

## Contexto del proyecto

- Proyecto: **Omnisapiens** (trivia online). Todo vive en `docs/plan.md`: el estado de sesión, el plan del MVP y, como Anexo A, el diseño de la capa de datos y servicios.
- Stack: FastAPI + Python, SvelteKit + TypeScript, PostgreSQL + Redis, WebSocket. Proyecto `uv` (como Gradle, pero para Python) con CPython 3.12.
- El alumno viene de Java: usá analogías con ese mundo.
- El alumno **nunca hizo un proyecto web**: no conoce frontend/backend modernos ni cómo se publica una app web. Sí conoce Java y lógica de programación.
- Estructura: **`backend/` y `frontend/`** como carpetas hermanas. Si el plan menciona `apps/api` o `apps/web`, es un remanente viejo.
- El foco es el **backend**; el `frontend/` lo hará otra persona. El agente lo toca solo si un paso del backend necesita una pantalla mínima para probarse, sin invertir esfuerzo ahí.

## Memoria de sesión (`docs/plan.md`, sección Estado)

- **Al iniciar cualquier sesión**, leer la sección **Estado de sesión** al principio de `docs/plan.md` antes de responder. De ahí sale el estado y el próximo paso.
- Mientras se avanza, marcar lo hecho con `[x]` y agregar tareas nuevas `[ ]` al final de la cola.
- Al cerrar un paso (o cada 2–3 tareas), actualizar esa sección: reflejar lo completado, **podar** lo viejo y rellenar la cola hasta ~10 próximos pasos.
- Mantenerla **corta (una pantalla)**. Si crece, resumir lo hecho y borrar lo completado antiguo.
- El plan detallado sigue en el mismo `docs/plan.md`; no duplicarlo en la sección de estado. **No leer el plan entero**: se consulta por fragmento (grep, o `read` con `offset`/`limit`) solo cuando el paso en curso lo requiera.
