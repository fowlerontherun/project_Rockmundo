-- File: backend/migrations/033_merch.sql
-- Basic merch store: products, SKUs (size/color), orders, items, refunds

CREATE TABLE IF NOT EXISTS merch_products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  band_id INTEGER,                   -- optional: which band/brand
  name TEXT NOT NULL,
  description TEXT,
  category TEXT NOT NULL,            -- 'tshirt','hoodie','poster','sticker','hat', etc.
  image_url TEXT,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS merch_skus (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER NOT NULL,
  option_size TEXT,                  -- e.g., 'S','M','L','XL','A3' (posters), null if N/A
  option_color TEXT,                 -- e.g., 'Black','White','Navy', null if N/A
  price_cents INTEGER NOT NULL,
  currency TEXT DEFAULT 'USD',
  stock_qty INTEGER NOT NULL DEFAULT 0,
  barcode TEXT,                      -- optional external SKU/barcode
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT,
  FOREIGN KEY(product_id) REFERENCES merch_products(id)
);

CREATE TABLE IF NOT EXISTS merch_orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  buyer_user_id INTEGER NOT NULL,
  total_cents INTEGER NOT NULL,
  currency TEXT DEFAULT 'USD',
  status TEXT NOT NULL DEFAULT 'confirmed',   -- pending|confirmed|refunded|cancelled
  shipping_address TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS merch_order_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL,
  sku_id INTEGER NOT NULL,
  unit_price_cents INTEGER NOT NULL,
  qty INTEGER NOT NULL,
  refunded_qty INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(order_id) REFERENCES merch_orders(id),
  FOREIGN KEY(sku_id) REFERENCES merch_skus(id)
);

CREATE TABLE IF NOT EXISTS merch_refunds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL,
  amount_cents INTEGER NOT NULL,
  reason TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(order_id) REFERENCES merch_orders(id)
);

CREATE INDEX IF NOT EXISTS ix_merch_skus_product ON merch_skus(product_id);
CREATE INDEX IF NOT EXISTS ix_merch_items_order ON merch_order_items(order_id);
CREATE INDEX IF NOT EXISTS ix_merch_items_sku ON merch_order_items(sku_id);
