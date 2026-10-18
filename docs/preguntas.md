# Preguntas — cómo escribirlas y cargarlas

El banco de preguntas entra por un único importador (CSV o JSON) y se revisa en el panel
`/admin`. No hace falta tocar la base ni el backend.

## La vía rápida (sin terminal)

1. Entrá a `/admin` con el `ADMIN_TOKEN` del backend (`backend/.env`).
2. En **Importar preguntas**, descargá la **plantilla CSV**.
3. Una fila por pregunta. Borrá las dos filas de ejemplo.
4. Importá con estado **Publicada**: es el único estado que entra a las partidas. Un
   **Borrador** sirve para revisar el listado, pero no se puede publicar después (hoy no hay
   edición); si dudás, revisá el archivo antes y subilo publicado.
5. Si hay filas rechazadas, el informe dice el número de fila y el motivo. Corregilas y volvé a
   subir el archivo: lo ya importado sale como duplicado y no se carga dos veces.

## Columnas

```csv
category,difficulty,prompt,option_a,option_b,option_c,option_d,correct,explanation,source,tags
geography,3,¿Cuál es la capital de Australia?,Sídney,Melbourne,Canberra,Perth,C,"Canberra es la capital, no la ciudad más poblada.",manual,capitales;oceanía
```

| Columna | Regla |
|---|---|
| `category` | `geography`, `history`, `science`, `art`, `entertainment` o `sports` |
| `difficulty` | entero 1–5 (1 fácil, 5 difícil) |
| `prompt` | enunciado de 1 a 300 caracteres; tiene que entenderse solo |
| `option_a` … `option_d` | las cuatro opciones, no vacías y distintas entre sí |
| `correct` | letra `A`, `B`, `C` o `D` |
| `explanation` | opcional; una frase con el dato o el porqué |
| `source` | opcional; `manual`, `wikidata`, una URL… |
| `tags` | opcional; separadas por `;` (`capitales;oceanía`) |

Detalles del importador:

- El encabezado tiene que tener **exactamente** esas columnas (el orden no importa).
- CSV en UTF-8 (con o sin BOM). Los campos con comas o comillas van entre comillas dobles.
- JSON: un array de objetos con las mismas claves; `tags` puede ser lista.
- El duplicado se detecta por el **enunciado normalizado** (sin tildes, signos ni mayúsculas):
  cambiar las opciones no esquiva el duplicado.
- Una fila mala no aborta la carga: queda en el informe con su motivo.

## Por terminal

```sh
# Borrador (para revisar en /admin antes de publicar)
make import FILE=mis-preguntas.csv

# Publicada directamente, salteando el `make`
cd backend && uv run python -m app.cli import-questions ../mis-preguntas.csv --status published

# Las 120 semilla del repo
make seed
```

`make seed` importa `backend/seeds/questions.csv` como publicado; ese archivo es la mejor
referencia de tono, dificultad y opciones. Hoy el banco son 120 preguntas repartidas así:
18 de dificultad 1, 23 de 2, 27 de 3, 28 de 4 y 24 de 5, con al menos 3 de cada nivel
3–5 en las seis categorías. Al sumar preguntas, mantené esa proporción para que las rondas
tardías del 1v1 y el arcade no terminen cayendo en preguntas fáciles.

## Extraer preguntas de una fuente

La regla corta: **los hechos no tienen dueño, la redacción sí**. No copies enunciados ni
opciones de sitios o apps de trivia; escribí la pregunta de nuevo y citá la fuente.

### Wikidata (recomendado para datos duros)

Wikidata es CC0 y tiene etiquetas en español. El repo trae un generador de borradores de
capitales:

```sh
python3 tools/questions/from_wikidata.py --limit 40 --out capitales.csv
```

Genera `category=geography` con cuatro capitales, la correcta marcada, dificultad estimada por
población y `source=wikidata`. Los distractores son países de población parecida, pero siguen
siendo una heurística: revisá que las opciones sean plausibles y ajustá la dificultad a mano.
Después se importa como cualquier CSV.

`tools/questions/capitales-10.csv` es un lote ya curado como ejemplo: 4 fáciles, 2 medias y 4
difíciles, con distractores elegidos a mano. Se importa tal cual:

```sh
cd backend && uv run python -m app.cli import-questions ../tools/questions/capitales-10.csv --status published
```

La consulta se puede adaptar a otros datos con la misma forma (obra → autor, país → moneda,
elemento → símbolo). Lo que no conviene automatizar sin revisión son preguntas de historia,
entretenimiento o deporte: la respuesta depende del recorte y de la actualidad.

### Open Trivia DB

Es cómoda pero **hoy solo responde en inglés** (el parámetro `lang=es` se ignora). Traducir y
adaptar cada pregunta cuesta más que escribirla, y la base es CC BY-SA: hay que atribuir. No es
la mejor fuente para este juego.

### Escribirlas vos (o con ayuda de un modelo)

