# Sistema de diseño

> Cómo se ve y se siente Omnisapiens. Se consulta al construir cualquier pantalla.
> Referencias vivas: `frontend/design/referencia-botones.html` (botón) y
> `frontend/design/laboratorio_de_botones_juicy_ui_sheen.html` (lenguaje del estilo Colorido).

## Dos estilos

La app tiene **dos estilos completos**, no dos paletas: mismo layout, misma estructura de
componentes y **otra piel entera** (forma, sombras, tipografía, densidad, tono). El jugador
elige; el estilo vive en `data-skin` sobre `<html>`, se recuerda en `localStorage` y el
cambio **recarga la página**.

| | **Papel** (por defecto) | **Colorido** |
|---|---|---|
| Idea | Juguete de mesa: papel, tinta, teclas | Preguntados / Clash: botones gruesos de maquinita sobre un lienzo iluminado |
| Fondo | papel cálido plano `#FCF8F0` | viñeta radial teñida con el acento del jugador (arriba saturada, abajo casi negra) |
| Superficie | blanca, borde de tinta `2.5px`, sombra dura `4px 4px 0` | panel translúcido, borde del acento al 30 %, radio 24 px, sombra suave |
| Botón | borde de tinta, degradado leve, sombra dura, base de 6 px | sin borde, degradado de volumen, bisel interno de 2 px, **radio 35 px y base sólida de 11 px**, glow al hover |
| Radial | `10` chips · `14` botones y tarjetas | `35` botones de modo · `6` tiles y campos · `14` chips · `24` paneles |
| Tamaños | `lg` 84 px · `md` 60 px | modo principal 78 px · modo secundario 64 px · tiles 50 px |
| Texto | frase normal, `Instrument Sans` + `Fredoka` | mayúsculas en botones/badges, `Plus Jakarta Sans` + `Fredoka` |
| Tiles de respuesta | teclas blancas, tecla `1`–`4` a la izquierda | **blancos y bajos** (50 px), 6 px de radio, base de 3 px y un brillo estático en la esquina; etiqueta centrada y tecla `1`–`4` en chip |
| Acierto | tile pintado con el color de la **categoría** | tile en **verde**, el fallo en **rojo** (`✓`/`✗`), el color de categoría queda en el badge |
| Paleta de controles | azul (acción) · blanco (secundario) | **el acento que elige el jugador** · acento oscuro = secundario · gris = fantasma |
| Extras | ninguno | destello diagonal en el modo principal, esticker sobre la pregunta, avatares en el marcador, fila de ranking |

Ningún estilo se mezcla con el otro: los componentes comparten markup y se visten por
bloques `body[data-skin='…']`. **Sin librería de UI y sin Tailwind**: CSS propio.

**Las reglas de abajo no se niegan en ningún estilo:**

- **Cero emojis.** Todos los íconos son SVG propios (grid 24, trazo 2.5, `currentColor`).
- El **gradiente solo da volumen** a lo presionable (luz arriba, sombra abajo) o el brillo
  estático de un borde (esquina de los tiles). Prohibido como decoración de fondos o
  tarjetas. Excepciones: la viñeta del lienzo de Colorido y el destello del botón principal.
- **Al presionar**: baja 2 px (tile) u 8 px (botón de maquinita) y la base se reduce. Sin
  rebotes largos.
- La **tipografía se elige**, no se hereda. Nada de `system-ui` como fuente principal.
- **Cero animaciones de entrada por scroll**: se anima el feedback (press, reveal, acierto).
  Excepción única: el **destello en loop del botón del modo principal** de Colorido.
- **Accesibilidad mínima**: foco visible, contraste AA, blancos táctiles ≥ 44 px, todo
  jugable con teclado (`1`–`4` responde, `Enter` confirma).
- **Sin scroll en la pantalla de partida**; en el resto, columna máx. 480 px.

## Estilo Papel

```css
body[data-skin='papel'] {
  --ink: #101828; --ink-2: #344054; --ink-3: #667085;
  --bg: #FCF8F0; --surface: #FFFFFF; --surface-2: #F2EADF; --surface-line: #101828;
  --key-primary-top: #3D78FF; --key-primary-bottom: #2F6BFF; --key-primary-edge: #1E4FD1;
  --key-secondary-top: #FFFFFF; --key-secondary-bottom: #F5EEE2; --key-secondary-edge: #D8CCB8;
  --timer-arc: #2F6BFF; --timer-alert: #E1484B;
  --cat-geography: #2E9E5B; --cat-history: #C77B2E; --cat-science: #2A6FD6;
  --cat-art: #8A4FD3; --cat-entertainment: #E0498F; --cat-sports: #1E9E9E;
  --font-ui: 'Instrument Sans', system-ui, sans-serif;
}
```

