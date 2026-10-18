# Tareas — backend (volátil)

> Una pantalla, nada más. Se borra lo hecho; lo nuevo se agrega al final.
> Al cerrar una tarea: commit + borrarla de acá + dejar la cola de abajo.

## Ahora

- [ ] **Pausa de revelación (2,5 s)**: entre `round_result` y la ronda siguiente, y entre
      `arcade_result` y la pregunta siguiente, dormir `reveal_seconds` (setting nuevo,
      default `2.5`) con el `_sleep` ya inyectado. El arranque siguiente y su `ends_at` se
      calculan **después** de la pausa: el reloj no puede gastar la revelación. El final de
      partida no lleva pausa extra. Hoy el hueco medido es de 2 ms, así que el cliente muestra
      el resultado pisado por la ronda nueva. Tests: pausa en 1v1, pausa en arcade, sin pausa
      al terminar. Al cerrar, actualizar `docs/api.md` §"Pedido pendiente al backend".

## Después

- [ ] Nada pedido por ahora.
