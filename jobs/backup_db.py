# backup_db.py
"""
SQLite snapshot rotation.

Creates timestamped copies of the DB file into BACKUP_DIR (default ./backups).
Keeps up to BACKUP_RETENTION (default 7) most recent snapshots, deleting older ones.

Environment/config:
- DB_PATH (str)               - path to main SQLite DB (default: app.db)
- BACKUP_DIR (str)            - default: ./backups
- BACKUP_RETENTION (int)      - default: 7
- BACKUP_PREFIX (str)         - default: db_snapshot_
"""

from __future__ import annotations
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple


def run() -> Tuple[int, str]:
    db_path = Path(os.getenv("DB_PATH", "app.db"))
    backup_dir = Path(os.getenv("BACKUP_DIR", "backups"))
    retention = int(os.getenv("BACKUP_RETENTION", "7"))
    prefix = os.getenv("BACKUP_PREFIX", "db_snapshot_")

    backup_dir.mkdir(parents=True, exist_ok=True)
    if not db_path.exists():
        # Nothing to back up but not an error; return 0 created
        return 0, f"db_missing:{db_path}"

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = backup_dir / f"{prefix}{timestamp}.sqlite"

    # Use SQLite safe copy (file-level) — for WAL safety, you can also
    # run 'VACUUM INTO' if using sqlite3 CLI; here we do a filesystem copy.
    shutil.copy2(db_path, dest)

    # Rotate: keep newest 'retention' matching prefix pattern
    created = 1
    deleted = 0
    pattern = re.compile(rf"^{re.escape(prefix)}\d{{8}}T\d{{6}}Z\.sqlite$")
    snapshots: List[Path] = sorted(
        [p for p in backup_dir.iterdir() if p.is_file() and pattern.match(p.name)],
        key=lambda p: p.name,
        reverse=True,
    )

    if len(snapshots) > retention:
        for old in snapshots[retention:]:
            try:
                old.unlink()
                deleted += 1
            except Exception:
                # best-effort; continue
                pass

    detail = f"created={created}, rotated_out={deleted}, kept={min(len(snapshots), retention)}"
    return created, detail
