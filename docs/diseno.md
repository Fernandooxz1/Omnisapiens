# Sistema de diseño

> Cómo se ve y se siente Omnisapiens. Se consulta al construir cualquier pantalla.
> Los tokens de `frontend/src/app.css` son la fuente de verdad; este documento explica el porqué.

## Un solo estilo

La app tiene **un estilo**: pizarra cálida, relleno liso y base sólida. No hay variantes de
color ni temas alternativos; lo que cambia es el **acento** del jugador.

| | **Pizarra cálida** |
|---|---|
| Idea | Preguntados: botones gruesos de maquinita sobre un tablero oscuro y cálido |
| Fondo | plano `#191724` con textura de puntos: **no** hay luz difusa ni degradado de relleno |
| Superficie | panel `#2E2A42` con base sólida `0 6px 0 #181524`; sombra dura de texto `#12101B` |
| Profundidad | bisel de luz arriba (`inset 0 2px 0 rgb(255 255 255 / .28)`) + base dura del color del filo |
| Radios | `24` paneles · `20` botones · `18` respuestas y pozos · `14` pastillas |
| Tamaños | botón de modo 78 px · paso siguiente flotante 64 px · respuesta ≥ 48 px (crece hasta 62 px) · táctiles ≥ 44 px |
| Texto | mayúsculas en botones y badges · `Plus Jakarta Sans` + `Fredoka` |
| Tiles de respuesta | **teclas blancas chatas**, una por fila, con la tecla `1`–`4` en un keycap a la izquierda |
| Extras | sello del logo, tarjeta de perfil con avatar y swatches, marcador abierto con corona |

**Las reglas de abajo no se negocian:**

- **Cero emojis.** Todos los íconos son SVG propios (grid 24, trazo 2.5, `currentColor`).
- **Cero degradados de color.** Ni de fondo, ni de tarjeta, ni de botón. El volumen sale del
  bisel interior y de la base sólida; un relleno que va de claro a oscuro está prohibido.
  La única textura permitida es el **patrón de puntos** del tablero (un solo color al 4 %,
  no un degradado).
- **Botones grandes, nunca píldora**: geometría squircle (`20px` el botón, `18px` la
  respuesta, `24px` el panel; `999px` solo en pastillas y badges chicos).
- **Al presionar** el elemento se hunde: baja 4 px (botón) o 3 px (tile) y la base sólida se
  reduce en la misma proporción. Sin rebotes largos.
- **Campos y contadores van hundidos** (pozo con sombra interna oscura), nunca con volumen
  hacia afuera.
- La **tipografía se elige**, no se hereda. Nada de `system-ui` como fuente principal.
- **Cero animaciones de entrada por scroll**: se anima el feedback (press, reveal, acierto).
  Tampoco hay animaciones en loop: el pulso del reloj solo aparece en los últimos 5 s.
- **Accesibilidad mínima**: foco visible, contraste AA, blancos táctiles ≥ 44 px, todo
  jugable con teclado (`1`–`4` responde, `Enter` confirma).
- **Sin scroll en la pantalla de partida**; en el resto, columna máx. 480 px.

## Paleta

```css
:root {
  --page-bg: #191724;  --card-bg: #232033;  --card-edge: #12101B;
  --panel-bg: #2E2A42; --panel-edge: #181524;
  --well-bg: #181523;  --well-border: #3B3654;
  --veil-bg: rgb(25 23 36 / .66);   /* velo del paso siguiente flotante */
  --ink: #FFFFFF; --ink-2: #D8D2E8; --ink-3: #9B94B8;

  --green: #1EC765;  --green-edge: #13964B;
  --blue: #0098E6;   --blue-edge: #006BB3;
  --yellow: #FFC800; --yellow-edge: #D69E00;
  --orange: #FF7800; --orange-edge: #CC5600;
  --pink: #EC388B;   --pink-edge: #B51B63;
  --purple: #9338C6; --purple-edge: #6A1E96;
  --red: #E62514;    --red-edge: #AD1407;

  --font-ui: 'Plus Jakarta Sans', system-ui, sans-serif;
}
```

Cada familia tiene **cuerpo y filo**: el cuerpo rellena (botón, badge, avatar) y el filo es la
base sólida de 5–6 px y el `text-shadow`. Un color, un uso; nunca se cruzan.

### Quién usa cada color

- **Verde** — CTA y modo principal (arcade), el acierto al revelar y `science`.
- **Azul** — modo secundario (1v1), el esticker "respondes" y `geography`.
- **Amarillo** — el sello del logo (`sapiens`), la corona del que va ganando, la ronda en
  curso y `history`. Lleva **tinta oscura** (`#3F2D00`) en el badge: blanco sobre amarillo
  no llega a AA.
- **Naranja** — el rival en el marcador y `sports`.
- **Rosa** — `entertainment`. **Rojo** — el fallo al revelar y `art`.
- **Violeta** — solo como acento elegible del jugador.
- **Pizarra** (`--well-border`/`#201C30`) — controles neutros (`slate`).

