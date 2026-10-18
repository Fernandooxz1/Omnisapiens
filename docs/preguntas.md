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

# Las 72 semilla del repo
make seed
```

`make seed` importa `backend/seeds/questions.csv` como publicado; ese archivo es la mejor
referencia de tono, dificultad y opciones.

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
Un prompt útil para un borrador:

> Generá N preguntas de trivia en español rioplatense neutro sobre \<tema\>. Devolvé solo CSV
> con estas columnas: category,difficulty,prompt,option_a,option_b,option_c,option_d,correct,
> explanation,source,tags. Una sola respuesta correcta, tres distractores plausibles de la
> misma categoría, dificultad 1–5 y explicación de una frase. No repitas preguntas.

Después se revisa a mano: un modelo inventa fechas y atribuciones con seguridad.

## Antes de publicar

- [ ] La respuesta correcta es **una sola** y no depende de una interpretación.
- [ ] Los distractores son del mismo tipo y plausibles; nada de “todas las anteriores”.
- [ ] El enunciado no necesita contexto externo (“según el texto…”) y entra en 300 caracteres.
- [ ] Español neutro, tildes y signos correctos; opciones sin explicaciones adentro.
- [ ] La dificultad es coherente con las semilla (1: cultura general, 5: especializado).
- [ ] No hay otra pregunta con el mismo enunciado normalizado.
- [ ] El dato no caduca (evitá “actualmente”, récords o cargos vigentes).
- [ ] `source` y `tags` ayudan a encontrarla después.
