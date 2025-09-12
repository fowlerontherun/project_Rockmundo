from __future__ import annotations
import os
import re
import sqlite3
from urllib.parse import urlparse

DB_PATH = os.getenv("DB_PATH", "devmind_schema.db")

def infer_key_from_url(url: str) -> str | None:
    if not url:
        return None
    # Try S3-style: https://bucket.s3.region.amazonaws.com/key...
    # or custom endpoint: https://endpoint/bucket/key...
    try:
        u = urlparse(url)
    except Exception:
        return None
    if u.scheme in ("http","https"):
        # Split path and drop leading slash
        path = u.path.lstrip("/")
        # If path contains "bucket/key" and netloc is custom endpoint, try to detect common patterns
        # Heuristic 1: if netloc looks like "*.amazonaws.com", assume path is "<key>"
        if "amazonaws.com" in u.netloc:
            return path
        # Heuristic 2: if path appears like "<bucket>/<key>", return everything after first segment
        parts = path.split("/", 1)
        if len(parts) == 2:
            return parts[1]
        return path or None
    if u.scheme == "file":
        # file:///abs/path/var/storage/<key> or similar; we can't reliably strip root here
        # Best effort: return tail after "/mail/attachments/..."
        m = re.search(r"(mail/attachments/.*)$", u.path)
        if m:
            return m.group(1)
        return None
    return None

def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    # Ensure column exists (in case user runs backfill before migration by accident)
    cur.execute("PRAGMA table_info(mail_attachments)")
    cols = {row[1] for row in cur.fetchall()}
    if "storage_key" not in cols:
        print("storage_key column not found; run migration 046 first.")
        return

    cur.execute("SELECT id, storage_url FROM mail_attachments WHERE storage_key IS NULL OR storage_key=''")
    rows = cur.fetchall()
    updated = 0
    for aid, url in rows:
        key = infer_key_from_url(url or "")
        if key:
            cur.execute("UPDATE mail_attachments SET storage_key=? WHERE id=?", (key, aid))
            updated += 1
    con.commit()
    print(f"Backfilled storage_key for {updated} attachment(s).")

if __name__ == '__main__':
    main()
