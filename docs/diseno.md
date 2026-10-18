# Sistema de diseño

> Cómo se ve y se siente Omnisapiens. Se consulta al construir cualquier pantalla.
> Referencia viva del botón: `frontend/design/referencia-botones.html`.

## Principio

La interfaz es **un juguete de mesa**: cada superficie presionable parece una tecla física
que se hunde al tocarla. Nada de vidrio, blur ni degradados de landing: volumen simple,
sombra dura y color plano.

**Estas reglas no se negocian:**

- El **gradiente solo da volumen** a lo presionable (luz arriba, sombra abajo). Prohibido
  como decoración de fondos o tarjetas.
- **Cero emojis.** Todos los íconos son SVG propios (grid 24, trazo 2.5, `currentColor`).
- **Sombras duras** (`4px 4px 0 0 var(--ink)`), sin blur. La única sombra con desenfoque
  permitida es la que despega el botón del fondo (`0 10px 15px -3px rgba(0,0,0,.3)`).
- **Borde `2.5px solid var(--ink)`** en todo interactivo.
- **Al presionar**: baja 3–4 px y la sombra dura se reduce a 1 px. Sin rebotes largos.
- Radios contenidos: `10px` chips, `14px` botones y tarjetas, `999px` solo badges.
- La **tipografía se elige**, no se hereda. Nada de `system-ui` como fuente principal.
- El **color de categoría** manda en el badge y en el acierto.
- **Cero animaciones de entrada por scroll**: se anima el feedback (press, reveal, acierto).
- **Accesibilidad mínima**: foco visible, contraste AA, todo jugable con teclado
  (`1`–`4` responde, `Enter` confirma).

## Paleta (decisión abierta)

Hay dos candidatas. Se decide probando el mismo `Button` y la misma pantalla de partida con
las dos, no en abstracto. Hasta entonces, los tokens de abajo son la **candidata A**.

**A — Preguntados (clara).** Fondo papel cálido, tinta oscura, seis colores de categoría
saturados. Es la que fija el producto: se lee bien al sol, en pantalla chica, y el color
codifica la categoría.

**B — oscura.** La de `referencia-botones.html`: fondo `#1e272e`, botones verdes/amarillos/
violetas. Más "arcade", peor contraste para texto largo.

```css
:root {
  /* Candidata A */
  --ink: #101828; --ink-2: #344054; --ink-3: #667085;
  --paper: #FCF8F0; --paper-2: #F2EADF; --white: #FFFFFF;
  --correct: #2FA36B; --correct-dark: #1E7A4D;
  --wrong: #E14B4B; --wrong-dark: #A32F2F;
  --brand: #2F6BFF; --brand-dark: #1E4FD1; --gold: #D99B1C;
  --cat-geography: #2E9E5B; --cat-history: #C77B2E; --cat-science: #2A6FD6;
  --cat-art: #8A4FD3; --cat-entertainment: #E0498F; --cat-sports: #1E9E9E;

  /* Forma */
  --r-sm: 10px; --r-md: 14px; --r-full: 999px; --border-w: 2.5px;
  --shadow-hard: 4px 4px 0 0 var(--ink); --shadow-press: 1px 1px 0 0 var(--ink);
  --edge-h: 6px;          /* borde inferior del botón "tecla" */

  /* Espaciado (4 → 64) */
  --s-1: 4px; --s-2: 8px; --s-3: 12px; --s-4: 16px;
  --s-5: 24px; --s-6: 32px; --s-7: 48px; --s-8: 64px;

  /* Tipografía */
  --font-display: "Fredoka", system-ui, sans-serif;   /* 600/700 */
  --font-ui: "Instrument Sans", system-ui, sans-serif;
}
```

Fuentes autoalojadas en `frontend/static/fonts/` (woff2, `font-display: swap`). Display en
título, marcador, números grandes y botones (700); UI en texto común. **Presupuesto:** ≤ 250 KB
de JS.

## Botón "juicy" (núcleo del sistema)

Extraído de `referencia-botones.html` y adaptado a los tokens:

```css
.button {
  --bg-top: var(--brand); --bg-bottom: var(--brand-dark); --edge: #1E4FD1;
  display: inline-flex; align-items: center; justify-content: center; gap: var(--s-2);
  min-height: 48px; padding: 16px 32px;
  font: 700 1.1rem/1 var(--font-display); letter-spacing: .6px; text-transform: uppercase;
  color: var(--white); border: none; border-radius: var(--r-md); cursor: pointer;
  background: linear-gradient(180deg, var(--bg-top), var(--bg-bottom));
  box-shadow:
    inset 0 2px 0 rgba(255,255,255,.35),
    inset 0 -2px 0 rgba(0,0,0,.10),
    0 var(--edge-h) 0 var(--edge),
    0 10px 15px -3px rgba(0,0,0,.30);
  text-shadow: 0 2px 0 var(--edge);
  transition: transform .08s cubic-bezier(.34,1.56,.64,1), box-shadow .08s ease;
}
.button:hover  { filter: brightness(1.05); transform: translateY(-1px); }
.button:active { transform: translateY(4px);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.2), 0 2px 0 var(--edge),
              0 4px 6px -2px rgba(0,0,0,.2); }
.button:disabled { filter: grayscale(.6) opacity(.5); cursor: not-allowed; }
```

Variantes: `primary` (brand), `secondary` (paper + ink, con borde), `danger` (wrong),
`ghost` (sin volumen). Tamaños `md` (48 px) y `lg` (56 px). El `:focus-visible` es
`outline: 3px solid var(--ink); outline-offset: 3px` en todos.

## Componentes

| Componente | Estados / notas |
|---|---|
| `Button` | primary/secondary/danger/ghost · md/lg · press de 4 px |
| `AnswerTile` | idle/selected/correct/wrong/disabled · alto ≥ 64 px · tecla `1`–`4` visible · color de categoría al revelar |
| `CategoryBadge` | color `--cat-*` + etiqueta de `es.json` |
| `TimerRing` | arco sobre `ends_at`; alerta y pulso en los últimos 5 s |
| `PlayerPanel` | nick, estado conectado/desconectado, puntos |
| `Scoreboard` | `you` – `opponent`, números en display |
| `CodeInput` | 6 casillas, alfabeto sin `O/0/I/1`, pegado del código completo |
| `NickInput` | 1–16, muestra el error del servidor tal cual |
| `Modal` | fondo plano (sin blur), `Enter`/`Esc`, foco atrapado |
| `Toast` | errores de la API con `code` + `message` |
| `LifeStrip` | 3 vidas del arcade, se apagan con animación corta |

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
- Contraste AA sobre `--paper` y sobre cada color de categoría (texto blanco solo donde
  el ratio lo permita).
- `prefers-reduced-motion`: sin pulso de `TimerRing`, sin rebote del botón, sin transición
  de tile.
- Sin scroll en la pantalla de partida; en el resto, columna máx. 480 px.
