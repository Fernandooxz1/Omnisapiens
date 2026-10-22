# Diseño — Sección de juegos (v1: Murdoku)

> Spec técnica y visual de la sección `/juegos`. Es la fuente de verdad del
> diseño; los prompts de fase la citan por sección. Los tokens reales viven en
> `frontend/src/app.css`; este documento explica el porqué y fija los contratos.

## 1. Objetivo y alcance

La sección de juegos es **otra cosa** que los modos de trivia: no hay sala, no
hay oponente, no hay reloj del servidor y no hay puntaje competitivo.

- **v1:** Murdoku, 62 casos, seis niveles, progreso local.
- **Sin backend:** los casos son datos estáticos del frontend y el progreso vive
  en `localStorage`. No se agrega ningún endpoint, tabla ni migración.
- **Sin cuenta:** jugar no requiere nick ni token. El nick sigue siendo solo
  para trivia y ranking.
- **Temporizador local:** es un cronómetro de la partida, no una marca
  autoritativa. Por eso no se publica ranking de juegos.
- **Preparado para más juegos:** el hub y el catálogo leen un registro
  (`src/lib/games/catalog.ts`); sumar Sudoku después es registrar otro juego.

Fuera de alcance: Sudoku en v1, Nonogram, multijugador, editor de casos, caso
diario, cuentas, sincronización en la nube, ranking de juegos y cualquier cambio
en `backend/`.

## 2. Rutas y navegación

```
/juegos                       → hub de juegos (tarjetas)
/juegos/murdoku               → catálogo de casos, filtros y progreso
/juegos/murdoku/[case]        → partida de un caso
```

- El adapter estático usa `fallback: index.html`; los deep links funcionan.
- Un juego o caso desconocido muestra un estado con volver al catálogo, no
  rompe la ruta.
- Los datos de un juego se importan de forma diferida desde el hub: el inicio
  no carga el catálogo.

### Tab bar

Barra inferior fija con tres destinos:

```
Inicio  ·  Juegos  ·  Ranking
```

- Visible en `/`, `/juegos*` (hub y catálogo) y `/ranking`.
- **Oculta** en `/play/*`, `/room/*`, `/admin/*` y `/juegos/murdoku/[case]`.
  En la partida se vuelve al catálogo con el botón de volver del header.
- El contenido reserva espacio inferior:
  `padding-bottom: calc(var(--tabbar-h) + env(safe-area-inset-bottom) + var(--s-4))`.
- Activo: icono y label en `--accent`, con una barra inferior de 3 px. Sin
  degradados.
- El link de ranking del final del home se elimina: la tab bar pasa a ser el
  único acceso persistente.

### Shell

`frontend/src/app.css` define `.shell` con 480 px. La sección de juegos agrega:

| Clase | Ancho máximo | Uso |
|---|---|---|
| `.shell` | 480 px | Home, ranking, admin |
| `.shell--wide` | 960 px | `/juegos` y `/juegos/murdoku` |
| `.shell--play` | 1100 px | `/juegos/murdoku/[case]` en desktop |

En móvil todas usan el ancho disponible con el padding habitual. El layout
decide la clase según `page.url.pathname`.

## 3. Reglas de Murdoku

El tablero es una grilla de `N × N`, con `N` entre 5 y 15.

1. Hay **N−1 sospechosos y 1 víctima**: N personas en total.
2. Cada persona ocupa exactamente una celda.
3. Hay exactamente una persona por fila y una por columna.
4. La víctima tiene una celda fija y visible; su fila y su columna quedan
   ocupadas por ella.
5. Cada sospechoso tiene **una o dos pistas** en su tarjeta. Todas las pistas
   son verdaderas.
6. Las regiones (habitaciones) agrupan celdas contiguas. Las pistas pueden
   referirse a una región, a una dirección, a otro sospechoso o a un objeto.
7. El **asesino** es el único sospechoso que comparte la región de la víctima.
   La solución del tablero debe dejar exactamente un sospechoso en esa región.
