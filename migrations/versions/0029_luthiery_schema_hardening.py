"""Forward-safe Luthiery schema repair for Phases 4, 7 and 8."""
from alembic import op

revision = "0029_luth_harden"
down_revision = "0028_172"
branch_labels = None
depends_on = None

def _columns(conn, table: str) -> set[str]:
    try:
        return {str(row[1]) for row in conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()}
    except Exception:
        return set()

def upgrade() -> None:
    conn = op.get_bind()
    cols = _columns(conn, "crafted_items")
    if cols and "rework_count" not in cols:
        conn.exec_driver_sql("ALTER TABLE crafted_items ADD COLUMN rework_count INTEGER NOT NULL DEFAULT 0 CHECK (rework_count >= 0)")
    if cols and "locked" not in cols:
        conn.exec_driver_sql("ALTER TABLE crafted_items ADD COLUMN locked INTEGER NOT NULL DEFAULT 0 CHECK (locked IN (0,1))")
    conn.exec_driver_sql("""CREATE TABLE IF NOT EXISTS crafted_item_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crafted_item_id INTEGER NOT NULL,
        character_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        details_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (crafted_item_id) REFERENCES crafted_items(id) ON DELETE CASCADE
    )""")
    conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_crafted_item_events_item ON crafted_item_events(crafted_item_id, created_at)")
    conn.exec_driver_sql("""CREATE TABLE IF NOT EXISTS character_equipped_crafted_instruments (
        character_id INTEGER PRIMARY KEY,
        crafted_item_id INTEGER NOT NULL UNIQUE,
        equipped_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (crafted_item_id) REFERENCES crafted_items(id) ON DELETE CASCADE
    )""")
    conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_equipped_crafted_item ON character_equipped_crafted_instruments(crafted_item_id)")
    conn.exec_driver_sql("""CREATE TABLE IF NOT EXISTS luthier_shops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_character_id INTEGER NOT NULL UNIQUE,
        name TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        city_id INTEGER,
        active INTEGER NOT NULL DEFAULT 1 CHECK(active IN(0,1)),
        created_at TEXT NOT NULL DEFAULT(datetime('now'))
    )""")
    conn.exec_driver_sql("""CREATE TABLE IF NOT EXISTS luthier_shop_listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_id INTEGER NOT NULL,
        crafted_item_id INTEGER NOT NULL,
        seller_character_id INTEGER NOT NULL,
        price_cents INTEGER NOT NULL CHECK(price_cents>0),
        status TEXT NOT NULL DEFAULT 'active' CHECK(status IN('active','sold','withdrawn')),
        buyer_character_id INTEGER,
        created_at TEXT NOT NULL DEFAULT(datetime('now')),
        sold_at TEXT,
        FOREIGN KEY(shop_id) REFERENCES luthier_shops(id),
        FOREIGN KEY(crafted_item_id) REFERENCES crafted_items(id)
    )""")
    conn.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS ux_luthier_active_item ON luthier_shop_listings(crafted_item_id) WHERE status='active'")
    conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_luthier_shop_active ON luthier_shop_listings(shop_id,status,created_at)")

def downgrade() -> None:
    # This repair migration intentionally preserves player-created data.
    pass
