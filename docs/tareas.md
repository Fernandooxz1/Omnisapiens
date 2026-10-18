# Tareas — frontend (volátil)

> Una pantalla, nada más. Se borra lo hecho; lo nuevo se agrega al final.
> Al cerrar una tarea: commit + borrarla de acá + dejar la cola de abajo.

## Ahora

- [ ] **Proof de estilos**: aprobar `frontend/design/proof-inicio-partida.html` (inicio +
      partida, tres estados, en Papel y Colorido) y el lenguaje del estilo Colorido tomado de
      `frontend/design/laboratorio_de_botones_juicy_ui_sheen.html`.

## Después

- [ ] `app.css` como dos pieles (`data-skin`) + componentes `Button`, `SkinSwitcher` (estilo) y
      `AccentSlider` (tono `--accent-h`), `CategoryBadge`.
- [ ] Cliente HTTP + sesión (`POST /auth/guest`, token en `sessionStorage`, `GET /me`).
- [ ] Inicio: nick obligatorio, modo principal (arcade) y 1v1, enlace al ranking, selector de
      estilo y slider de acento.
- [ ] Crear/unirse a sala y lobby con código gigante.
- [ ] Cliente WS (`ws.ts`) con reconexión y heartbeat.
- [ ] Pantalla de partida: `AnswerTile`, `TimerRing`, marcador y revelación (espera la pausa
      de 2,5 s del backend).
- [ ] Fin de partida + revancha.
- [ ] Arcade completo (`LifeStrip`, fin con ranking).
- [ ] Ranking global/semanal.
- [ ] Admin de preguntas (token, listado, subida).
- [ ] Sonido, teclado (`1`–`4`, `Enter`) y PWA.
- [ ] Playwright: una partida 1v1 completa y un arcade hasta el final.
- [ ] Errores: `+error.svelte`, `Toast` con `code`/`message` y aviso de API caída.
- [ ] Borrar `frontend/dev/` cuando lobby + arcade anden en SvelteKit.