8. La solución es **única** y se deduce sin adivinar.

Los objetos (estantería, piano, planta, etc.) son anclas de pistas: no bloquean
la colocación. El generador evita poner un objeto en la celda de una persona en
la solución, para que el tablero resuelto se lea limpio.

La tarjeta de la víctima es fija: **"La víctima. Estaba a solas con el
asesino."** No es una pista más y no se usa para deducir la posición de nadie.

## 4. Escala de dificultad

La dificultad la manda el tamaño. El nivel es un dato explícito del caso, no una
consecuencia automática del tamaño, para poder tener 7×7 fáciles y medios.

| Tamaño | Nivel | Casos v1 | Pistas | Minutos aprox. |
|---|---|---|---|---|
| 5×5 | Muy fácil | 6 | 4 | 3 |
| 6×6 | Fácil | 8 | 5 | 4 |
| 7×7 | Fácil | 6 | 6 | 6 |
| 7×7 | Medio | 6 | 7–8 | 7 |
| 8×8 | Medio | 8 | 8–9 | 8 |
| 9×9 | Medio | 10 | 9–10 | 10 |
| 9×9 | Difícil | 4 | 10–11 | 12 |
| 10×10 | Difícil | 6 | 10–12 | 14 |
| 12×12 | Muy difícil | 4 | 12–14 | 20 |
| 14×14 | Hardcore | 2 | 15–17 | 28 |
| 15×15 | Hardcore | 2 | 16–18 | 32 |

**Total: 62 casos.** Cada sospechoso aporta al menos una pista; por eso el piso
es N−1. Las pistas extra se agregan solo cuando hacen falta para dejar la
solución única. El rango de la tabla es orientativo: si un caso grande necesita
más, se permiten hasta dos pistas por sospechoso. Nunca se publica un caso
ambiguo para respetar el número de pistas.

### Cómo se decide el nivel

- 5×5 → `very_easy`.
- 6×6 → `easy`.
- 7×7 → `easy` o `medium` según complejidad.
- 8×8 → `medium`.
- 9×9 → `medium` o `hard` según complejidad.
- 10×10 → `hard`.
- 12×12 → `very_hard`.
- 14×14 y 15×15 → `hardcore`.

Complejidad inicial (se puede calibrar en la tarea 2.2/2.3):

```
+1 por cada pista negativa (notRegion, notSameRegion)
+1 por cada dirección de 2+ casillas
+1 por cada diagonal
+1 por cada sameRegion / notSameRegion
+1 si el total de pistas supera N−1+2
```

- 7×7: complejidad ≤ 2 → fácil; ≥ 3 → medio.
- 9×9: complejidad ≤ 3 → medio; ≥ 4 → difícil.

Si un caso no cae en el nivel que le corresponde por tamaño, se regenera. Nunca
se publica un caso ambiguo para completar el cupo: si un tamaño no llega al
número objetivo, el catálogo muestra el conteo real.

## 5. Modelo de datos

Los tipos viven en `frontend/src/lib/games/` y no importan Svelte.

