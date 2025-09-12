CREATE TABLE releases (
    id INTEGER PRIMARY KEY,
    band_id INTEGER,
    title TEXT NOT NULL,
    format TEXT CHECK(format IN ('single','ep','lp')) NOT NULL,
    release_date DATE,
    total_runtime INTEGER DEFAULT 0,
    collaboration_id INTEGER,
    distribution_channels TEXT
);

-- SPLIT --

CREATE TABLE tracks (
    id INTEGER PRIMARY KEY,
    release_id INTEGER NOT NULL REFERENCES releases(id),
    title TEXT NOT NULL,
    duration INTEGER NOT NULL,
    track_number INTEGER NOT NULL
);
