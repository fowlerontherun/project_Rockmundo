-- File: backend/migrations/085_access_tokens.sql
-- Adds a table for tracking issued access JWTs so they can be revoked

CREATE TABLE IF NOT EXISTS access_tokens (
    jti TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT
);
