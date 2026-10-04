from fastapi import HTTPException

from routes.tour_routes import _require_band_member


class FakeBandService:
    def get_band_info(self, band_id):
        return {"id": band_id, "members": [{"user_id": 101}, {"user_id": 202}]}


def test_tour_band_member_accepts_selected_character(monkeypatch):
    import routes.tour_routes as routes
    monkeypatch.setattr(routes, "_band_service", FakeBandService())
    _require_band_member(7, 202)


def test_tour_band_member_rejects_other_character(monkeypatch):
    import routes.tour_routes as routes
    monkeypatch.setattr(routes, "_band_service", FakeBandService())
    try:
        _require_band_member(7, 303)
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("cross-character band control was allowed")
