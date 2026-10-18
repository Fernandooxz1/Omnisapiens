# Sistema de diseño

> Cómo se ve y se siente Omnisapiens. Se consulta al construir cualquier pantalla.
> Referencias vivas: `frontend/design/referencia-botones.html` (botón) y
> `frontend/design/laboratorio_de_botones_juicy_ui_sheen.html` (lenguaje del estilo Colorido).

## Dos estilos

La app tiene **dos estilos completos**, no dos paletas: mismo layout, misma estructura de
componentes y **otra piel entera** (forma, sombras, tipografía, densidad, tono). El jugador
elige; el estilo vive en `data-skin` sobre `<html>` y se recuerda en `localStorage`. El cambio
es **inmediato** (la CSS lee variables de la piel, no hay markup distinto) y la piel se resuelve
en `app.html` antes del primer pintado para que no parpadee.

| | **Papel** (por defecto) | **Colorido** |
|---|---|---|
| Idea | Juguete de mesa: papel, tinta, teclas | Preguntados / Clash: botones gruesos de maquinita sobre un tablero oscuro |
| Fondo | papel cálido plano `#FCF8F0` | tablero pizarra `#222831` con viñeta radial desde `#2C3849` |
| Superficie | blanca, borde de tinta `2.5px`, sombra dura `4px 4px 0` | tarjeta `#2B323C` con base sólida `0 6px 0 #171C22`, panel `#363F4C` |
| Botón | borde de tinta, degradado leve, base dura de 6 px | sin borde, bisel interno, **radio 18 px y base sólida de 6 px** |
| Radial | `10` chips · `14` botones y tarjetas | `18` botones · `16` respuestas y campos · `22` paneles |
| Tamaños | `lg` 84 px · `md` 60 px | modo principal 78 px · modo secundario 78 px · tiles 60 px |
| Texto | frase normal, `Instrument Sans` + `Fredoka` | mayúsculas en botones/badges, `Plus Jakarta Sans` + `Fredoka` |
| Tiles de respuesta | teclas blancas con borde de tinta, tecla `1`–`4` a la izquierda | **teclas blancas y altas** (60 px), radio 16 px, base de 5 px y tecla `1`–`4` en el keycap |
| Acierto | verde, con la tecla pintada | verde, con la tecla pintada |
| Paleta de controles | azul (acción) · blanco (secundario) | **verde** (acción/arcade) · **azul** (secundario/1v1) · pizarra (neutro) |
| Extras | ninguno | destello diagonal en el modo principal, esticker sobre la pregunta, avatares en el marcador |

Ningún estilo se mezcla con el otro: los componentes comparten markup y se visten por
bloques `html[data-skin='…']`. **Sin librería de UI y sin Tailwind**: CSS propio.

**Las reglas de abajo no se niegan en ningún estilo:**

- **Cero emojis.** Todos los íconos son SVG propios (grid 24, trazo 2.5, `currentColor`).
- El **gradiente solo da volumen** a lo presionable (luz arriba, sombra abajo) o el brillo
  estático de un borde. Prohibido como decoración de fondos o tarjetas. Excepciones: la
  viñeta del tablero de Colorido y el destello del botón principal.
- **Botones grandes, nunca píldora**: geometría squircle (`18px` el botón, `16px` la
  respuesta, `22px` el panel).
- **Al presionar** el elemento se hunde: baja 4 px (botón) o 3 px (tile) y la base sólida se
  reduce en la misma proporción. Sin rebotes largos.
- **Campos y contadores van hundidos** (pozo con sombra interna oscura), nunca con volumen
  hacia afuera.
- La **tipografía se elige**, no se hereda. Nada de `system-ui` como fuente principal.
- **Cero animaciones de entrada por scroll**: se anima el feedback (press, reveal, acierto).
  Excepción única: el **destello en loop del botón del modo principal** de Colorido.
- **Accesibilidad mínima**: foco visible, contraste AA, blancos táctiles ≥ 44 px, todo
  jugable con teclado (`1`–`4` responde, `Enter` confirma).
- **Sin scroll en la pantalla de partida**; en el resto, columna máx. 480 px.

## Estilo Papel

