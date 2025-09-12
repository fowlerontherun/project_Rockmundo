-- File: backend/migrations/sql/150_permissions.sql

CREATE TABLE IF NOT EXISTS permissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  description TEXT
);

-- SPLIT --

CREATE TABLE IF NOT EXISTS role_permissions (
  role_id INTEGER NOT NULL,
  permission_id INTEGER NOT NULL,
  PRIMARY KEY (role_id, permission_id),
  FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
  FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

-- SPLIT --

-- Seed default permissions mirroring roles
INSERT OR IGNORE INTO permissions (id, name, description) VALUES
  (1, 'admin', 'Administrator'),
  (2, 'moderator', 'Moderator'),
  (3, 'band_member', 'Band member'),
  (4, 'user', 'Regular user');

-- SPLIT --

INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES
  (1, 1),
  (2, 2),
  (3, 3),
  (4, 4);
