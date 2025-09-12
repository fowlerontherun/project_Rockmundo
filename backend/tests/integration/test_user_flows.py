from backend.services import event_service


def test_registration_event_transaction_flow(client, db_path, monkeypatch):
    # register user
    r = client.post("/auth/register", json={"email": "user@example.com", "password": "Secretpass1", "display_name": "User"})
    assert r.status_code == 200
    uid = r.json()["id"]

    # trigger event with deterministic outcome
    monkeypatch.setattr(event_service.random, "random", lambda: 0.0)
    r = client.post("/events/daily-roll", params={"user_id": uid})
    assert r.status_code == 200
    assert r.json()["event"]["event"] == "vocal fatigue"

    # transaction flow
    r = client.post("/payment/purchase", json={"user_id": uid, "amount_cents": 500})
    pid = r.json()["payment_id"]
    r = client.post("/payment/callback", json={"payment_id": pid})
    assert r.status_code == 200
    assert r.json()["status"] == "completed"

    from backend.services.economy_service import EconomyService
    econ = EconomyService(db_path)
    assert econ.get_balance(uid) > 0
