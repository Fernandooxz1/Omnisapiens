"""Las formas del protocolo: el sobre, y que la respuesta no filtra nada."""

from app.game.protocols import (
    Error,
    MatchEnd,
    MatchStart,
    PlayerView,
    Pong,
    ReconnectPending,
    RoomState,
    RoundChoice,
    RoundResult,
    RoundStart,
    Scores,
    encode,
)


def test_encode_wraps_type_and_data() -> None:
    mensaje = Pong()

    assert encode(mensaje) == {"t": "pong", "d": {}}


def test_encode_correlates_with_an_id_when_asked() -> None:
    assert encode(Pong(), id="7") == {"t": "pong", "d": {}, "id": "7"}


def test_room_state_serializes_players_and_you() -> None:
    estado = RoomState(
        code="K7M2QP",
        status="waiting",
        config={"rounds": 5, "seconds": 20},
        you=PlayerView(id="a", nick="ana"),
        players=[PlayerView(id="a", nick="ana"), PlayerView(id="b", nick="beto")],
        match_id=None,
    )

    assert encode(estado) == {
        "t": "room_state",
        "d": {
            "code": "K7M2QP",
            "status": "waiting",
            "config": {"rounds": 5, "seconds": 20},
            "you": {"id": "a", "nick": "ana"},
            "players": [
                {"id": "a", "nick": "ana"},
                {"id": "b", "nick": "beto"},
            ],
            "match_id": None,
        },
    }


def test_round_start_has_no_correct_index() -> None:
    ronda = RoundStart(
        round=0,
        question_id="q1",
        prompt="¿Cuál es el río más largo?",
        options=["Paraná", "Amazonas", "Orinoco", "Magdalena"],
        category="geography",
        difficulty=2,
        ends_at=1_700_000_000_000,
        total_seconds=20,
    )

    cuerpo = encode(ronda)["d"]

    assert "correct_index" not in cuerpo
    assert cuerpo["options"] == ["Paraná", "Amazonas", "Orinoco", "Magdalena"]


def test_round_result_carries_everything_for_the_reveal() -> None:
    resultado = RoundResult(
        round=0,
        correct_index=1,
        explanation="El Amazonas es el más caudaloso.",
        you=RoundChoice(choice=1, ms=3_000, points=145, correct=True),
        opponent=RoundChoice(choice=0, ms=9_000, points=0, correct=False),
        scores=Scores(you=145, opponent=0),
    )

    assert encode(resultado)["d"] == {
        "round": 0,
        "correct_index": 1,
        "explanation": "El Amazonas es el más caudaloso.",
        "you": {"choice": 1, "ms": 3_000, "points": 145, "correct": True},
        "opponent": {"choice": 0, "ms": 9_000, "points": 0, "correct": False},
        "scores": {"you": 145, "opponent": 0},
    }


def test_match_end_reuses_round_results() -> None:
    fin = MatchEnd(
        winner="you",
        scores=Scores(you=290, opponent=0),
        rounds=[],
        reason="completed",
    )

    assert encode(fin)["d"]["winner"] == "you"
    assert encode(fin)["d"]["reason"] == "completed"


def test_reconnect_pending_carries_the_grace() -> None:
    assert encode(ReconnectPending(seconds_left=20))["d"] == {"seconds_left": 20}


def test_error_uses_the_api_format() -> None:
    assert encode(Error(code="ROOM_NOT_FOUND", message="No hay sala."))["d"] == {
        "code": "ROOM_NOT_FOUND",
        "message": "No hay sala.",
    }


def test_match_start_carries_the_total_rounds() -> None:
    inicio = MatchStart(
        match_id="m1", config={"rounds": 5, "seconds": 20}, rounds_total=5
    )

    assert encode(inicio)["d"]["rounds_total"] == 5
