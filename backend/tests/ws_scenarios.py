"""Los escenarios vivos que congelan los transcripts y revisa el test de fuga.

Un solo lugar para recorrer el protocolo actual: el golden compara el orden y
el contenido, y el test de fuga mira esos mismos mensajes antes de la revelación.
"""

import uuid
from typing import Any

from .factories import quiz_content
from .ws_client import WebSocketClient


class Transcript:
    """Lo recibido por cada cliente, normalizado para que el JSONL sea estable.

    Los ids y los `ends_at` cambian en cada partida; el resto del contenido no.
    Los ids se numeran en orden de aparición y los tiempos se guardan como
    desplazamiento desde el arranque del escenario.
    """

    def __init__(self, *, base_ms: int) -> None:
        self._base_ms = base_ms
        self._ids: dict[str, str] = {}
        self._streams: dict[str, list[dict[str, Any]]] = {}

    def wrap(self, who: str, socket: WebSocketClient) -> "RecordingSocket":
        self._streams.setdefault(who, [])
        return RecordingSocket(socket, who, self)

    def add(self, who: str, message: dict[str, Any]) -> None:
        normalized = self._normalize(message)
        if normalized.get("t") == "room_state":
            normalized["d"]["code"] = "<room_code>"
        self._streams[who].append(normalized)

    def lines(self) -> list[dict[str, Any]]:
        return [
            {"who": who} | message
            for who, messages in self._streams.items()
            for message in messages
        ]

    def _normalize(self, value: Any, key: str | None = None) -> Any:
        if isinstance(value, dict):
            return {name: self._normalize(item, name) for name, item in value.items()}
        if isinstance(value, list):
            return [self._normalize(item) for item in value]
        if key == "ends_at" and isinstance(value, int):
            return f"<ends_at:{value - self._base_ms}>"
        if isinstance(value, str):
            try:
                parsed = uuid.UUID(value)
            except ValueError:
                return value
            return self._placeholder(parsed)
        return value

    def _placeholder(self, parsed: uuid.UUID) -> str:
        known = self._ids.get(str(parsed))
        if known is None:
            known = f"<id:{len(self._ids) + 1}>"
            self._ids[str(parsed)] = known
        return known


class RecordingSocket:
    """Un socket de test que anota todo lo que recibe, también lo que saltea."""

    def __init__(
        self, socket: WebSocketClient, who: str, transcript: Transcript
    ) -> None:
        self._socket = socket
        self._who = who
        self._transcript = transcript

    async def send(self, payload: dict[str, Any]) -> None:
        await self._socket.send(payload)

    async def receive(self) -> dict[str, Any]:
        message = await self._socket.receive()
        self._transcript.add(self._who, message)
        return message

    async def until(self, tipo: str) -> dict[str, Any]:
        while True:
            message = await self.receive()
            if message["t"] == tipo:
                return message


async def _sembrar_arcade(session: Any) -> None:
    """Cuatro preguntas con ids fijos: el orden del golden no depende del azar."""
    pares = [
        quiz_content(
            id=uuid.UUID(int=100 + indice),
            category="geography",
            difficulty=1,
            status="published",
            prompt=f"pregunta {indice}",
            options=["correcta", "a", "b", "c"],
            correct_index=0,
        )
        for indice in range(4)
    ]
    session.add_all([fila for par in pares for fila in par])
    await session.flush()


async def arcade_complete(api: Any, connect: Any) -> Transcript:
    """Partida hasta perder las tres vidas: un acierto, dos errores y un vencimiento."""
    await _sembrar_arcade(api.session)
    transcript = Transcript(base_ms=api.clock.now_ms())

    async with connect(api.user) as raw:
        socket = transcript.wrap("ana", raw)
        await socket.send({"t": "start"})
        await socket.until("arcade_start")

        for indice in range(4):
            pregunta = await socket.until("arcade_question")
            if indice == 2:
                # La tercera vida se va por vencimiento, sin respuesta.
                api.clock.advance(pregunta["d"]["ends_at"] - api.clock.now_ms())
                await socket.until("arcade_result")
                continue

            opciones: list[str] = pregunta["d"]["options"]
            correcta = opciones.index("correcta")
            eleccion = correcta if indice == 0 else (correcta + 1) % 4
            await socket.send(
                {
                    "t": "answer",
                    "d": {"round": pregunta["d"]["round"], "choice": eleccion},
                }
            )
            await socket.until("arcade_result")

        await socket.until("arcade_end")

    return transcript