```css
html[data-skin='papel'] {
  --ink: #101828; --ink-2: #344054; --ink-3: #667085;
  --bg: #FCF8F0; --surface: #FFFFFF; --surface-2: #F2EADF;
  --key-primary-top: #3D78FF; --key-primary-bottom: #2F6BFF; --key-primary-edge: #1E4FD1;
  --key-secondary-top: #FFFFFF; --key-secondary-bottom: #F5EEE2; --key-secondary-edge: #D8CCB8;
  --cat-geography: #2E9E5B; --cat-history: #C77B2E; --cat-science: #2A6FD6;
  --cat-art: #8A4FD3; --cat-entertainment: #E0498F; --cat-sports: #1E9E9E;
  --font-ui: 'Instrument Sans', system-ui, sans-serif;
}
```

El **texto del badge** depende del color: blanco en `science` y `art`, tinta en el resto. Los
pares exactos se fijan en los tokens (`--cat-*-ink`), no a ojo.

## Estilo Colorido

La paleta es la oficial de Preguntados: cada familia tiene luz, cuerpo y filo (la base sólida
del botón). Un color, un uso; nunca se cruzan.

```css
html[data-skin='colorido'] {
  --board-bg: #222831; --card-bg: #2B323C; --card-edge: #171C22;
  --panel-bg: #363F4C; --panel-edge: #1E232A;
  --well-bg: #1A1F26; --well-border: #3E4856;

  --green-top: #2CE67C; --green-bot: #1EC765; --green-edge: #13964B;
  --blue-top: #2BC0FF;  --blue-bot: #0098E6;  --blue-edge: #006BB3;
  --yellow-top: #FFE135; --yellow-bot: #FFC800; --yellow-edge: #D69E00;
  --orange-top: #FF9E2C; --orange-bot: #FF7800; --orange-edge: #CC5600;
  --pink-top: #FF66B2;   --pink-bot: #EC388B;   --pink-edge: #B51B63;
  --red-top: #FF5242;    --red-bot: #E62514;    --red-edge: #AD1407;

  --ink: #F8FAFC; --ink-2: #CBD5E1; --ink-3: #94A3B8;
  --font-ui: 'Plus Jakarta Sans', system-ui, sans-serif;
}
```

### Quién usa cada color

- **Verde** — CTA y modo principal (arcade), y el acierto al revelar. También `science`.
- **Azul** — modo secundario (1v1), el esticker "respondes" y `geography`.
- **Amarillo** — destacados y monedas; `history`.
- **Naranja** — `sports`. **Rosa** — `entertainment`. **Rojo** — el fallo al revelar y `art`.
- **Pizarra** (`#334155`/`#243042`/`#111722`) — controles neutros (`slate`).
- **Los seis colores de categoría** — solo el badge de categoría.

## Forma y tipografía (compartidas)

```css
:root {
  --r-sm: 10px; --r-md: 14px; --r-lg: 22px; --r-key: 18px; --r-tile: 16px;
  --border-w: 2.5px; --depth-key: 6px; --depth-tile: 5px;
  --s-1: 4px; --s-2: 8px; --s-3: 12px; --s-4: 16px; --s-5: 24px; --s-6: 32px; --s-7: 48px;
  --font-display: 'Fredoka', system-ui, sans-serif;
}
```

`--font-display` (títulos, botones, marcador, números) es **Fredoka**, siempre. La UI cambia
por estilo: `Instrument Sans` en Papel, `Plus Jakarta Sans` en Colorido. Fuentes autoalojadas
en `frontend/static/fonts/` (woff2, `font-display: swap`). **Presupuesto:** ≤ 250 KB de JS.

## Botón "juicy" (núcleo del estilo Colorido)

```css
.btn {
  --bg-top: var(--green-top); --bg-bot: var(--green-bot); --edge: var(--green-edge);
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px;
  width: 100%; min-height: 78px; padding: 15px 20px;
  border: none; border-radius: var(--r-key);                 /* 18 px, nunca píldora */
  background: linear-gradient(180deg, var(--bg-top), var(--bg-bot));
  box-shadow:
    inset 0 2px 0 rgb(255 255 255 / .4), inset 0 -2px 0 rgb(0 0 0 / .12),
    0 var(--depth-key) 0 var(--edge), 0 calc(var(--depth-key) + 4px) 18px -4px rgb(0 0 0 / .35);
  color: #FFF;                                                 /* título BLANCO */
  text-shadow: 0 2px 0 var(--edge);
  cursor: pointer; overflow: hidden;
  transition: transform .07s cubic-bezier(.34,1.56,.64,1), box-shadow .07s ease, filter .15s ease;
}
.btn:hover  { filter: brightness(1.04); transform: translateY(-1px); }
.btn:active { transform: translateY(4px);                     /* se hunde casi toda la base */
  box-shadow: inset 0 1px 0 rgb(255 255 255 / .2), 0 2px 0 var(--edge),
              0 3px 5px -1px rgb(0 0 0 / .3); }
.btn:disabled { filter: grayscale(.5) opacity(.55); cursor: not-allowed; }
```