```ts
export type GameId = 'murdoku';

export type DifficultyKey =
  | 'very_easy'
  | 'easy'
  | 'medium'
  | 'hard'
  | 'very_hard'
  | 'hardcore';

export interface Cell {
  row: number;
  col: number;
}

export interface GameMeta {
  id: GameId;
  route: string;
  titleKey: MessageKey;
  blurbKey: MessageKey;
  icon: IconName;
  accent: 'green' | 'blue' | 'yellow' | 'orange' | 'red' | 'purple';
  order: number;
}

export interface CaseMeta {
  id: string;                 // "murdoku-001"
  game: GameId;
  number: number;             // 1..62
  title: string;              // "El estudio"
  setting: string;            // "Una mansión a medianoche"
  difficulty: DifficultyKey;
  size: number;               // 5..15
  estimatedMinutes: number;
  tutorial?: boolean;         // solo el primer 5×5
}

/** Datos mínimos para dibujar un sobre antes de cargar el caso completo. */
export interface CasePreview {
  meta: CaseMeta;
  regions: number[][];
  victim: Cell;               // la víctima es pública; los sospechosos no
}

export interface MurdokuCase extends CaseMeta {
  game: 'murdoku';
  grid: {
    size: number;
    regions: number[][];      // region id por celda [row][col]
    regionList: MurdokuRegion[];
    props: MurdokuProp[];
  };
  suspects: MurdokuSuspect[];
  victim: {
    name: string;
    row: number;
    col: number;
  };
  solution: Record<string, Cell>;  // suspect id → celda
  killer: string;                  // suspect id; se valida, no se muestra antes de resolver
  meta: {
    seed: number;
    clueCount: number;
    negatives: number;
    complexity: number;
    generatedBy: string;
  };
}

export interface MurdokuRegion {
  id: number;
  name: string;               // "Biblioteca"
  tone: number;               // 0..5, elige un tinte neutro
}

export interface MurdokuProp {
  id: string;
  name: string;               // "estantería"
  icon: PropIcon;             // nombre del SVG
  row: number;
  col: number;
}

export interface MurdokuSuspect {
  id: string;
  name: string;               // "Blake"
  initial: string;            // única en el caso
  color: 'green' | 'blue' | 'yellow' | 'orange' | 'pink' | 'purple' | 'red';
  clues: Clue[];              // 1..2
}
```

### Pistas

Las pistas se guardan como AST, no como texto. El solver las evalúa y la UI las
traduce desde `es.json`.

```ts
export type Clue =
  | { type: 'region'; who: string; region: number }
  | { type: 'notRegion'; who: string; region: number }
  | { type: 'direction'; who: string; dir: 'N' | 'S' | 'E' | 'W'; steps: number; than: string }
  | { type: 'adjacent'; a: string; b: string; diagonal: boolean }
  | { type: 'sameRegion'; a: string; b: string }
  | { type: 'notSameRegion'; a: string; b: string }
  | { type: 'nearProp'; who: string; prop: string }
  | { type: 'rowEdge'; who: string; edge: 'top' | 'bottom' }
  | { type: 'colEdge'; who: string; edge: 'left' | 'right' };
```

Semántica:

- `N`/`S`/`E`/`W`: fila menor/mayor, columna mayor/menor. `steps` ≥ 1.
- `adjacent` sin diagonal: las 4 celdas ortogonales. Con diagonal: las 8.
- `nearProp`: ortogonalmente adyacente al objeto. Estar en la misma celda no
  cuenta.
- `rowEdge`/`colEdge`: fila 0 / fila N−1; columna 0 / columna N−1.
- `sameRegion`/`notSameRegion`: comparan la región de las dos celdas.

Render en español neutro (sin voseo, sin emojis):

| Tipo | Texto en la tarjeta |
|---|---|
| `region` | Estaba en {región}. |
| `notRegion` | No estaba en {región}. |
| `direction` | Estaba {una/dos/tres} casilla(s) al {norte/sur/este/oeste} de {nombre}. |
| `adjacent` | Estaba junto a {nombre}. / Estaba en diagonal con {nombre}. |
| `sameRegion` | Compartía habitación con {nombre}. |
| `notSameRegion` | No compartía habitación con {nombre}. |
| `nearProp` | Estaba junto a {objeto}. |
| `rowEdge` | Estaba en la fila de arriba/abajo. |
| `colEdge` | Estaba en la columna de la izquierda/derecha. |

Cuando la pista es del propio sospechoso, no se repite el nombre: "Estaba en la
biblioteca", no "Blake estaba en la biblioteca".

### Progreso

```ts
export interface GameProgress {
  version: 1;
  cases: Record<string, {
    solved: boolean;
    bestMs: number | null;
    lastMs: number | null;
    hints: number;            // pistas usadas en la última resolución
    solvedAt: string | null;  // ISO
    lastPlayedAt: string | null;
    resume: {
      placements: Record<string, Cell>;
      marks: string[];        // "r,c"
      elapsedMs: number;
      hintsUsed: number;
      updatedAt: string;
    } | null;
  }>;
}
```

