-- Luthiery production schema hardening: persistent live controls, provenance and admin audit.
CREATE TABLE IF NOT EXISTS luthiery_live_config (
 key TEXT PRIMARY KEY,value_json TEXT NOT NULL,updated_at TEXT NOT NULL DEFAULT(datetime('now'))
);
CREATE TABLE IF NOT EXISTS luthiery_trait_controls (
 trait_key TEXT PRIMARY KEY,enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1))
);
CREATE TABLE IF NOT EXISTS luthier_reputation_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT,luthier_character_id INTEGER NOT NULL,crafted_item_id INTEGER,
 event_type TEXT NOT NULL,points INTEGER NOT NULL,source_character_id INTEGER,details_json TEXT NOT NULL DEFAULT '{}',
 created_at TEXT NOT NULL DEFAULT(datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_luthier_rep_owner ON luthier_reputation_events(luthier_character_id,created_at);
CREATE TABLE IF NOT EXISTS crafted_item_notable_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT,crafted_item_id INTEGER NOT NULL,event_type TEXT NOT NULL,
 character_id INTEGER,details_json TEXT NOT NULL DEFAULT '{}',created_at TEXT NOT NULL DEFAULT(datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_luthier_notable_item ON crafted_item_notable_history(crafted_item_id,created_at);
CREATE UNIQUE INDEX IF NOT EXISTS ux_luthier_notable_event ON crafted_item_notable_history(crafted_item_id,event_type,details_json);
CREATE UNIQUE INDEX IF NOT EXISTS ux_luthier_famous_owner ON crafted_item_notable_history(crafted_item_id,character_id) WHERE event_type='famous_owner';
CREATE TABLE IF NOT EXISTS luthier_achievements (
 id INTEGER PRIMARY KEY AUTOINCREMENT,character_id INTEGER NOT NULL,achievement_key TEXT NOT NULL,
 crafted_item_id INTEGER,details_json TEXT NOT NULL DEFAULT '{}',unlocked_at TEXT NOT NULL DEFAULT(datetime('now')),
 UNIQUE(character_id,achievement_key)
);
CREATE TABLE IF NOT EXISTS luthiery_admin_audit (
 id INTEGER PRIMARY KEY AUTOINCREMENT,admin_user_id INTEGER NOT NULL,action TEXT NOT NULL,target TEXT NOT NULL,
 before_json TEXT,after_json TEXT,created_at TEXT NOT NULL DEFAULT(datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_luthiery_admin_audit_created ON luthiery_admin_audit(created_at,id);