El **texto del badge y del acierto** depende del color: blanco en `science` y `art`, tinta en
el resto. Los pares exactos se fijan en los tokens (`--cat-*-on`), no a ojo.

## Estilo Colorido

```css
body[data-skin='colorido'] {
  /* El acento es preferencia del jugador: un tono para todo lo presionable. */
  --accent-h: 252;
  --accent-top: hsl(var(--accent-h) 88% 70%);
  --accent-bottom: hsl(var(--accent-h) 78% 56%);
  --accent-edge: hsl(var(--accent-h) 62% 34%);
  --accent-glow: hsl(var(--accent-h) 88% 70% / .45);
  --accent-soft: hsl(var(--accent-h) 90% 96%);
  --accent-line: hsl(var(--accent-h) 55% 74%);
  --accent-ink: hsl(var(--accent-h) 62% 36%);

  --bg: radial-gradient(circle at 50% 0%,
        hsl(var(--accent-h) 55% 27%) 0%, hsl(var(--accent-h) 52% 15%) 62%, #0A0D18 100%);
  --surface: rgb(11 15 26 / .55);   --surface-line: hsl(var(--accent-h) 70% 78% / .3);
  --ink: #F8FAFC; --ink-2: #CBD5E1; --ink-3: #94A3B8;
  --on-bg-dim: hsl(var(--accent-h) 80% 80%);
  --timer-arc: var(--accent-bottom); --timer-alert: #F87171;

  /* Forma: botones gruesos de maquinita y respuestas bajas y sutiles. */
  --r-key: 35px; --depth-key: 11px;      /* botones de modo */
  --r-tile: 6px; --depth-tile: 3px;      /* respuestas y campos */
  --font-ui: 'Plus Jakarta Sans', system-ui, sans-serif;

  /* los seis colores pintan solo el badge de categoría, nunca los botones */
  --cat-geography: #2ED573; --cat-history: #FFBE26; --cat-science: #38BDF8;
  --cat-art: #A855F7; --cat-entertainment: #F87171; --cat-sports: #FB923C;
}
```

### El acento es del jugador

El estilo no trae un color propio: trae un **tono elegido** (slider de `0`–`360` en el inicio,
recordado en `localStorage`). Ese tono pinta todo lo presionable, el anillo del reloj, el
avatares propio y tiñe el lienzo; por eso el estilo nunca se ve violeta por obligación.

Las otras reglas del color, para que la pantalla no sea un circo:

- **Acento** — modo principal, modo secundario, chips, esticker, tiles elegidos.
- **Acento oscuro** (`hsl(accent 48% 34%)` → `hsl(accent 50% 23%)`) — el modo secundario:
  misma familia, menos brillo, así el principal manda.
- **Verde** `#35D97A/#22A15A/#1A8A4C` — solo el acierto al revelar.
- **Rojo** `#F87171/#D92C2C/#8F1D1D` — solo el fallo al revelar.
- **Fantasma** — superficies translúcidas con borde del acento, sin base: filas secundarias
  (ranking) y chip no elegido.
- **Los seis colores de categoría** — solo el badge.

### Respuestas

Los cuatro tiles son **blancos y bajos** (`linear-gradient(180deg,#F7F8FD,#E4E7F6)`), de 6 px
de radio y 3 px de base, con un **brillo estático** en la esquina (un `linear-gradient` a 118°
al 95 % de blanco sobre el fondo del tile, siempre en la misma posición: brilla, no late).
El texto va oscuro (`#1E2244`); el chip de la tecla `1`–`4` va teñido con el acento.

Lo único que cambia entre estados es la marca y el color de acierto: elegido = tinte y borde
del acento, descartado = atenuado, acierto = verde, fallo = rojo. La etiqueta va centrada en
una grilla `1fr auto 1fr` (tecla · texto · marcas) para que **no se mueva** cuando aparece el
chip del jugador.

## Forma y tipografía (compartidas)

