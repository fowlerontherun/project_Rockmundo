import sqlite3

from services.mod_marketplace_service import ModMarketplaceService
from services.economy_service import EconomyService
from backend.storage.local import LocalStorage


def test_marketplace_workflow(tmp_path):
    db = tmp_path / "db.sqlite"
    storage_root = tmp_path / "store"
    storage = LocalStorage(root=str(storage_root), public_base_url="http://mods")
    economy = EconomyService(db_path=str(db))
    economy.ensure_schema()

    svc = ModMarketplaceService(db_path=str(db), storage=storage, economy=economy)
    svc.ensure_schema()

    # give buyer some funds
    economy.deposit(user_id=1, amount_cents=1000)

    # author publishes a mod
    mod_id = svc.publish_mod(
        author_id=2,
        name="Cool Mod",
        description="",
        price_cents=500,
        file_bytes=b"hello mod",
        content_type="text/plain",
    )
    pending = svc.list_pending_mods()
    assert pending and pending[0]["id"] == mod_id

    # admin approves
    svc.approve_mod(mod_id)

    # buyer purchases / downloads
    url = svc.download_mod(user_id=1, mod_id=mod_id)
    assert url.endswith(".mod")

    # ownership recorded
    with sqlite3.connect(str(db)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM mod_ownership WHERE mod_id=? AND user_id=?", (mod_id, 1))
        assert cur.fetchone()[0] == 1

    # economy transfer
    assert economy.get_balance(1) == 500
    assert economy.get_balance(2) == 500

    # rating
    svc.rate_mod(user_id=1, mod_id=mod_id, rating=4)
    with sqlite3.connect(str(db)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT rating_sum, rating_count FROM mods WHERE id=?", (mod_id,))
        rs, rc = cur.fetchone()
        assert rs == 4 and rc == 1
