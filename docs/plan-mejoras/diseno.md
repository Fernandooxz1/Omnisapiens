# Diseño de Mejoras: Juiciness, Feedback y Contenido

Este documento detalla las especificaciones técnicas y estéticas para las mejoras de Omnisapiens.

---

## 1. Principios de Animación y Juiciness (Pizarra Cálida)

Todas las animaciones deben respetar las normas de [`docs/diseno.md`](../diseno.md):
- **Cero emojis.** Todos los íconos son SVG nativos (grid 24, trazo 2.5, `currentColor`).
- **Cero degradados.** El volumen proviene del bisel y la base sólida.
- **Micro-interacciones reactivas:** La animación responde a la interacción del usuario (pulsación, acierto, error, racha, pérdida de vida), nunca en bucles infinitos molestos.
- **Accesibilidad:** Todo efecto visual debe respetar `@media (prefers-reduced-motion: reduce)` deshabilitando movimientos bruscos o sacudidas.

---

## 2. Especificación Técnica de Componentes

### 2.1. Acierto y Error (`AnswerTile`)
- **Acierto:** Al activarse `is-correct`, la opción ejecuta una animación `@keyframes tile-pop` (escala sutil a `1.04` y retorno elástico en `0.24s`). El bisel superior y la sombra dura acentúan el relieve.
- **Error:** Se mantiene `tile-shake` en la tecla elegida incorrectamente.
- **Haptics:** Módulo `frontend/src/lib/haptics.ts`:
  - `haptics.tap()`: 12 ms al tocar/seleccionar.
  - `haptics.success()`: 40 ms al acertar.
  - `haptics.error()`: patrón `[35, 50, 35]` al fallar.
  - Comprueba `typeof navigator !== 'undefined' && 'vibrate' in navigator`.

### 2.2. Vidas (`LifeStrip`)
- Al perder una vida (cambio a `is-off`), el corazón ejecuta `@keyframes heart-break`:
  - Sacudida horizontal rápida (`±3px`) y salto leve hacia arriba (`-4px`) antes de desvanecerse a gris opaco (`opacity: 0.2`).

### 2.3. Racha y Puntos Flotantes
- **Racha:** Nuevo ícono `flame` en `Icon.svelte`. Cuando `streak >= 2`, el contador de racha en `ArcadeScreen` muestra la llama y pulsa suavemente al incrementarse.
- **Puntos flotantes (`+pts`):** Elemento temporal con clase `.points-floater` que se renderiza al resolver la ronda, flotando hacia arriba `20px` y desvaneciéndose en `0.8s`.
- **Interpolación de puntaje:** El puntaje principal en pantalla no salta en seco, sino que interpola rápidamente su valor en ~250 ms.

### 2.4. Celebración de Fin de Partida
- **Confetti:** Implementación de partículas sin dependencias pesadas mediante `<canvas>` superpuesto o SVG flotante. Disparado solo ante `isNewBest` (en Arcade) o victoria en 1v1.
- **Conteo de Récord:** Animación ascendente del número del récord en la pantalla final (`ArcadeScreen`).

---

## 3. Especificación de Contenido (Batch 4)

- Archivo: `backend/seeds/questions_batch_4.csv`.
- Estructura exacta requerida por `docs/preguntas.md`:
  `category,difficulty,prompt,option_a,option_b,option_c,option_d,correct,explanation,source,tags`
- 150 a 200 preguntas balanceadas entre las 6 categorías (`geography`, `history`, `science`, `art`, `entertainment`, `sports`).
- Dificultades calibradas 1 a 5.
- Explicaciones pedagógicas y curiosas en `explanation`.
- Validación obligatoria con `python -m tools.check_seeds`.