- Clave: `omnisapiens.games.v1`.
- Parseo defensivo: si `version !== 1`, se descarta y se arranca vacío. Los
  casos desconocidos se ignoran. Un JSON roto no rompe la pantalla.
- `resume` se guarda con debounce de 300 ms y se borra al resolver.
- Si el navegador limpia el storage, se pierde el progreso. Es aceptado en v1.

## 6. Arquitectura del frontend

```
src/lib/games/
  types.ts                  → GameId, DifficultyKey, Cell, CaseMeta, GameMeta
  catalog.ts                → registro de juegos (murdoku)
  difficulty.ts             → orden, labels, colores, conteos
  progress.svelte.ts        → localStorage y estado reactivo
  components/
    GameCard.svelte
    CaseEnvelope.svelte
    DifficultyChips.svelte
    PuzzleHeader.svelte     → volver, título, dificultad, timer
    PuzzleToolbar.svelte    → X, deshacer, pista, reiniciar
    CaseFile.svelte         → pistas y sospechosos (rail o sheet)
  murdoku/
    types.ts
    rules.ts                → predicados de pistas + asesino
    solver.ts               → backtracking + unicidad
    validate.ts             → validación de catálogo
    generate.ts             → generador offline
    engine.ts               → estado puro de la partida
    engine.svelte.ts        → runas, timer, persistencia
    fixtures.ts             → previews 5×5, 9×9 y 15×15; luego 2 casos reales
    cases/
      standard.ts           → 5×5 a 9×9
      large.ts              → 10×10 a 15×15
      index.ts              → allCases, findCase, byDifficulty
    MurdokuBoard.svelte
    BoardViewport.svelte
    SuspectToken.svelte
    ClueCard.svelte

src/routes/
  juegos/+page.svelte
  juegos/[game]/+page.svelte
  juegos/[game]/[case]/+page.svelte

src/lib/components/TabBar.svelte
```

Reglas de capas:

- `engine.ts`, `rules.ts`, `solver.ts` y `generate.ts` son puros: no importan
  Svelte ni tocan `window`.
- `engine.svelte.ts` es la única capa con runas, timer y persistencia.
- Las pantallas no hablan con `localStorage` directamente: usan
  `progress.svelte.ts`.
- No hay `fetch` ni `WebSocket` en la sección.

## 7. Solver y generador

### Solver

- La víctima está fija en `(rv, cv)`. Los sospechosos solo pueden usar filas
  distintas de `rv` y columnas distintas de `cv`.
- Variables: los N−1 sospechosos. Dominio: celdas libres.
- Backtracking con:
  - máscaras de bits de filas y columnas usadas,
  - heurística MRV (el sospechoso con menos celdas posibles primero),
  - forward checking,
  - evaluación de pistas parciales cuando ya hay una variable asignada,
  - conteo de soluciones con tope 2 (basta para probar unicidad).
- La regla del asesino se evalúa al completar: exactamente un sospechoso en la
  región de la víctima.
- `solve(case, limit = 2)` devuelve hasta `limit` soluciones. `validateCase`
  exige exactamente 1.

### Generador

1. PRNG determinista (`mulberry32`) con semilla guardada en el caso.
2. Elegir N, una permutación válida para las N personas y una celda de víctima
   acorde al nivel (borde para fáciles, centro/aleatoria para difíciles).
3. Generar 4–6 regiones contiguas por crecimiento aleatorio desde semillas;
   cada región con nombre y 4–10 objetos temáticos en total. Ningún objeto
   comparte celda con una persona en la solución.
4. Enumerar pistas candidatas verdaderas sobre la solución (región, negación,
   dirección, adyacencia, misma región, objeto, borde).
