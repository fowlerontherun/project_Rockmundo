import tempfile

import pytest

from backend.services.radio_service import RadioService
from backend.services.economy_service import EconomyService
from backend.services.analytics_service import AnalyticsService


def setup_services(tmp_path):
    db = tmp_path / "radio.db"
    eco = tmp_path / "eco.db"
    economy = EconomyService(str(eco))
    economy.ensure_schema()
    svc = RadioService(db_path=str(db), economy=economy)
    svc.ensure_schema()
    return svc, economy, AnalyticsService(db_path=str(db))


def test_schedule_and_access_control(tmp_path):
    svc, economy, analytics = setup_services(tmp_path)

    station = svc.create_station(owner_id=1, name="Rock FM")
    sched = svc.schedule_show(station_id=station["id"], title="Morning", start_time="2024-01-01T08:00:00")
    assert sched["station_id"] == station["id"]

    # Subscribe and listen
    svc.subscribe(station["id"], user_id=2)
    count = svc.listen(station["id"], user_id=2)
    assert count == 1
    assert economy.get_balance(1) == 1

    # Analytics should see the listener
    metrics = analytics.kpis("2000-01-01", "2030-12-31")
    assert metrics["radio"]["plays"] == 1

    # Unauthorized listener
    with pytest.raises(PermissionError):
        svc.listen(station["id"], user_id=3)
