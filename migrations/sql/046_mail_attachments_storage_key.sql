ALTER TABLE mail_attachments ADD COLUMN storage_key TEXT;
-- SPLIT --
CREATE INDEX IF NOT EXISTS idx_mail_attachments_storage_key ON mail_attachments(storage_key);