### Acento del jugador

El jugador no elige un tema, elige **su color**: `AccentPicker` escribe `data-accent`
(`blue` · `green` · `orange` · `pink` · `purple`) sobre `<html>` y lo recuerda en
`localStorage` (clave `omni-accent`, ver `src/lib/accent.ts`). Los tokens `--accent` y
`--accent-edge` salen de ahí y pintan **solo el avatar propio** (perfil y marcador). El
`app.html` lo resuelve antes del primer pintado para que no parpadee.

## Forma y tipografía

```css
:root {
  --r-sm: 10px; --r-md: 14px; --r-lg: 24px; --r-key: 20px; --r-tile: 18px;
  --border-w: 2.5px; --depth-key: 6px;
  --key-h: 78px; --key-h-sm: 64px;   /* botón de modo · paso siguiente flotante */
  --s-1: 4px; --s-2: 8px; --s-3: 12px; --s-4: 16px; --s-5: 24px; --s-6: 32px; --s-7: 48px;
  --font-display: 'Fredoka', system-ui, sans-serif;
}
```

`--font-display` (títulos, botones, marcador, números) es **Fredoka**, siempre. La UI usa
`Plus Jakarta Sans`. Fuentes autoalojadas en `frontend/static/fonts/` (woff2,
`font-display: swap`). **Presupuesto:** ≤ 250 KB de JS.

## Botón "juicy"

```css
.btn {
  --key-bg: var(--green); --edge: var(--green-edge);
  display: flex; flex-direction: column; align-items: flex-start; justify-content: center; gap: 3px;
  width: 100%; min-height: 78px; padding: 15px 20px;
  border: none; border-radius: var(--r-key);                 /* 20 px, nunca píldora */
  background: var(--key-bg);                                 /* relleno liso, sin degradado */
  box-shadow:
    inset 0 2px 0 rgb(255 255 255 / .28),
    0 6px 0 var(--edge), 0 10px 18px -6px rgb(0 0 0 / .5);
  color: #FFF;                                               /* título BLANCO */
  text-shadow: 0 2px 0 var(--edge);
  cursor: pointer;
  transition: transform .07s cubic-bezier(.34,1.56,.64,1), box-shadow .07s ease, filter .15s ease;
}
.btn:hover  { filter: brightness(1.06); transform: translateY(-1px); }
.btn:active { transform: translateY(4px);                     /* se hunde casi toda la base */
  box-shadow: inset 0 1px 0 rgb(255 255 255 / .16), 0 2px 0 var(--edge); }
.btn:disabled { filter: grayscale(.5) opacity(.55); cursor: not-allowed; }
```

El botón lleva **dos líneas**: título en mayúsculas (Fredoka `1.3rem`) y subtítulo descriptivo
(`Plus Jakarta Sans`, `0.82rem`). Variantes: `green` (acento/CTA) · `blue` (secundario) ·
`slate` (neutro). Con la prop `aside` se convierte en fila y acepta una **pastilla a la
derecha** (las tres vidas del arcade, el `VS` del duelo). El `:focus-visible` es
`outline: 3px solid #FFF`.

## Logo y perfil

El sello del inicio es una pastilla naranja inclinada 2° arriba del wordmark; el wordmark va
en dos tonos (`Omni` blanco con sombra dura, `sapiens` amarillo con filo) y debajo, la
bajada en `--ink-3`.

La **tarjeta de perfil** es un panel `--r-lg` con el `NickInput` adentro (avatar a la
izquierda dentro del pozo, badge verde de check a la derecha) y, debajo, los **swatches** del
acento: cuadrados de 26 px centrados en un botón de 44 px, el elegido sube 2 px y se escala.

## Input hundido (pozo)

Campos de texto y contadores no tienen volumen hacia afuera: parecen cavados en el tablero.
Fondo `--well-bg`, borde `2px solid --well-border`, radio `18px` y
`box-shadow: inset 0 4px 0 rgb(0 0 0 / .45)`. A la derecha, el badge de validación es un
squircle verde de 34 px con relieve propio (`inset 0 2px 0 rgb(255 255 255 / .4)`,
`0 3px 0 var(--green-edge)`) y un check SVG adentro.

## Respuestas (teclado mecánico)

Las cuatro opciones van **en una columna**: una tecla por fila, y la columna se reparte el
alto libre de la pantalla (`min-height: 48px`, `max-height: 62px`). Son teclas **bajas** y
anchas: blancas (`#F8FAFC`), sin borde, radio 18 px y una base de 4 px; el volumen es chato,
un bisel de luz arriba (`inset 0 3px 0 #FFF`) y **sin sombra proyectada**. El número `1`–`4`
vive en un **keycap** de 26×26 px a la izquierda, con su propio relieve (`0 2px 0 #CBD5E1`) y
el número en azul. La etiqueta (`1.1rem`) va centrada para que **no se mueva** cuando
aparecen las marcas.

