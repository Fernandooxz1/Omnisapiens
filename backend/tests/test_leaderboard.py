"""El corte semanal del ranking: lunes 00:00 en Buenos Aires, no en UTC."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.services.leaderboard import week_start

BUENOS_AIRES = ZoneInfo("America/Argentina/Buenos_Aires")


def test_the_week_starts_on_monday_midnight_local() -> None:
    # 2026-10-17 es sábado: 12:00 UTC son las 09:00 en Buenos Aires.
    assert week_start(datetime(2026, 10, 17, 12, 0, tzinfo=UTC)) == datetime(
        2026, 10, 12, 0, 0, tzinfo=BUENOS_AIRES
    )


def test_monday_midnight_opens_the_week_and_the_second_before_closes_the_last() -> None:
    lunes = datetime(2026, 10, 12, 0, 0, tzinfo=BUENOS_AIRES)

    assert week_start(lunes) == lunes
    assert week_start(lunes - timedelta(seconds=1)) == datetime(
        2026, 10, 5, 0, 0, tzinfo=BUENOS_AIRES
    )
