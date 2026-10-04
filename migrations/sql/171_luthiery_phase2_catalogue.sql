-- Phase 2 Luthiery materials/component catalogue and character-owned stock.

CREATE TABLE IF NOT EXISTS crafting_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    material_type TEXT NOT NULL,
    rarity TEXT NOT NULL DEFAULT 'common',
    cost_cents INTEGER NOT NULL CHECK (cost_cents >= 0),
    quality REAL NOT NULL DEFAULT 1.0,
    stat_affinities_json TEXT NOT NULL DEFAULT '{}',
    instrument_compatibility_json TEXT NOT NULL DEFAULT '["guitar","bass"]',
    required_skill TEXT NOT NULL DEFAULT 'luthiery',
    required_level INTEGER NOT NULL DEFAULT 1 CHECK (required_level BETWEEN 1 AND 100),
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0,1))
);

CREATE TABLE IF NOT EXISTS crafting_component_designs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    part_type TEXT NOT NULL CHECK (part_type IN ('body','neck','fretboard','electronics','hardware')),
    rarity TEXT NOT NULL DEFAULT 'common',
    cost_cents INTEGER NOT NULL CHECK (cost_cents >= 0),
    quality REAL NOT NULL DEFAULT 1.0,
    stat_affinities_json TEXT NOT NULL DEFAULT '{}',
    instrument_compatibility_json TEXT NOT NULL DEFAULT '["guitar","bass"]',
    required_skill TEXT NOT NULL DEFAULT 'luthiery',
    required_level INTEGER NOT NULL DEFAULT 1 CHECK (required_level BETWEEN 1 AND 100),
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0,1))
);

CREATE TABLE IF NOT EXISTS instrument_shapes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    instrument_type TEXT NOT NULL CHECK (instrument_type IN ('guitar','bass')),
    required_skill TEXT NOT NULL DEFAULT 'luthiery',
    required_level INTEGER NOT NULL DEFAULT 1 CHECK (required_level BETWEEN 1 AND 100),
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0,1))
);

CREATE TABLE IF NOT EXISTS crafting_unlocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_key TEXT NOT NULL UNIQUE,
    content_type TEXT NOT NULL,
    required_skill TEXT NOT NULL,
    required_level INTEGER NOT NULL CHECK (required_level BETWEEN 1 AND 100),
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0,1))
);

CREATE TABLE IF NOT EXISTS character_crafting_materials (
    character_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    PRIMARY KEY (character_id, material_id),
    FOREIGN KEY (material_id) REFERENCES crafting_materials(id)
);

CREATE TABLE IF NOT EXISTS luthier_supplier_stock (
    material_id INTEGER PRIMARY KEY,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    FOREIGN KEY (material_id) REFERENCES crafting_materials(id)
);

CREATE TABLE IF NOT EXISTS material_purchase_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_cost_cents INTEGER NOT NULL CHECK (unit_cost_cents >= 0),
    total_cost_cents INTEGER NOT NULL CHECK (total_cost_cents >= 0),
    purchased_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (material_id) REFERENCES crafting_materials(id)
);

CREATE INDEX IF NOT EXISTS ix_material_purchase_character
    ON material_purchase_history(character_id, purchased_at);
