CREATE TABLE IF NOT EXISTS mail_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    FOREIGN KEY (message_id) REFERENCES mail_messages(id) ON DELETE CASCADE
);
-- SPLIT --
CREATE VIRTUAL TABLE IF NOT EXISTS mail_fts USING fts5(
    subject, 
    body,
    content=mail_messages, 
    content_rowid=id
);
-- SPLIT --
CREATE TRIGGER IF NOT EXISTS mail_messages_ai AFTER INSERT ON mail_messages BEGIN
  INSERT INTO mail_fts(rowid, subject, body) VALUES (new.id, new.subject, new.body);
END;
-- SPLIT --
CREATE TRIGGER IF NOT EXISTS mail_messages_ad AFTER DELETE ON mail_messages BEGIN
  DELETE FROM mail_fts WHERE rowid=old.id;
END;
