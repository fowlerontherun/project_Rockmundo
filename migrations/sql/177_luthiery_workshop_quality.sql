-- Persistent per-character Luthiery workshop quality.
CREATE TABLE IF NOT EXISTS character_luthiery_workshops (
 character_id INTEGER PRIMARY KEY,
 quality_score INTEGER NOT NULL DEFAULT 50 CHECK(quality_score BETWEEN 0 AND 100),
 upgrade_level INTEGER NOT NULL DEFAULT 0 CHECK(upgrade_level BETWEEN 0 AND 5),
 updated_at TEXT NOT NULL DEFAULT(datetime('now'))
);