Lo único que cambia entre estados es el **color**: elegido = borde azul, acierto = **verde**,
fallo = **rojo** con una sacudida horizontal de `0.36s`. El cuerpo es el mismo en los tres
(relleno liso, bisel de luz y base de 4 px del filo), así que la tecla no cambia de forma al
revelarse; en acierto y fallo el texto pasa a blanco.

## Marcador abierto y pastillas

El **marcador** no lleva caja: avatar, nick y puntos flotan sobre el tablero a cada lado y
en el medio van las **cápsulas de ronda** o el `vs`. El reloj es una **pastilla** con ícono
de reloj sobre `ends_at`; en los últimos 5 s se pinta rojo y late. Debajo del marcador corre
la **barra de tiempo** (verde → amarillo → rojo) como cuenta atrás visual.

## Componentes

| Componente | Notas |
|---|---|
| `Button` | `green/blue/slate` · dos líneas (título + subtítulo) · 78 px · press de 4 px · `aside` opcional a la derecha · variante flotante del paso siguiente: 64 px |
| `AccentPicker` | swatches del acento del jugador; escribe `data-accent` y `localStorage` (clave `omni-accent`) |
| `Avatar` | squircle 44 px con la inicial; acento propio o naranja del rival; corona al que va ganando |
| `CategoryBadge` | pastilla `--r-full` con color `--cat-*` + etiqueta de `es.json` |
| `AnswerTile` | idle/selected/correct/wrong/dim · una por fila · keycap `1`–`4` · **misma forma en todos los estados**, solo cambia el color |
| `QuestionCard` | panel con la pastilla de categoría **centrada sobre el borde** y esticker "Responde" flotante a la derecha |
| `NickInput` | 1–16, pozo hundido, badge de check, snippet `prefix` para el avatar |
| `TimerBadge` | pastilla con reloj sobre `ends_at`; late y se pinta rojo en los últimos 5 s, se apaga fuera del turno |
| `PlayerPanel` | nick, estado conectado/desconectado, puntos |
| `Scoreboard` | **abierto** (sin caja): avatar + nick + puntos a cada lado, `vs` en el medio, corona al líder |
| `CodeInput` | 6 casillas, alfabeto sin `O/0/I/1`, pegado del código completo |
| `Modal` | fondo plano (sin blur), `Enter`/`Esc`, foco atrapado |
| `Toast` | errores de la API con `code` + `message` |
| `LifeStrip` | 3 vidas del arcade, se apagan con animación corta |

## Partida

- La **revelación** dura 2,5 s: la correcta, qué eligió cada jugador y los puntos. **No hay
  explicación de la respuesta**: el tablero queda limpio y se pasa a la ronda siguiente.
- La pausa la da el servidor antes de servir la próxima ronda; mientras no exista, la
  pantalla de partida no se cierra (`docs/api.md`).
- Mientras el rival no contestó, la elección propia queda bloqueada y marcada; nunca se
  insinúa si es correcta.
- Arriba van las **cápsulas de ronda** (ganada / perdida / en curso), la pastilla del reloj y,
  debajo del marcador, la **barra de tiempo**; la ronda también se anuncia para lectores de
  pantalla.
- Sobre todo eso, la **marca**: el wordmark del inicio, al mismo tamaño, centrado como cabecera.
- El **paso siguiente** flota al pie sobre un velo `--veil-bg` con `backdrop-filter: blur(7px)`
  (el único blur del sistema; no es un `Modal`) y entra con un fundido de `0.18s`. Está fuera
  del flujo: no empuja el tablero ni tapa una respuesta.
- El tablero se **centra** en el alto que deja libre el velo (`100dvh` menos los bordes del
  `shell` y el botón), con `min-height: min-content` como piso; la columna de respuestas se
  reparte ese alto entre 48 y 62 px. Así el aire sobra igual arriba y abajo y la partida nunca
  scrollea.
- Mientras no exista el cliente WS, `/play` se dibuja con datos de ejemplo de `src/lib/demo/`;
  esa carpeta se borra al conectar el servidor.

## Sonido

`tick`, `reveal`, `correct`, `wrong`, `match_start`, `match_win`, `match_lose`, `best_score`
en `frontend/static/assets/sfx/` (mp3/ogg, < 60 KB, CC0). Se inicializa tras la primera
interacción; el silencio se persiste en `localStorage`.

## Pantallas

Inicio · jugar (crear/unirse) · lobby · partida · revelación · fin · arcade · fin de arcade ·
ranking · admin. El contenido de cada una está en `docs/plan.md`.

## Accesibilidad y movimiento

- Foco visible siempre; orden de tabulación natural; `aria-live` para el resultado de ronda.
- Teclado: `1`–`4` elige, `Enter` confirma, `Esc` cierra modal.
- Contraste AA: texto blanco sobre los cuerpos de color con `text-shadow` para el filo; el
  badge de `history` usa tinta oscura sobre el amarillo.
- `prefers-reduced-motion`: sin pulso del reloj, sin rebote del botón, sin transición de tile.