5. Elegir una pista por sospechoso y agregar pistas extra con selección greedy
   hasta que el solver cuente una sola solución.
6. Eliminar pistas extra redundantes sin romper la unicidad, conservando
   siempre una por sospechoso.
7. Validar: solución única, todas las pistas verdaderas, asesino correcto,
   iniciales únicas, regiones y objetos válidos.
8. Calcular complejidad y nivel; si no coincide con el objetivo, reintentar con
   otra semilla (tope de intentos).
9. Escribir el caso en `cases/standard.ts` o `cases/large.ts`, ordenado por
   número.

### Rendimiento

- 5×5 a 9×9: 48 casos. Generación interactiva para el batch; validación en
  segundos.
- 10×10 a 15×15: 14 casos. Batch offline. Objetivo: menos de 60 s por caso de
  15×15 y menos de 10 min para los 14 casos grandes.
- Si un caso no se puede validar dentro del presupuesto, no se publica. El
  catálogo muestra el conteo real y la tarea 2.3 reporta el faltante.

### Scripts

En `frontend/package.json`:

```json
{
  "scripts": {
    "games:generate": "node scripts/games/generate-murdoku.ts",
    "games:validate": "node scripts/games/validate-murdoku.ts",
    "test:games": "node --test src/lib/games"
  }
}
```

Node 26 ejecuta TypeScript nativo. Los módulos puros se importan con extensión
`.ts` en tests y scripts; si `svelte-check` se queja, se habilita
`allowImportingTsExtensions` en `tsconfig.json`. Los scripts aceptan
`--size`, `--count`, `--difficulty`, `--seed`, `--all` y `--id`.

Argumentos mínimos:

- `npm run games:generate -- --max-size 9`
- `npm run games:generate -- --min-size 10`
- `npm run games:validate -- --all`
- `npm run games:validate -- --id murdoku-001`

## 8. Catálogo de casos

### Hub `/juegos`

- Título "Juegos" y una línea de contexto.
- Tarjeta de Murdoku con icono, nombre, descripción, "62 casos" y progreso.
- La tarjeta es un enlace completo; en el futuro se agregan más tarjetas sin
  tocar la home.

### Catálogo `/juegos/murdoku`

- Header con volver, título, descripción y resumen de progreso
  ("12 de 62 resueltos").
- Chips horizontales: `Todo` + los seis niveles, con conteo.
- Con `Todo`, los sobres se agrupan por nivel, con un encabezado por sección y
  su conteo. Con un nivel elegido, se muestra solo esa sección.
- Grid de sobres: 2 columnas en móvil, 3 desde 720 px, 4 desde 1000 px.
- Orden por número de caso. Sin bloqueos: todos los casos están disponibles.
- Estado del sobre: `sin abrir`, `en curso`, `resuelto` + mejor tiempo.
- Un caso con `resume` muestra "Continuar" en el sobre.
- Deep link directo al caso.

### Sobre de caso (`CaseEnvelope.svelte`)

No copia la UI de Murdoku. Toma la metáfora del sobre y la resuelve con nuestros
tokens.

- Cuerpo: `--panel-bg`, radio 24 px, base sólida `0 6px 0 --panel-edge`.
- Solapa: triángulo SVG en un tono más oscuro del panel, borde de 2.5 px y
  línea de pliegue. Al hover/focus se levanta 2 px y el sello gira a 0°.
- Mini-vista: muestra las regiones del caso en una grilla de 4×4 o 5×5 muestreada
  de `regions` (el preview) o de `grid.regions` (el caso completo), con la
  víctima marcada. Es dato del caso, no una ilustración. **Nunca muestra la
  posición de los sospechosos**: eso revelaría la solución.
- Sello: círculo de 36–40 px con el número de caso, color según dificultad y
  base sólida. Rotación de -6°.
- Etiqueta: título, dificultad, `N×N`, estado y mejor tiempo.
- Accesible como un único enlace con nombre "Caso 12, El estudio, Medio, 9×9,
  sin resolver".