Es la mejor calidad por esfuerzo, sobre todo para historia, arte, deporte y entretenimiento.
Para un lote nuevo, copiá el prompt de abajo y **adjuntá `backend/seeds/questions.csv`** (o
pegá solo su columna `prompt`): así el modelo sabe qué preguntas ya existen y no las repite.
Cambiá la cantidad si querés otro tamaño, pero conservá la distribución por categoría y
dificultad.

```text
Sos editor de contenido de Omnisapiens, un juego de trivia en español rioplatense neutro.
Tu tarea es escribir preguntas nuevas y devolver un único CSV listo para importar.

CONTEXTO
Te adjunto el CSV del banco actual (`backend/seeds/questions.csv`). Leelo completo antes de
escribir. No repitas ni reformules ninguno de sus enunciados, ni siquiera cambiando las
opciones. No reutilices la misma respuesta correcta con otro enunciado.

CANTIDAD Y BALANCE
Escribí 60 preguntas: 10 por cada categoría.
En cada categoría: 2 de dificultad 1, 2 de 2, 2 de 3, 2 de 4 y 2 de 5.
Variá los temas dentro de cada categoría; no hagas diez preguntas de fútbol ni diez de cine.

FORMATO DE SALIDA
Devolvé solo el CSV, sin explicación, sin markdown y sin bloques de código.
Encabezado exacto, una sola vez:
category,difficulty,prompt,option_a,option_b,option_c,option_d,correct,explanation,source,tags

Reglas de cada columna:
- category: geography, history, science, art, entertainment o sports.
- difficulty: entero de 1 a 5 (1 fácil, 5 difícil).
- prompt: una sola pregunta autosuficiente, de 1 a 300 caracteres.
- option_a, option_b, option_c, option_d: cuatro opciones no vacías y distintas entre sí.
- correct: A, B, C o D, y tiene que coincidir con la posición de la opción correcta.
- explanation: una frase con el dato o el porqué; no repitas literalmente la opción.
- source: llm.
- tags: 1 a 4 etiquetas en minúsculas, separadas por `;` y sin comas.

REGLAS DE CONTENIDO
- Una sola respuesta correcta e indiscutible. Si hay dos defendibles, descartá la pregunta.
- Los tres distractores tienen que ser del mismo tipo que la correcta y plausibles; nada de
  opciones absurdas, "todas las anteriores" ni "ninguna de las anteriores".
- No uses preguntas negativas ("¿Cuál NO...?") ni preguntas de opinión.
- Dificultad: 1 es cultura general amplia; 3 es secundaria; 5 es especializado. Difícil no
  significa inventado ni irrelevante: el dato tiene que ser verificable.
- Usá hechos estables. Evitá "actualmente", cargos vigentes, récords que cambian, precios,
  dueños de clubes, fronteras disputadas y cualquier dato de la coyuntura.
- Español neutro con tildes y signos correctos. Opciones cortas, sin explicaciones adentro.
- Repartí la letra correcta entre A, B, C y D; no pongas todas en la misma letra.
- Si no estás seguro de un dato, descartá la pregunta: no la inventes ni la completes con
  una fecha aproximada.

CSV
- UTF-8, sin BOM, sin líneas vacías y sin filas de ejemplo.
- Si un campo tiene coma, comilla o salto de línea, va entre comillas dobles; las comillas
  internas se duplican. No uses saltos de línea dentro de un campo.
- Una fila por pregunta. No agregues columnas ni comentarios.

Ejemplo de formato (no lo incluyas: ya existe en el banco):
geography,3,¿Cuál es la capital de Australia?,Sídney,Melbourne,Canberra,Perth,C,"Canberra es la capital, no la ciudad más poblada.",llm,capitales;oceanía

ANTES DE RESPONDER, VERIFICÁ
- Hay 60 filas de datos además del encabezado.
- Hay 10 preguntas por categoría y 2 por cada dificultad.
- Todas tienen cuatro opciones distintas y una letra `correct` que coincide.
- No hay enunciados repetidos ni parecidos a los del banco adjunto.
- Ningún campo con comas quedó sin comillas y no hay markdown alrededor del CSV.
```

Después se revisa a mano: un modelo inventa fechas y atribuciones con seguridad. El
importador rechaza las filas mal formadas, pero no detecta un dato falso.

## Antes de publicar

- [ ] La respuesta correcta es **una sola** y no depende de una interpretación.
- [ ] Los distractores son del mismo tipo y plausibles; nada de “todas las anteriores”.
- [ ] El enunciado no necesita contexto externo (“según el texto…”) y entra en 300 caracteres.
- [ ] Español neutro, tildes y signos correctos; opciones sin explicaciones adentro.
- [ ] La dificultad es coherente con las semilla (1: cultura general, 5: especializado).
- [ ] No hay otra pregunta con el mismo enunciado normalizado.
- [ ] El dato no caduca (evitá “actualmente”, récords o cargos vigentes).
- [ ] `source` y `tags` ayudan a encontrarla después.
