-- Track dynamic pricing for city shops

CREATE TABLE IF NOT EXISTS shop_item_price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    price_cents INTEGER NOT NULL,
    quantity_sold INTEGER DEFAULT 0,
    recorded_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (shop_id) REFERENCES city_shops(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS shop_book_price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    price_cents INTEGER NOT NULL,
    quantity_sold INTEGER DEFAULT 0,
    recorded_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (shop_id) REFERENCES city_shops(id) ON DELETE CASCADE
);
