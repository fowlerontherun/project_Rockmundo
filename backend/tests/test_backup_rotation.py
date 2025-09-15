# test_backup_rotation.py
import os
import sqlite3
import time

from jobs import backup_db


def test_backup_rotation(tmp_path):
    db = tmp_path / "app.db"
    backups = tmp_path / "backups"
    backups.mkdir(parents=True, exist_ok=True)

    # Create DB and a table so copy isn't empty
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE t(x INTEGER);")
    conn.commit()
    conn.close()

    os.environ["DB_PATH"] = str(db)
    os.environ["BACKUP_DIR"] = str(backups)
    os.environ["BACKUP_RETENTION"] = "3"
    os.environ["BACKUP_PREFIX"] = "snap_"

    # Create 5 snapshots; retention=3 -> only last 3 kept
    for _ in range(5):
        created, detail = backup_db.run()
        assert created == 1
        time.sleep(1)  # ensure distinct timestamps for file ordering

    files = sorted([p.name for p in backups.iterdir() if p.is_file()])
    assert len(files) == 3
    assert all(name.startswith("snap_") and name.endswith(".sqlite") for name in files)
