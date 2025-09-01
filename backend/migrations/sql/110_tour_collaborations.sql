CREATE TABLE IF NOT EXISTS tour_collaborations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    band_ids TEXT NOT NULL,
    setlist TEXT NOT NULL,
    revenue_split TEXT NOT NULL,
    schedule TEXT,
    expenses TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
