-- Phase 7 authoritative equipped crafted instrument relation.
CREATE TABLE IF NOT EXISTS character_equipped_crafted_instruments (
 character_id INTEGER PRIMARY KEY,
 crafted_item_id INTEGER NOT NULL UNIQUE,
 equipped_at TEXT NOT NULL DEFAULT (datetime('now')),
 FOREIGN KEY (crafted_item_id) REFERENCES crafted_items(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_equipped_crafted_item ON character_equipped_crafted_instruments(crafted_item_id);
