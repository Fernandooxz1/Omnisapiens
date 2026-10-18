# Sistema de diseño

> Cómo se ve y se siente Omnisapiens. Se consulta al construir cualquier pantalla.
> Referencias vivas: `frontend/design/referencia-botones.html` (botón) y
> `frontend/design/laboratorio_de_botones_juicy_ui.html` (lenguaje del estilo Colorido).

## Dos estilos

La app tiene **dos estilos completos**, no dos paletas: mismo layout, misma estructura de
componentes y **otra piel entera** (forma, sombras, tipografía, densidad, tono). El jugador
elige; el estilo vive en `data-skin` sobre `<html>`, se recuerda en `localStorage` y el
cambio **recarga la página**.

| | **Papel** (por defecto) | **Colorido** |
|---|---|---|
| Idea | Juguete de mesa: papel, tinta, teclas | Preguntados / Clash: squircle 3D sobre un lienzo iluminado |
| Fondo | papel cálido plano `#FCF8F0` | viñeta radial índigo `#312E81 → #1E1B4B → #0F172A` |
| Superficie | blanca, borde de tinta `2.5px`, sombra dura `4px 4px 0` | panel translúcido, borde índigo 30 %, radio 24 px, sombra suave |
| Botón | borde de tinta, degradado leve, sombra dura | sin borde, degradado de volumen, bisel interno de 2 px, **base sólida** de 6 px, glow al hover |
| Radio | `10` chips · `14` botones y tarjetas | `14–16` chips · `18–22` botones · `24` paneles |
| Texto | frase normal, `Instrument Sans` + `Fredoka` | mayúsculas en botones/badges, `Plus Jakarta Sans` + `Fredoka` |
| Tiles de respuesta | teclas blancas, tecla `1`–`4` a la izquierda | cuatro botones de color, etiqueta centrada, tecla `1`–`4` en chip |
| Acierto | tile pintado con el color de la **categoría** | tile en **verde**, el fallo en **rojo** (`✓`/`✗`), el color de categoría queda en el badge |
| Extras | ninguno | esticker sobre la pregunta, avatares en el marcador, botón de ranking |

Ningún estilo se mezcla con el otro: los componentes comparten markup y se visten por
bloques `body[data-skin='…']`. **Sin librería de UI y sin Tailwind**: CSS propio.

**Las reglas de abajo no se negocian en ningún estilo:**

- **Cero emojis.** Todos los íconos son SVG propios (grid 24, trazo 2.5, `currentColor`).
- El **gradiente solo da volumen** a lo presionable (luz arriba, sombra abajo). Prohibido
  como decoración de fondos o tarjetas. Única excepción: la viñeta del lienzo de Colorido,
  que hace de arena iluminada.
- **Al presionar**: baja 3–4 px y la base del botón se reduce. Sin rebotes largos.
- La **tipografía se elige**, no se hereda. Nada de `system-ui` como fuente principal.
- **Cero animaciones de entrada por scroll**: se anima el feedback (press, reveal, acierto).
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
  --bg: radial-gradient(circle at 50% 0%, #312E81 0%, #1E1B4B 62%, #0F172A 100%);
  --surface: rgb(15 23 42 / .55);   --surface-line: rgb(129 140 248 / .3);
  --ink: #F8FAFC; --ink-2: #CBD5E1; --ink-3: #94A3B8; --on-bg-dim: #A5B4FC;
  --timer-arc: #FFBE26; --timer-alert: #F87171;
  --font-ui: 'Plus Jakarta Sans', system-ui, sans-serif;
  /* las seis categorías son los seis colores del botón */
  --cat-geography: #2ED573; --cat-history: #FFBE26; --cat-science: #38BDF8;
  --cat-art: #A855F7; --cat-entertainment: #F87171; --cat-sports: #FB923C;
}
```

Cada color tiene su terna (arriba, abajo, base) y su glow, como variantes del botón:
`green #2ED573/#26AF61/#1B8A4B` · `blue #38BDF8/#0284C7/#0369A1` ·
`yellow #FFBE26/#F39C12/#C27803` · `purple #A855F7/#7E22CE/#581C87` ·
`orange #FB923C/#EA580C/#9A3412` · `red #F87171/#DC2626/#991B1B`.
Sobre estos fondos el texto va **siempre en blanco**, con `text-shadow: 0 2px 0 <base>`.

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
  --j-top: var(--brand); --j-bottom: var(--brand-dark); --j-edge: #1E4FD1;
  display: inline-flex; align-items: center; justify-content: center; gap: var(--s-2);
  min-height: 48px; padding: 16px 32px;
  font: 700 1.1rem/1 var(--font-display); letter-spacing: .6px; text-transform: uppercase;
  color: #FFF; border: none; border-radius: var(--r-lg); cursor: pointer;
  background: linear-gradient(180deg, var(--j-top), var(--j-bottom));
  box-shadow:
    inset 0 2px 0 rgb(255 255 255 / .38),
    inset 0 -2px 0 rgb(0 0 0 / .12),
    0 6px 0 var(--j-edge),
    0 11px 15px -3px rgb(0 0 0 / .35);
  text-shadow: 0 2px 0 var(--j-edge);
  transition: transform .07s cubic-bezier(.34,1.56,.64,1), box-shadow .07s ease, filter .15s ease;
}
.button:hover  { filter: brightness(1.05); transform: translateY(-1px); }
.button:active { transform: translateY(4px);
  box-shadow: inset 0 1px 0 rgb(255 255 255 / .2), 0 2px 0 var(--j-edge),
              0 3px 6px -2px rgb(0 0 0 / .25); }
.button:disabled { filter: grayscale(.6) opacity(.5); cursor: not-allowed; }
```

Variantes: `primary` (green), `secondary` (blue), `gold` (ranking), `danger` (red),
`ghost` (sin volumen). El `:focus-visible` es `outline: 3px solid #FFF; outline-offset: 4px`
(Colorido) o `3px solid var(--ink); outline-offset: 3px` (Papel).

## Componentes

| Componente | Notas |
|---|---|
| `Button` | `primary/secondary/gold/danger/ghost` · `md/lg` · press de 4 px · misma API en los dos estilos |
| `SkinSwitcher` | elegido en Inicio; escribe `data-skin` y `localStorage`, luego recarga |
| `AnswerTile` | idle/selected/correct/wrong · ≥ 64 px · tecla `1`–`4` visible · Papel: color de categoría al revelar; Colorido: verde/rojo |
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
