from backend.services.production_service import ProductionService


class FakeEconomy:
    def __init__(self):
        self.deposits = []

    def deposit(self, user_id: int, amount_cents: int) -> None:
        self.deposits.append((user_id, amount_cents))


class FakeAnalytics:
    def __init__(self):
        self.sales = []
        self.charts = []

    def record_sale(self, track_id: int, sales: int) -> None:
        self.sales.append((track_id, sales))

    def update_charts(self, track_id: int, sales: int) -> None:
        self.charts.append(track_id)


def test_end_to_end_release_flow():
    economy = FakeEconomy()
    analytics = FakeAnalytics()
    svc = ProductionService(economy, analytics)

    track = svc.create_track("My Song", band_id=1, duration_sec=180)
    svc.schedule_session(track.id, "2024-01-01", "Jane", hours=5, hourly_rate_cents=1000)
    svc.mix_track(track.id, "Bob", cost_cents=2000)

    # Verify cost calculation
    assert svc.production_cost(track.id) == 5 * 1000 + 2000

    release = svc.release_track(
        track.id,
        "2024-02-01",
        ["digital"],
        price_cents=150,
        sales=10,
    )

    assert release.sales == 10
    assert economy.deposits == [(1, 1500)]
    assert analytics.sales == [(track.id, 10)]
    assert analytics.charts == [track.id]
    assert svc.get_track(track.id).release == release