- Sin retratos: los sospechosos son tokens con inicial; no se copian las
  ilustraciones ajenas.

Colores de dificultad:

| Nivel | Color | Tinta |
|---|---|---|
| Muy fácil | `--green` | blanca |
| Fácil | `--blue` | blanca |
| Medio | `--yellow` | `#3F2D00` |
| Difícil | `--orange` | blanca |
| Muy difícil | `--red` | blanca |
| Hardcore | `--purple` | blanca |

## 9. Tablero y pantalla de partida

### Tablero

- Grilla CSS `repeat(var(--size), 1fr)` con `aspect-ratio: 1`.
- Tintes de región (agregar a `app.css` en la tarea 3.2):

```css
--region-1: #221E33;
--region-2: #2A2438;
--region-3: #1F2633;
--region-4: #242B31;
--region-5: #2B2530;
--region-6: #231F2C;
--region-line: #4A4463;
```

- Las regiones se distinguen por **tinte + borde grueso + etiqueta/leyenda**, no
  solo por color.
- Para 5×5 a 9×9, etiqueta corta en la primera celda de la región. Para 10×10 a
  15×15, número de región y leyenda en el expediente.
- Objetos: SVG propio al 55 % de opacidad. Si una persona cae en la misma celda
  (no debería pasar en la solución), el token la tapa.
- Víctima: token "V" con borde de peligro y sin interacción.
- Sospechoso colocado: token con inicial, color de familia y base sólida.
- Marca X: icono `x` en `--ink-3`.
- Selección: anillo `--accent` de 3 px.
- Conflicto: anillo `--danger-ring` y sacudida corta; no se permite una segunda
  persona en la misma fila o columna.

### BoardViewport

- Para 5×5 a 9×9: modo "ajustar" por defecto; celdas entre 40 y 56 px.
- Para 10×10 a 15×15: modo "ajustar" con celdas de ~28–32 px y controles de
  zoom `-` / `+` (32, 40, 48 px) con desplazamiento.
- Contenedor con scroll en ambos ejes cuando el zoom supera el ancho.
- Teclado: la celda enfocada se hace visible con `scrollIntoView({ block:
  'nearest', inline: 'nearest' })`.
- En móvil, el tablero queda sticky arriba y el expediente se desplaza debajo.

### Layout de la partida

Desktop (≥ 900 px):

```
[ header: volver · caso · dificultad · timer ]
[ tablero                         ] [ expediente ]
                                     sospechosos
                                     pistas
                                     herramientas
```

Móvil:

```
[ header ]
[ tablero sticky ]
[ solapas: Sospechosos | Pistas ]
[ herramientas ]
[ comprobar ]
```

- El expediente muestra las tarjetas de sospechosos con su pista y la víctima.
- En móvil, las solapas permiten cambiar entre sospechosos y pistas sin perder
  el tablero de vista.
- Herramientas: marcar X, deshacer, pista, reiniciar. `Comprobar` se habilita
  cuando todos los sospechosos están colocados.

### Partida

- El timer arranca con la primera acción (colocar, marcar o usar una pista), no
  al abrir la página. Se pausa cuando la pestaña queda oculta y se reanuda al
  volver.
- Colocar un sospechoso en otra celda lo mueve; deshacer restaura la posición
  anterior.
- Colocar limpia las X de esa fila y columna (y la de la celda), con deshacer.
- Pista: revela la celda correcta de un sospechoso mal ubicado o sin ubicar;
  incrementa `hintsUsed`.
- Comprobar: si falta gente, no hace nada. Si está completo y alguna pista no
  se cumple, muestra "Algo no cierra" y sacude el tablero sin decir qué pista
  falla. Si es correcto, revela al asesino.
- Victoria: nombre del asesino, región, tiempo, pistas usadas, "Siguiente caso"
  y "Volver al catálogo". Confetti solo si es el primer caso resuelto o si hay
  nuevo mejor tiempo. Sonido y haptics reutilizan los módulos existentes.