async def session_complete(api: Any, connect: Any) -> Transcript:
    """La misma partida que el arcade, por el canal canónico."""
    await _sembrar_arcade(api.session)
    transcript = Transcript(base_ms=api.clock.now_ms())
    session_id = await api.create()

    async with connect(session_id) as raw:
        socket = transcript.wrap("ana", raw)
        inicio = await socket.until("session_start")
        assert inicio["d"]["mode"] == "trivia_arcade"

        for indice in range(4):
            item = await socket.until("item_start")
            if indice == 2:
                # La tercera vida se va por vencimiento, sin respuesta.
                api.clock.advance(item["d"]["ends_at"] - api.clock.now_ms())
                await socket.until("item_result")
                continue

            opciones: list[str] = item["d"]["payload"]["options"]
            correcta = opciones.index("correcta")
            eleccion = correcta if indice == 0 else (correcta + 1) % 4
            await socket.send(
                {
                    "t": "answer",
                    "d": {"round": item["d"]["position"], "choice": eleccion},
                }
            )
            await socket.until("item_result")

        await socket.until("session_end")

    return transcript


async def versus_complete(api: Any, connect: Any) -> Transcript:
    """Partida 1v1 de tres rondas: Ana acierta y Beto no."""
    transcript = Transcript(base_ms=api.harness.clock.now_ms())

    async with connect(api.host) as raw_ana:
        ana = transcript.wrap("ana", raw_ana)
        await ana.until("room_state")

        async with connect(api.guest) as raw_beto:
            beto = transcript.wrap("beto", raw_beto)
            await ana.until("room_state")
            await beto.until("room_state")

            await ana.send({"t": "start"})
            await ana.until("match_start")
            await beto.until("match_start")

            for ronda in range(3):
                await ana.until("round_start")
                await beto.until("round_start")
                await ana.send({"t": "answer", "d": {"round": ronda, "choice": 1}})
                await beto.send({"t": "answer", "d": {"round": ronda, "choice": 0}})
                await ana.until("round_result")
                await beto.until("round_result")

            await ana.until("match_end")
            await beto.until("match_end")

    return transcript


async def versus_reconnect(api: Any, connect: Any) -> Transcript:
    """Beto se cae, corre la gracia y vuelve a tiempo para cerrar la ronda."""
    transcript = Transcript(base_ms=api.harness.clock.now_ms())

    async with connect(api.host) as raw_ana:
        ana = transcript.wrap("ana", raw_ana)
        await ana.until("room_state")

        async with connect(api.guest) as raw_beto:
            beto = transcript.wrap("beto", raw_beto)
            await ana.until("room_state")
            await beto.until("room_state")

            await ana.send({"t": "start"})
            await ana.until("match_start")
            await beto.until("match_start")
            await ana.until("round_start")
            await beto.until("round_start")

        await ana.until("reconnect_pending")
        api.harness.clock.advance(5_000)

        async with connect(api.guest) as raw_vuelta:
            vuelta = transcript.wrap("beto", raw_vuelta)
            await ana.until("opponent_returned")
            await vuelta.until("room_state")
            await vuelta.until("round_start")

            await ana.send({"t": "answer", "d": {"round": 0, "choice": 1}})
            await vuelta.send({"t": "answer", "d": {"round": 0, "choice": 0}})
            await ana.until("round_result")
            await vuelta.until("round_result")

    return transcript


ESCENARIOS = {
    "arcade_complete": arcade_complete,
    "session_complete": session_complete,
    "versus_complete": versus_complete,
    "versus_reconnect": versus_reconnect,
}


def es_revelacion(message: dict[str, Any]) -> bool:
    """Los únicos mensajes que pueden llevar la solución."""
    return message["t"] in {
        "round_result",
        "arcade_result",
        "match_end",
        "arcade_end",
        "item_result",
        "session_end",
    }
