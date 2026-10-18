# DIRECTRIZ OBLIGATORIA DE UI/UX: ESTILO "TACTILE JUICY UI" (OMNISAPIENS)

Actuá como un Senior Frontend UI Engineer especializado en interfaces de juegos (estilo Trivia Crack / Duolingo). Debés construir o refactorizar toda la interfaz de **Omnisapiens** aplicando estrictamente el siguiente sistema de diseño. No uses estilos planos (flat design) ni sombras difusas estándar.

## 1. REGLAS INQUEBRANTABLES
1. **CERO EMOJIS UNICODE:** Está terminantemente prohibido usar emojis de texto (ej. 🏆, ⚡, ✅) en el HTML/JSX. Todos los íconos deben ser **SVGs inline** con `stroke="currentColor"`, `stroke-width="2.5"`, `stroke-linecap="round"` y `stroke-linejoin="round"`.
2. **NO USAR BORDES TIPO PÍLDORA (`999px`) EN BOTONES GRANDES:** Usá geometría **Squircle** (`border-radius: 18px` en botones grandes, `16px` en opciones de respuesta, `28px` en contenedores principales).
3. **VOLUMEN 3D SÓLIDO (PUSHABLE):** Todo botón, tarjeta o badge debe tener un borde inferior sólido sin difuminar (`box-shadow: 0 Xpx 0 var(--edge-color)`) y un bisel de luz blanco superior interno (`inset 0 2px 0 rgba(255,255,255,0.4)`). Al hacer `:active`, el elemento debe hundirse físicamente (`transform: translateY(...)`) reduciendo su sombra inferior en la misma proporción.
4. **INPUTS Y CONTADORES "HUNDIDOS" (RECESSED WELLS):** Los campos de texto (`input`) y fondos de marcadores no llevan relieve hacia afuera; deben parecer cavados en el tablero usando sombra interna oscura (`box-shadow: inset 0 4px 0 rgba(0,0,0,0.45)`).

---

## 2. TIPOGRAFÍA Y JERARQUÍA
Importar de Google Fonts: `'Fredoka'` (pesos 600, 700) y `'Plus Jakarta Sans'` (pesos 600, 700, 800).
- **Títulos, Botones, Puntajes y Badges:** `font-family: 'Fredoka', sans-serif; font-weight: 700;`
- **Textos secundarios, subtítulos y descripciones dentro de botones:** `font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700;`
- **Título Principal (Logo):** Blanco (`#FFFFFF`), `letter-spacing: -1px`, con sombra sólida 3D hacia abajo: `text-shadow: 0 5px 0 #15191F, 0 8px 16px rgba(0,0,0,0.35);`.
- **Texto en botones de color:** Blanco con relieve `text-shadow: 0 2px 0 var(--edge-color)`. Nunca usar `-webkit-text-stroke` negro.

---

## 3. VARIABLES Y PALETA DE COLORES (OFICIAL PREGUNTADOS)
Usá exactamente estas variables CSS en `:root`:

```css
:root {
  --font-display: 'Fredoka', system-ui, sans-serif;
  --font-body: 'Plus Jakarta Sans', system-ui, sans-serif;

  /* Superficies del Tablero (Modo Oscuro / Colorido) */
  --board-bg: #222831;
  --card-bg: #2B323C;
  --card-edge: #171C22;
  --panel-bg: #363F4C;
  --panel-edge: #1E232A;
  --well-bg: #1A1F26;
  --well-border: #12161B;

  /* Verde Ciencia (CTA Principal / Arcade / Respuesta Correcta) */
  --green-top: #2CE67C; --green-bot: #1EC765; --green-edge: #13964B;
  /* Azul Geografía (Jugar 1v1 / Secundario) */
  --blue-top: #2BC0FF;  --blue-bot: #0098E6;  --blue-edge: #006BB3;
  /* Amarillo Historia (Monedas / Destacados) */
  --yellow-top: #FFE135; --yellow-bot: #FFC800; --yellow-edge: #D69E00;
  /* Naranja Deportes */
  --orange-top: #FF9E2C; --orange-bot: #FF7800; --orange-edge: #CC5600;
  /* Rosa Entretenimiento */
  --pink-top: #FF66B2;   --pink-bot: #EC388B;   --pink-edge: #B51B63;
  /* Rojo Arte (Error / Respuesta Incorrecta) */
  --red-top: #FF5242;    --red-bot: #E62514;    --red-edge: #AD1407;
}

4. ARQUITECTURA EXACTA DE LOS COMPONENTES CLAVE
A. Botones de Acción Masivos (Ej: "ARCADE" y "JUGAR 1V1")
Contienen dos líneas: un título en mayúsculas (1.25rem, Fredoka) y un subtítulo descriptivo (0.82rem, Plus Jakarta Sans, opacidad 0.95).

border-radius: 18px, padding: 15px 20px.

Sombra: inset 0 2px 0 rgba(255,255,255,0.4), inset 0 -2px 0 rgba(0,0,0,0.12), 0 6px 0 var(--edge-color), 0 10px 18px -4px rgba(0,0,0,0.35).

Estado :active: transform: translateY(4px) y la sombra 3D baja de 6px a 2px.

Efecto Sheen (Destello en CTA Principal): Agregar un ::after con background: linear-gradient(90deg, transparent, rgba(255,255,255,0.42), transparent), transform: skewX(-25deg) y una animación infinita de 3.5s que cruce de left: -130% a left: 160%.

B. Input Hundido ("TU NOMBRE")
Fondo --well-bg (#1A1F26), border: 2px solid #3E4856, border-radius: 16px.

Sombra interna: box-shadow: inset 0 4px 0 rgba(0, 0, 0, 0.45).

Adentro a la derecha lleva un badge circular verde de validación (28px x 28px) con relieve 3D propio (0 3px 0 var(--green-edge)) y un ícono SVG de check adentro.

C. Tarjeta de Pregunta y Badges Flotantes
Contenedor con fondo --panel-bg (#363F4C), border: 2px solid rgba(255,255,255,0.08), border-radius: 22px, y base 3D 0 6px 0 var(--panel-edge).

Badge de Categoría (ej. "CIENCIA"): Pastilla con el gradiente de la categoría correspondiente, border-radius: 10px, box-shadow: inset 0 1px 0 rgba(255,255,255,0.4), 0 3px 0 var(--edge-color).

Badge Flotante "RESPONDE": Posicionado con position: absolute; top: -13px; right: 16px; transform: rotate(2deg);, gradiente azul, borde 0 3px 0 var(--blue-edge).

D. Botones de Respuesta Tipo Teclado Mecánico (Opciones 1 a 4)
Estado por defecto (Blanco táctil):

Fondo: linear-gradient(180deg, #FFFFFF 0%, #F1F5F9 100%).

Borde: 2px solid #E2E8F0, border-radius: 16px.

Sombra 3D: 0 5px 0 #CBD5E1, 0 8px 12px rgba(0, 0, 0, 0.2).

Texto: #1E293B, centrado.

Tecla Numérica Izquierda (1, 2, 3, 4):

Es un cuadrado de 30px x 30px posicionado a la izquierda dentro del botón (border-radius: 9px), con fondo #F8FAFC, border: 2px solid #CBD5E1, y su propio relieve 0 3px 0 #CBD5E1. Color de número: #0098E6.

Estados al responder:

.is-correct: Cambia el fondo del botón al gradiente Verde Ciencia, texto blanco, sombra 0 5px 0 var(--green-edge), y la tecla numérica pasa a tener fondo blanco con texto verde.

.is-wrong: Cambia al gradiente Rojo Arte, sombra 0 5px 0 var(--red-edge) y ejecuta una animación @keyframes shakeError horizontal de 0.35s.

CSS y estructura:
:root {
      --font-display: 'Fredoka', system-ui, -apple-system, sans-serif;
      --font-body: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;

      /* ==========================================
         PALETA OFICIAL PREGUNTADOS (TRIVIA CRACK)
         ========================================== */
      /* Ciencia (Verde) */
      --tc-green-top: #2ce67c;
      --tc-green-bot: #1ec765;
      --tc-green-edge: #13964b;

      /* Geografía (Azul) */
      --tc-blue-top: #2bc0ff;
      --tc-blue-bot: #0098e6;
      --tc-blue-edge: #006bb3;

      /* Historia (Amarillo) */
      --tc-yellow-top: #ffe135;
      --tc-yellow-bot: #ffc800;
      --tc-yellow-edge: #d69e00;

      /* Deportes (Naranja) */
      --tc-orange-top: #ff9e2c;
      --tc-orange-bot: #ff7800;
      --tc-orange-edge: #cc5600;

      /* Entretenimiento (Rosa) */
      --tc-pink-top: #ff66b2;
      --tc-pink-bot: #ec388b;
      --tc-pink-edge: #b51b63;

      /* Arte (Rojo) */
      --tc-red-top: #ff5242;
      --tc-red-bot: #e62514;
      --tc-red-edge: #ad1407;

      /* Corona / Especial (Violeta) */
      --tc-purple-top: #b55fe6;
      --tc-purple-bot: #9338c6;
      --tc-purple-edge: #6a1e96;
    }

    body {
      font-family: var(--font-body);
      background-color: #12161f;
      color: #f8fafc;
      margin: 0;
      overflow-x: hidden;
    }

    .font-display {
      font-family: var(--font-display);
    }

    /* ==========================================
       CONTENEDOR DE PANTALLA (DISPOSITIVO)
       ========================================== */
    .phone-frame {
      width: 100%;
      max-width: 430px;
      min-height: 760px;
      border-radius: 32px;
      padding: 28px 24px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
      transition: background 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
      
      /* Tema Oscuro Pizarra (Colorido) por defecto */
      background: radial-gradient(circle at 50% 0%, #2c3849 0%, #1e2631 55%, #171d26 100%);
      border: 4px solid #334052;
      box-shadow: 
        0 10px 0 #0d1117,
        0 25px 50px -12px rgba(0, 0, 0, 0.7);
    }

    /* Tema "PAPEL" (Claro Táctil) */
    .phone-frame.theme-papel {
      background: radial-gradient(circle at 50% 0%, #ffffff 0%, #f1f5f9 65%, #e2e8f0 100%);
      border: 4px solid #cbd5e1;
      color: #1e293b;
      box-shadow: 
        0 10px 0 #94a3b8,
        0 25px 50px -12px rgba(15, 23, 42, 0.35);
    }

    /* Título Principal 3D (Omnisapiens) */
    .game-logo {
      font-family: var(--font-display);
      font-size: 3.1rem;
      font-weight: 700;
      line-height: 1;
      letter-spacing: -0.5px;
      color: #ffffff;
      text-shadow: 0 4px 0 #0f141c;
    }
    .theme-papel .game-logo {
      color: #1e293b;
      text-shadow: 0 4px 0 #cbd5e1;
    }

    /* ==========================================
       INPUT 3D HUNDIDO (RECESSED WELL)
       ========================================== */
    .tactile-input-wrap {
      position: relative;
      display: flex;
      align-items: center;
      background-color: #131820;
      border: 2px solid #2e3a4b;
      border-radius: 18px;
      padding: 6px 8px 6px 16px;
      box-shadow: 
        inset 0 4px 0 rgba(0, 0, 0, 0.45),
        0 2px 0 rgba(255, 255, 255, 0.05);
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .tactile-input-wrap:focus-within {
      border-color: #2bc0ff;
      box-shadow: 
        inset 0 4px 0 rgba(0, 0, 0, 0.45),
        0 0 0 3px rgba(43, 192, 255, 0.25);
    }
    .theme-papel .tactile-input-wrap {
      background-color: #e2e8f0;
      border-color: #cbd5e1;
      box-shadow: 
        inset 0 3px 0 rgba(15, 23, 42, 0.12),
        0 2px 0 #ffffff;
    }

    .tactile-input {
      width: 100%;
      background: transparent;
      border: none;
      outline: none;
      font-family: var(--font-display);
      font-size: 1.25rem;
      font-weight: 600;
      color: #ffffff;
      padding: 8px 0;
    }
    .theme-papel .tactile-input {
      color: #1e293b;
    }

    /* Badge 3D del Check Verde dentro del Input */
    .check-badge-3d {
      width: 34px;
      height: 34px;
      border-radius: 11px;
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(180deg, var(--tc-green-top) 0%, var(--tc-green-bot) 100%);
      box-shadow: 
        inset 0 2px 0 rgba(255, 255, 255, 0.4),
        0 3px 0 var(--tc-green-edge);
      color: #ffffff;
    }

    /* ==========================================
       BOTONES JUICY 3D (MODOS DE JUEGO Y ACCIONES)
       ========================================== */
    .juicy-btn {
      position: relative;
      width: 100%;
      display: flex;
       flex-direction: column;
      align-items: center;
      justify-content: center;
      border: none;
      border-radius: 20px;
      padding: 16px 24px;
      cursor: pointer;
      user-select: none;
      outline: none;
      overflow: hidden;
      -webkit-tap-highlight-color: transparent;

      --bg-top: var(--tc-green-top);
      --bg-bot: var(--tc-green-bot);
      --edge: var(--tc-green-edge);
      --depth: 6px;

      background: linear-gradient(180deg, var(--bg-top) 0%, var(--bg-bot) 100%);
      box-shadow: 
        inset 0 2px 0 rgba(255, 255, 255, 0.42),
        inset 0 -2px 0 rgba(0, 0, 0, 0.12),
        0 var(--depth) 0 var(--edge),
        0 calc(var(--depth) + 6px) 14px -3px rgba(0, 0, 0, 0.38);

      transition: transform 0.07s cubic-bezier(0.34, 1.56, 0.64, 1),
                  box-shadow 0.07s cubic-bezier(0.34, 1.56, 0.64, 1),
                  filter 0.15s ease;
    }

    .juicy-btn:hover:not(:disabled) {
      filter: brightness(1.04);
      transform: translateY(-1px);
      box-shadow: 
        inset 0 2px 0 rgba(255, 255, 255, 0.5),
        inset 0 -2px 0 rgba(0, 0, 0, 0.12),
        0 calc(var(--depth) + 1px) 0 var(--edge),
        0 calc(var(--depth) + 9px) 18px -2px rgba(0, 0, 0, 0.42);
    }

    .juicy-btn:active:not(:disabled) {
      transform: translateY(4px);
      box-shadow: 
        inset 0 1px 0 rgba(255, 255, 255, 0.25),
        0 2px 0 var(--edge),
        0 3px 5px -1px rgba(0, 0, 0, 0.3);
    }

    .juicy-btn__title {
      position: relative;
      z-index: 2;
      font-family: var(--font-display);
      font-size: 1.35rem;
      font-weight: 700;
      letter-spacing: 0.6px;
      text-transform: uppercase;
      color: #ffffff;
      text-shadow: 0 2px 0 var(--edge);
      display: flex;
      align-items: center;
      gap: 8px;
      line-height: 1.15;
    }

    .juicy-btn__sub {
      position: relative;
      z-index: 2;
      font-family: var(--font-body);
      font-size: 0.82rem;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.92);
      text-shadow: 0 1px 0 var(--edge);
      margin-top: 3px;
    }

    /* Variantes de Color Oficiales */
    .juicy-btn--green {
      --bg-top: var(--tc-green-top);
      --bg-bot: var(--tc-green-bot);
      --edge: var(--tc-green-edge);
    }
    .juicy-btn--blue {
      --bg-top: var(--tc-blue-top);
      --bg-bot: var(--tc-blue-bot);
      --edge: var(--tc-blue-edge);
    }
    .juicy-btn--orange {
      --bg-top: var(--tc-orange-top);
      --bg-bot: var(--tc-orange-bot);
      --edge: var(--tc-orange-edge);
    }
    .juicy-btn--yellow {
      --bg-top: var(--tc-yellow-top);
      --bg-bot: var(--tc-yellow-bot);
      --edge: var(--tc-yellow-edge);
    }
    .juicy-btn--slate {
      --bg-top: #334155;
      --bg-bot: #243042;
      --edge: #111722;
    }
    .theme-papel .juicy-btn--slate {
      --bg-top: #ffffff;
      --bg-bot: #f1f5f9;
      --edge: #cbd5e1;
    }
    .theme-papel .juicy-btn--slate .juicy-btn__title {
      color: #1e293b;
      text-shadow: none;
    }

    /* Brillo Diagonal Animado (Sheen Effect para el CTA Principal) */
    .juicy-btn--sheen::after {
      content: "";
      position: absolute;
      top: -50%;
      left: -130%;
      width: 60%;
      height: 200%;
      background: linear-gradient(
        90deg,
        rgba(255, 255, 255, 0) 0%,
        rgba(255, 255, 255, 0.16) 25%,
        rgba(255, 255, 255, 0.48) 50%,
        rgba(255, 255, 255, 0.16) 75%,
        rgba(255, 255, 255, 0) 100%
      );
      transform: skewX(-25deg);
      pointer-events: none;
      z-index: 1;
      animation: sheenSweep 3.6s infinite ease-in-out;
    }

    @keyframes sheenSweep {
      0% { left: -130%; }
      32%, 100% { left: 220%; }
    }

    /* ==========================================
       PILLS DE ESTILO (PAPEL / COLORIDO)
       ========================================== */
    .pill-toggle-btn {
      font-family: var(--font-display);
      font-size: 0.85rem;
      font-weight: 700;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      padding: 9px 16px;
      border-radius: 14px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      transition: transform 0.07s ease, box-shadow 0.07s ease;
    }
    .pill-toggle-btn--inactive {
      background: #263142;
      color: #94a3b8;
      border: 1px solid #364459;
      box-shadow: 0 4px 0 #131922;
    }
    .theme-papel .pill-toggle-btn--inactive {
      background: #e2e8f0;
      color: #475569;
      border-color: #cbd5e1;
      box-shadow: 0 4px 0 #94a3b8;
    }
    .pill-toggle-btn--active {
      background: linear-gradient(180deg, var(--tc-blue-top) 0%, var(--tc-blue-bot) 100%);
      color: #ffffff;
      text-shadow: 0 1.5px 0 var(--tc-blue-edge);
      box-shadow: 
        inset 0 2px 0 rgba(255, 255, 255, 0.4),
        0 4px 0 var(--tc-blue-edge);
    }
    .pill-toggle-btn:active {
      transform: translateY(2px);
    }

    /* ==========================================
       PANTALLA 2: MARCADOR, PREGUNTA Y OPCIONES
       ========================================== */
    /* Tarjeta 3D del Marcador (ANA 348 - 296 BETO) */
    .scoreboard-card {
      background: linear-gradient(180deg, #2a3444 0%, #222b38 100%);
      border: 2px solid #38465b;
      border-radius: 22px;
      padding: 12px 16px;
      box-shadow: 
        inset 0 2px 0 rgba(255, 255, 255, 0.08),
        0 6px 0 #121720;
    }
    .theme-papel .scoreboard-card {
      background: #ffffff;
      border-color: #cbd5e1;
      box-shadow: 0 6px 0 #cbd5e1;
    }

    /* Fichas de Avatar 3D (A y B) */
    .avatar-token {
      width: 40px;
      height: 40px;
      border-radius: 13px;
      font-family: var(--font-display);
      font-weight: 700;
      font-size: 1.15rem;
      color: #ffffff;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .avatar-token--ana {
      background: linear-gradient(180deg, var(--tc-blue-top) 0%, var(--tc-blue-bot) 100%);
      box-shadow: inset 0 2px 0 rgba(255,255,255,0.4), 0 4px 0 var(--tc-blue-edge);
      text-shadow: 0 2px 0 var(--tc-blue-edge);
    }
    .avatar-token--beto {
      background: linear-gradient(180deg, var(--tc-orange-top) 0%, var(--tc-orange-bot) 100%);
      box-shadow: inset 0 2px 0 rgba(255,255,255,0.4), 0 4px 0 var(--tc-orange-edge);
      text-shadow: 0 2px 0 var(--tc-orange-edge);
    }

    /* Tarjeta 3D de la Pregunta */
    .question-card {
      position: relative;
      background: linear-gradient(180deg, #2a3444 0%, #212936 100%);
      border: 2px solid #38465b;
      border-radius: 22px;
      padding: 20px 20px 22px 20px;
      box-shadow: 
        inset 0 2px 0 rgba(255, 255, 255, 0.08),
        0 6px 0 #121720;
    }
    .theme-papel .question-card {
      background: #ffffff;
      border-color: #cbd5e1;
      box-shadow: 0 6px 0 #cbd5e1;
    }

    /* Etiqueta Flotante Inclinada "RESPONDE" */
    .responde-badge {
      position: absolute;
      top: -13px;
      right: 14px;
      font-family: var(--font-display);
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.7px;
      text-transform: uppercase;
      color: #ffffff;
      padding: 5px 12px;
      border-radius: 10px;
      transform: rotate(3deg);
      background: linear-gradient(180deg, var(--tc-blue-top) 0%, var(--tc-blue-bot) 100%);
      box-shadow: 
        inset 0 1.5px 0 rgba(255,255,255,0.45),
        0 3px 0 var(--tc-blue-edge),
        0 5px 10px rgba(0,0,0,0.3);
      text-shadow: 0 1.5px 0 var(--tc-blue-edge);
      animation: badgePulse 2.4s ease-in-out infinite;
    }
    @keyframes badgePulse {
      0%, 100% { transform: translateY(0) rotate(3deg); }
      50% { transform: translateY(-3px) rotate(3deg); }
    }

    /* Pastilla 3D de Categoría (CIENCIA, HISTORIA, etc.) */
    .category-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-family: var(--font-display);
      font-size: 0.76rem;
      font-weight: 700;
      letter-spacing: 0.7px;
      text-transform: uppercase;
      color: #ffffff;
      padding: 4px 12px;
      border-radius: 10px;
      background: linear-gradient(180deg, var(--cat-top, var(--tc-green-top)) 0%, var(--cat-bot, var(--tc-green-bot)) 100%);
      box-shadow: 
        inset 0 1.5px 0 rgba(255,255,255,0.45),
        0 3px 0 var(--cat-edge, var(--tc-green-edge));
      text-shadow: 0 1.5px 0 var(--cat-edge, var(--tc-green-edge));
    }

    /* ==========================================
       BOTONES DE RESPUESTA BLANCOS 3D (AU, AG, FE, OR)
       ========================================== */
    .answer-btn {
      position: relative;
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 15px 18px;
      border-radius: 18px;
      border: 2px solid #e2e8f0;
      cursor: pointer;
      user-select: none;
      outline: none;

      background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
      color: #1e293b;
      box-shadow: 
        inset 0 2px 0 #ffffff,
        0 5px 0 #b8c4d4,
        0 8px 14px -3px rgba(0, 0, 0, 0.3);

      transition: transform 0.07s cubic-bezier(0.34, 1.56, 0.64, 1),
                  box-shadow 0.07s cubic-bezier(0.34, 1.56, 0.64, 1),
                  background 0.15s ease,
                  border-color 0.15s ease;
    }

    .answer-btn:hover:not(.is-locked) {
      transform: translateY(-1px);
      border-color: #cbd5e1;
      box-shadow: 
        inset 0 2px 0 #ffffff,
        0 6px 0 #b8c4d4,
        0 12px 18px -3px rgba(0, 0, 0, 0.35);
    }

    .answer-btn:active:not(.is-locked) {
      transform: translateY(3px);
      box-shadow: 
        inset 0 1px 0 #ffffff,
        0 2px 0 #b8c4d4,
        0 3px 6px rgba(0, 0, 0, 0.25);
    }

    /* Tecla numérica izquierda (1, 2, 3, 4) con relieve propio */
    .answer-keycap {
      position: absolute;
      left: 14px;
      width: 30px;
      height: 30px;
      border-radius: 9px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: var(--font-display);
      font-size: 0.9rem;
      font-weight: 700;
      color: #334155;
      background: #e2e8f0;
      border: 1.5px solid #cbd5e1;
      box-shadow: 0 2.5px 0 #b8c4d4;
      transition: all 0.15s ease;
    }

    .answer-label {
      font-family: var(--font-display);
      font-size: 1.2rem;
      font-weight: 700;
      letter-spacing: 0.6px;
      color: #17202e;
    }

    /* Estado Respuesta CORRECTA (Verde Ciencia) */
    .answer-btn.is-correct {
      background: linear-gradient(180deg, var(--tc-green-top) 0%, var(--tc-green-bot) 100%);
      border-color: #55f29b;
      box-shadow: 
        inset 0 2px 0 rgba(255, 255, 255, 0.45),
        0 5px 0 var(--tc-green-edge),
        0 10px 20px rgba(30, 199, 101, 0.35);
    }
    .answer-btn.is-correct .answer-label {
      color: #ffffff;
      text-shadow: 0 2px 0 var(--tc-green-edge);
    }
    .answer-btn.is-correct .answer-keycap {
      background: #13964b;
      border-color: #0e7339;
      color: #ffffff;
      box-shadow: 0 2px 0 #0a5228;
    }

    /* Estado Respuesta INCORRECTA (Rojo Arte) */
    .answer-btn.is-wrong {
      background: linear-gradient(180deg, var(--tc-red-top) 0%, var(--tc-red-bot) 100%);
      border-color: #ff8075;
      box-shadow: 
        inset 0 2px 0 rgba(255, 255, 255, 0.4),
        0 5px 0 var(--tc-red-edge),
        0 10px 20px rgba(230, 37, 20, 0.35);
      animation: wrongShake 0.36s ease;
    }
    .answer-btn.is-wrong .answer-label {
      color: #ffffff;
      text-shadow: 0 2px 0 var(--tc-red-edge);
    }
    .answer-btn.is-wrong .answer-keycap {
      background: #ad1407;
      border-color: #850f05;
      color: #ffffff;
      box-shadow: 0 2px 0 #5e0a03;
    }

    @keyframes wrongShake {
      0%, 100% { transform: translateX(0); }
      25% { transform: translateX(-5px); }
      50% { transform: translateX(5px); }
      75% { transform: translateX(-3px); }
    }

    /* Medidor Circular de Tiempo 3D (Arriba a la derecha) */
    .timer-badge-3d {
      width: 50px;
      height: 50px;
      border-radius: 50%;
      background: linear-gradient(180deg, #2a3444 0%, #1e2632 100%);
      border: 3px solid #3b495e;
      box-shadow: 
        inset 0 2px 0 rgba(255,255,255,0.1),
        0 4px 0 #11161d;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: var(--font-display);
      font-size: 1.15rem;
      font-weight: 700;
      color: #ffffff;
      cursor: pointer;
      user-select: none;
    }
    .theme-papel .timer-badge-3d {
      background: #ffffff;
      border-color: #cbd5e1;
      color: #1e293b;
      box-shadow: 0 4px 0 #94a3b8;
    }

