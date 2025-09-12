import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "backend"))

from services.analytics_service import AnalyticsService


def test_data_analytics_skill_improves_forecast_accuracy():
    svc = AnalyticsService()
    history = [100, 120, 80, 110]
    actual_next = 115

    low = svc.sales_forecast(1, history)
    low_error = abs(low["forecast"] - actual_next)

    for _ in range(5):
        svc.sales_forecast(2, history)
    high = svc.sales_forecast(2, history)
    high_error = abs(high["forecast"] - actual_next)

    assert high_error < low_error
    assert "confidence" in high
    assert "confidence" not in low