- El caso tutorial (5×5) muestra un panel "Cómo jugar" de 3 pasos; no cambia el
  motor.

## 10. Accesibilidad

- Grilla con roles `grid`, `row` y `gridcell`; cada celda tiene `aria-label`
  con fila, columna, región, ocupante o marca.
- Flechas mueven el foco; `Enter` coloca al sospechoso seleccionado; `X` alterna
  el modo marca; `Backspace` borra; `Ctrl/Cmd+Z` deshace; `H` pide pista.
- La bandeja de sospechosos se recorre con `Tab` y flechas; `1–9` selecciona los
  primeros nueve; `0` el décimo; los demás con flechas.
- `aria-live="polite"` para "Blake colocado en fila 3, columna 4", conflictos y
  caso resuelto.
- Contraste AA; foco visible; blancos táctiles ≥ 44 px salvo el modo ajustar de
  tableros grandes, donde se ofrece zoom.
- `prefers-reduced-motion`: sin sacudidas, sin apertura de solapa y sin
  confetti.

## 11. Contenido y tono

- 12 escenarios base: estudio, biblioteca, invernadero, cocina, museo, tren,
  faro, teatro, laboratorio, mansión, mercado y escuela.
- Cada escenario aporta nombres de regiones y objetos; los títulos de caso son
  únicos.
- Español neutro, sin voseo, sin emojis y sin violencia explícita. El crimen es
  estilizado, de novela de misterio.
- Las pistas no pueden revelar directamente al asesino ni decir "a solas con la
  víctima" en una tarjeta de sospechoso.
- Evitar pistas tautológicas o ambiguas. El validador comprueba verdad y
  unicidad; la curaduría (tarea 2.4) revisa naturalidad.

## 12. Verificación

Cada tarea de código corre:

```bash
cd frontend && npm run check && npm run build
```

Las tareas de dominio agregan:

```bash
npm run test:games
npm run games:validate -- --all
```

Las tareas de pantalla agregan la e2e correspondiente:

```bash
npm run test:e2e
```

La suite e2e debe cubrir, como mínimo:

1. Hub → catálogo → abrir un caso por sobre.
2. Filtros por dificultad y conteos.
3. Tutorial 5×5 resuelto con teclado o clics.
4. Caso 9×9: colocar, marcar X, deshacer y usar pista.
5. Caso 15×15: abrir, hacer zoom y colocar un sospechoso (smoke de viewport).
6. Progreso: resolver, volver al catálogo y ver el sobre como resuelto.
7. Deep link directo a un caso.

Revisión visual en 390 px, 768 px y 1280 px.

## 13. Riesgos y decisiones

| Riesgo | Mitigación |
|---|---|
| Generación de 14×14/15×15 demasiado lenta | Solver con MRV y poda; presupuesto de tiempo; menos casos antes que casos ambiguos |
| Tablero denso en móvil | Modo ajustar + zoom con scroll; tablero sticky; tokens con inicial |
| Pistas generadas poco naturales | Plantillas curadas + revisión manual de los 62 casos en 2.4 |
| Dos columnas de sobres con títulos largos | Títulos cortos en el sobre; escenario completo en la pantalla del caso |
| Pérdida de progreso al limpiar el navegador | Aceptado en v1; `progress.ts` aislado para sincronizar después |
| La solución viaja en el bundle estático | Aceptado: no hay ranking ni puntaje competitivo. Si se agrega ranking, la validación se mueve al backend |
| Nombre "Murdoku" de terceros | El id interno queda `murdoku`; el nombre visible es una clave de i18n y se puede cambiar |
| Choque con la regla de "servidor autoritativo" | No hay ranking ni puntaje competitivo; el timer es local y no se publica |

## 14. Fuera de alcance

Sudoku, Nonogram, Kakuro, ranking de juegos, cuentas, nube, multijugador,
editor, importación CSV, caso diario, notificaciones, monetización y cambios en
`backend/`.
