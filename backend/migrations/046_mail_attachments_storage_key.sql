-- 046_mail_attachments_storage_key.sql
-- Adds a durable storage_key to mail_attachments for provider-agnostic access.
-- Safe for SQLite.
BEGIN TRANSACTION;

ALTER TABLE mail_attachments ADD COLUMN storage_key TEXT;

-- Optional index for faster lookups/deletes by key
CREATE INDEX IF NOT EXISTS idx_mail_attachments_storage_key ON mail_attachments(storage_key);

COMMIT;
