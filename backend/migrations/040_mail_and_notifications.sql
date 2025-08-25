-- File: backend/migrations/040_mail_and_notifications.sql
-- Idempotent schema for mail + notifications

BEGIN;

CREATE TABLE IF NOT EXISTS mail_threads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subject TEXT NOT NULL,
  created_by INTEGER NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS mail_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id INTEGER NOT NULL,
  sender_id INTEGER NOT NULL,
  body TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (thread_id) REFERENCES mail_threads(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS mail_participants (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  last_read_message_id INTEGER DEFAULT 0,
  UNIQUE (thread_id, user_id),
  FOREIGN KEY (thread_id) REFERENCES mail_threads(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_mail_messages_thread ON mail_messages(thread_id, created_at);
CREATE INDEX IF NOT EXISTS ix_mail_messages_thread_id ON mail_messages(thread_id, id);
CREATE INDEX IF NOT EXISTS ix_mail_participants_user ON mail_participants(user_id, thread_id);

CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  type TEXT NOT NULL,         -- 'mail' | 'system' | 'order' | ...
  title TEXT NOT NULL,
  body TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  read_at TEXT
);

CREATE INDEX IF NOT EXISTS ix_notifications_user ON notifications(user_id, created_at);
CREATE INDEX IF NOT EXISTS ix_notifications_unread ON notifications(user_id, read_at);

COMMIT;
