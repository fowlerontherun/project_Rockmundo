CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_target TEXT NOT NULL,
    duration INTEGER NOT NULL,
    prerequisites TEXT,
    prestige INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    completed INTEGER NOT NULL DEFAULT 0,
    enrolled_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(course_id) REFERENCES courses(id)
);