El botón lleva **dos líneas**: título en mayúsculas (Fredoka `1.3rem`) y subtítulo descriptivo
(`Plus Jakarta Sans`, `0.82rem`). Variantes: `green` (acento/CTA) · `blue` (secundario) ·
`slate` (neutro). El `:focus-visible` es `outline: 3px solid #FFF` (Colorido) o
`3px solid var(--ink)` (Papel).

**Destello del modo principal** (solo Colorido): el botón lleva `overflow: hidden` y un `::after`
de 60 % de ancho, inclinado `-25°`, que cruza de `-130%` a `160%` en el 32 % de un ciclo de
3,5 s y descansa el resto. Es la única animación en loop permitida, y `prefers-reduced-motion`
la apaga. En Papel no se dibuja.

## Input hundido (pozo)

Campos de texto y contadores no tienen volumen hacia afuera: parecen cavados en el tablero.
Fondo `--well-bg`, borde `2px solid --well-border`, radio `16px` y
`box-shadow: inset 0 4px 0 rgb(0 0 0 / .45)`. A la derecha, el badge de validación es un
squircle verde de 34 px con relieve propio (`inset 0 2px 0 rgb(255 255 255 / .4)`,
`0 3px 0 var(--green-edge)`) y un check SVG adentro.

## Respuestas (teclado mecánico)

Las cuatro opciones son **teclas blancas** (`linear-gradient(180deg,#FFFFFF,#F1F5F9)`), borde
`2px solid #E2E8F0`, radio 16 px y base de 5 px. El número `1`–`4` vive en un **keycap** de
30×30 px a la izquierda, con su propio relieve (`0 2.5px 0 #CBD5E1`) y el número en azul.
La etiqueta va centrada para que **no se mueva** cuando aparecen las marcas.

Lo único que cambia entre estados es el color y la marca: elegido = borde azul, acierto =
**verde**, fallo = **rojo** con una sacudida horizontal de `0.36s`; en acierto y fallo la tecla
pasa a blanco sobre su color.

## Componentes

| Componente | Notas |
|---|---|
| `Button` | `green/blue/slate` · dos líneas (título + subtítulo) · 78 px · press de 4 px · misma API en los dos estilos · `sheen` solo el principal |
| `SkinSwitcher` | elegido en Inicio; escribe `data-skin` y `localStorage` (clave `omni-skin`) |
| `CategoryBadge` | color `--cat-*` + etiqueta de `es.json` |
| `AnswerTile` | idle/selected/correct/wrong/dim · ≥ 60 px · keycap `1`–`4` · verde/rojo al revelar |
| `NickInput` | 1–16, pozo hundido, badge de check; muestra el error del servidor tal cual |
| `TimerRing` | arco sobre `ends_at`; alerta y pulso en los últimos 5 s |
| `PlayerPanel` | nick, estado conectado/desconectado, puntos |
| `Scoreboard` | `you` – `opponent`, números en display; avatares en Colorido |
| `CodeInput` | 6 casillas, alfabeto sin `O/0/I/1`, pegado del código completo |
| `Modal` | fondo plano (sin blur), `Enter`/`Esc`, foco atrapado |
| `Toast` | errores de la API con `code` + `message` |
| `LifeStrip` | 3 vidas del arcade, se apagan con animación corta |

## Partida

- La **revelación** dura 2,5 s: correcta, qué eligió cada jugador y los puntos. La
  explicación aparece **solo si el jugador falló**.
- La pausa la da el servidor antes de servir la próxima ronda; mientras no exista, la
  pantalla de partida no se cierra (`docs/api.md`).
- Mientras el rival no contestó, la elección propia queda bloqueada y marcada; nunca se
  insinúa si es correcta.

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
- Contraste AA en ambos estilos: en Papel sobre el fondo y sobre cada color de categoría
  (blanco solo donde el ratio lo permita); en Colorido el texto de los botones es blanco
  sobre el degradado, con `text-shadow` para el filo.
- `prefers-reduced-motion`: sin pulso de `TimerRing`, sin rebote del botón, sin destello,
  sin transición de tile.
