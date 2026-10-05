"""Repair legacy Luthier listing uniqueness without losing sale history."""
from alembic import op

revision="0030_luth_listing_history"
down_revision="0029_luth_harden"
branch_labels=None
depends_on=None

def upgrade()->None:
 conn=op.get_bind()
 row=conn.exec_driver_sql("SELECT sql FROM sqlite_master WHERE type='table' AND name='luthier_shop_listings'").fetchone()
 ddl=(row[0] if row else "") or ""
 legacy="UNIQUE(crafted_item_id,status)" in ddl.replace(" ","")
 if not legacy:
  conn.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS ux_luthier_active_item ON luthier_shop_listings(crafted_item_id) WHERE status='active'")
  return
 conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
 conn.exec_driver_sql("""CREATE TABLE luthier_shop_listings_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT, shop_id INTEGER NOT NULL, crafted_item_id INTEGER NOT NULL,
  seller_character_id INTEGER NOT NULL, price_cents INTEGER NOT NULL CHECK(price_cents>0),
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN('active','sold','withdrawn')),
  buyer_character_id INTEGER, created_at TEXT NOT NULL DEFAULT(datetime('now')), sold_at TEXT,
  FOREIGN KEY(shop_id) REFERENCES luthier_shops(id), FOREIGN KEY(crafted_item_id) REFERENCES crafted_items(id))""")
 conn.exec_driver_sql("""INSERT INTO luthier_shop_listings_new
  (id,shop_id,crafted_item_id,seller_character_id,price_cents,status,buyer_character_id,created_at,sold_at)
  SELECT id,shop_id,crafted_item_id,seller_character_id,price_cents,status,buyer_character_id,created_at,sold_at FROM luthier_shop_listings""")
 conn.exec_driver_sql("DROP TABLE luthier_shop_listings")
 conn.exec_driver_sql("ALTER TABLE luthier_shop_listings_new RENAME TO luthier_shop_listings")
 conn.exec_driver_sql("CREATE UNIQUE INDEX ux_luthier_active_item ON luthier_shop_listings(crafted_item_id) WHERE status='active'")
 conn.exec_driver_sql("CREATE INDEX ix_luthier_shop_active ON luthier_shop_listings(shop_id,status,created_at)")
 conn.exec_driver_sql("PRAGMA foreign_keys=ON")

def downgrade()->None:
 pass