```css
:root {
  --r-sm: 10px; --r-md: 14px; --r-lg: 22px; --r-full: 999px; --border-w: 2.5px;
  --s-1: 4px; --s-2: 8px; --s-3: 12px; --s-4: 16px; --s-5: 24px; --s-6: 32px; --s-7: 48px;
  --font-display: 'Fredoka', system-ui, sans-serif;
}
```

`--font-display` (títulos, botones, marcador, números) es **Fredoka**, siempre. La UI cambia
por estilo: `Instrument Sans` en Papel, `Plus Jakarta Sans` en Colorido. Fuentes
autoalojadas en `frontend/static/fonts/` (woff2, `font-display: swap`).
**Presupuesto:** ≤ 250 KB de JS.

## Botón "juicy" (núcleo del estilo Colorido)

```css
.button {
  --j-top: var(--accent-top); --j-bottom: var(--accent-bottom); --j-edge: var(--accent-edge);
  --j-depth: var(--depth-key);            /* 11 px: alta, de maquinita */
  display: inline-flex; align-items: center; justify-content: center; gap: var(--s-2);
  min-height: 78px; padding: 16px 24px;
  font: 700 1.25rem/1 var(--font-display); letter-spacing: .5px; text-transform: uppercase;
  color: #FFF; border: none; border-radius: var(--r-key); cursor: pointer;  /* 35 px */
  background: linear-gradient(180deg, var(--j-top), var(--j-bottom));
  box-shadow:
    inset 0 2px 0 rgb(255 255 255 / .38),
    inset 0 -2px 0 rgb(0 0 0 / .12),
    0 var(--j-depth) 0 var(--j-edge),
    0 11px 15px -3px rgb(0 0 0 / .35);
  text-shadow: 0 2px 0 var(--j-edge);
  transition: transform .07s cubic-bezier(.34,1.56,.64,1), box-shadow .07s ease, filter .15s ease;
}
.button:hover  { filter: brightness(1.05); transform: translateY(-1px); }
.button:active { transform: translateY(8px);            /* se hunde casi toda la base */
  box-shadow: inset 0 1px 0 rgb(255 255 255 / .2), 0 3px 0 var(--j-edge),
              0 3px 6px -2px rgb(0 0 0 / .25); }
.button:disabled { filter: grayscale(.6) opacity(.5); cursor: not-allowed; }
```

Variantes: `primary` (acento) · `secondary` (acento oscuro, 64 px) · `danger` (rojo) ·
`ghost` (sin volumen). El `:focus-visible` es `outline: 3px solid #FFF; outline-offset: 4px`
(Colorido) o `3px solid var(--ink); outline-offset: 3px` (Papel).

**Destello del modo principal** (solo `primary`, del laboratorio con *sheen*): el botón lleva
`overflow: hidden` y un `::after` de 65 % de ancho, inclinado `-25°`, que cruza de `-130%` a
`220%` en el 32 % de un ciclo de 3,5 s y descansa el resto. Es la única animación en loop
permitida, y `prefers-reduced-motion` la apaga.

## Componentes

| Componente | Notas |
|---|---|
| `Button` | `primary/secondary/danger/ghost` · 78/64 px en Colorido, `lg/md` en Papel · press de 8 px · misma API en los dos estilos |
| `SkinSwitcher` | elegido en Inicio; escribe `data-skin` y `localStorage`, luego recarga |
| `AccentSlider` | tono `0`–`360` del acento, en Inicio; escribe `--accent-h` y `localStorage` |
| `AnswerTile` | idle/selected/correct/wrong · ≥ 50 px · tecla `1`–`4` visible · Papel: color de categoría al revelar; Colorido: tinte del acento, verde/rojo al revelar |
| `CategoryBadge` | color `--cat-*` + etiqueta de `es.json` |
| `TimerRing` | arco sobre `ends_at`; alerta y pulso en los últimos 5 s |
| `PlayerPanel` | nick, estado conectado/desconectado, puntos |
| `Scoreboard` | `you` – `opponent`, números en display; avatares solo en Colorido |
| `CodeInput` | 6 casillas, alfabeto sin `O/0/I/1`, pegado del código completo |
| `NickInput` | 1–16, muestra el error del servidor tal cual |
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
- `prefers-reduced-motion`: sin pulso de `TimerRing`, sin rebote del botón, sin transición
  de tile.
