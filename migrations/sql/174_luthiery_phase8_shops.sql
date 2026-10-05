-- Phase 8 player Luthier shop and serialized stock listings.
CREATE TABLE IF NOT EXISTS luthier_shops (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 owner_character_id INTEGER NOT NULL UNIQUE,
 name TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '',
 city_id INTEGER,
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN(0,1)),
 created_at TEXT NOT NULL DEFAULT(datetime('now'))
);
CREATE TABLE IF NOT EXISTS luthier_shop_listings (
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
 FOREIGN KEY(crafted_item_id) REFERENCES crafted_items(id),
 UNIQUE(crafted_item_id,status)
);
CREATE INDEX IF NOT EXISTS ix_luthier_shop_active ON luthier_shop_listings(shop_id,status,created_at);
