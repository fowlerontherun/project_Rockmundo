-- Adds tables for generic items, XP items, and user inventories

CREATE TABLE IF NOT EXISTS item_categories (
    name TEXT PRIMARY KEY,
    description TEXT
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    stats_json TEXT DEFAULT '{}',
    price_cents INTEGER DEFAULT 0,
    stock INTEGER DEFAULT 0,
    FOREIGN KEY (category) REFERENCES item_categories(name)
);

CREATE TABLE IF NOT EXISTS user_items (
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (user_id, item_id),
    FOREIGN KEY (item_id) REFERENCES items(id)
);

CREATE TABLE IF NOT EXISTS xp_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    effect_type TEXT NOT NULL,
    amount REAL NOT NULL,
    duration INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS user_xp_items (
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (user_id, item_id),
    FOREIGN KEY (item_id) REFERENCES xp_items(id)
);

