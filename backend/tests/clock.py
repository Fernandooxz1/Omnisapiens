"""Reloj de test que el test mueve a mano.

`sleep` registra el vencimiento y se queda ahí: el tiempo no pasa solo. El test
avanza la hora y despierta a los que ya vencieron. Así una partida o una corrida
entera por vencimientos corre en milisegundos.

Dos detalles cubren la carrera entre el test y la tarea que duerme:

- El vencimiento se calcula **al llamar** a `sleep`, no al ejecutar la corrutina.
- Si el test adelantó la hora antes de que la corrutina se registre, el registro
  ya nace vencido y se resuelve en el acto.
"""

import asyncio
from collections.abc import Coroutine


class FakeClock:
    def __init__(self, start: int = 1_000_000) -> None:
        self.ms = start
        self._durmiendo: list[tuple[int, asyncio.Future[None]]] = []

    def now_ms(self) -> int:
        return self.ms

    def sleep(self, seconds: float) -> Coroutine[object, object, None]:
        vence = self.ms + int(seconds * 1000)

        async def _dormir() -> None:
            futuro: asyncio.Future[None] = asyncio.get_running_loop().create_future()
            if vence <= self.ms:
                futuro.set_result(None)
            self._durmiendo.append((vence, futuro))
            try:
                await futuro
            finally:
                self._durmiendo = [
                    (d, f) for d, f in self._durmiendo if f is not futuro
                ]

        return _dormir()

    def advance(self, ms: int) -> None:
        self.ms += ms
        for vence, futuro in self._durmiendo:
            if vence <= self.ms and not futuro.done():
                futuro.set_result(None)
