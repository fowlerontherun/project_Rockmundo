-- Phase 4 Luthiery persistent crafting engine and provenance.

CREATE TABLE IF NOT EXISTS crafted_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_number TEXT NOT NULL UNIQUE,
    creator_character_id INTEGER NOT NULL,
    owner_character_id INTEGER NOT NULL,
    instrument_type TEXT NOT NULL CHECK (instrument_type IN ('guitar','bass')),
    shape_key TEXT NOT NULL,
    name TEXT NOT NULL,
    primary_colour TEXT NOT NULL DEFAULT '#202020',
    accent_colour TEXT,
    finish_key TEXT NOT NULL DEFAULT 'luthier.finish.solid',
    quality_score REAL NOT NULL CHECK (quality_score BETWEEN 0 AND 100),
    quality_tier TEXT NOT NULL,
    skill_snapshot_json TEXT NOT NULL DEFAULT '{}',
    workshop_snapshot_json TEXT NOT NULL DEFAULT '{}',
    traits_json TEXT NOT NULL DEFAULT '[]',
    stat_modifiers_json TEXT NOT NULL DEFAULT '{}',
    condition_percent INTEGER NOT NULL DEFAULT 100 CHECK (condition_percent BETWEEN 0 AND 100),
    locked INTEGER NOT NULL DEFAULT 0 CHECK (locked IN (0,1)),
    rework_count INTEGER NOT NULL DEFAULT 0 CHECK (rework_count >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (shape_key) REFERENCES instrument_shapes(key)
);

CREATE TABLE IF NOT EXISTS crafted_item_parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crafted_item_id INTEGER NOT NULL,
    part_type TEXT NOT NULL CHECK (part_type IN ('body','neck','fretboard','electronics','hardware')),
    material_key TEXT,
    component_key TEXT,
    quality_contribution REAL NOT NULL DEFAULT 0,
    UNIQUE(crafted_item_id, part_type),
    FOREIGN KEY (crafted_item_id) REFERENCES crafted_items(id) ON DELETE CASCADE,
    FOREIGN KEY (material_key) REFERENCES crafting_materials(key),
    FOREIGN KEY (component_key) REFERENCES crafting_component_designs(key)
);

CREATE TABLE IF NOT EXISTS crafting_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    request_token TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('pending','completed','failed')),
    crafted_item_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    UNIQUE(character_id, request_token),
    FOREIGN KEY (crafted_item_id) REFERENCES crafted_items(id)
);

CREATE INDEX IF NOT EXISTS ix_crafted_items_owner ON crafted_items(owner_character_id, created_at);
CREATE INDEX IF NOT EXISTS ix_crafted_items_creator ON crafted_items(creator_character_id, created_at);

CREATE TABLE IF NOT EXISTS crafted_item_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crafted_item_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (crafted_item_id) REFERENCES crafted_items(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_crafted_item_events_item ON crafted_item_events(crafted_item_id, created_at);
