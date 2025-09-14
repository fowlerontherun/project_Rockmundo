# backend/jobs/data_hygiene_jobs.py
# Data hygiene & backup jobs for SQLite
# - Cleanup: purge expired idempotency + rate-limit rows
# - Backup: safe .db snapshots with rotation
# This module is designed to be imported by your job runner or invoked directly.
from __future__ import annotations

import os
import re
import sqlite3
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Tuple, List


# --- Config helpers ---------------------------------------------------------

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "y", "on")


def _detect_db_path() -> str:
    """
    Try to resolve DB path from project settings, with safe fallbacks.
    """
    # Preferred: dedicated settings
    for mod_name, attr in (
        ("backend.core.settings", "DB_PATH"),
        ("backend.settings", "DB_PATH"),
        ("settings", "DB_PATH"),
    ):
        try:
            mod = __import__(mod_name, fromlist=[attr])
            dbp = getattr(mod, attr, None)
            if isinstance(dbp, str) and dbp:
                return dbp
        except Exception:
            pass

    # Next: try to import a get_conn that knows the path
    try:
        from backend.core.database import DB_PATH as CORE_DB_PATH  # type: ignore
        if CORE_DB_PATH:
            return CORE_DB_PATH
    except Exception:
        pass

    # Env fallbacks
    dbp = os.getenv("DB_PATH")
    if dbp:
        return dbp

    # Last resort
    return "devmind_schema.db"


DB_PATH = _detect_db_path()
DEFAULT_BACKUP_DIR = os.getenv("DB_BACKUP_DIR", "backups/db")
DEFAULT_BACKUP_PREFIX = os.getenv("DB_BACKUP_PREFIX", "snapshot")
DEFAULT_BACKUP_COPIES = int(os.getenv("DB_BACKUP_COPIES", "7"))


# --- DB connection helper ---------------------------------------------------

def get_conn(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Import the project's get_conn() if available; otherwise provide a safe default.
    Ensures WAL-friendly settings and reasonable timeouts.
    """
    # Try project-level helpers first
    for mod_name in (
        "backend.core.database",
        "database",
    ):
        try:
            mod = __import__(mod_name, fromlist=["get_conn"])
            return getattr(mod, "get_conn")(db_path or DB_PATH)  # type: ignore
        except Exception:
            continue

    # Fallback local connector
    path = db_path or DB_PATH
    conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES, timeout=30.0)
    conn.row_factory = sqlite3.Row
    # These pragmas are safe; they'll be ignored if unsupported
    with conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


# --- Introspection helpers --------------------------------------------------

def _table_has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table});")
    cols = [row["name"] for row in cur.fetchall()]
    return column in cols


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table,)
    )
    return cur.fetchone() is not None


# --- Cleanup job ------------------------------------------------------------

def cleanup_expired_records(
    db_path: Optional[str] = None,
    *,
    idempotency_table: str = "idempotency_records",
    rate_limit_table: str = "rate_limit_counters",
    now: Optional[datetime] = None,
    dry_run: bool = False,
) -> dict:
    """
    Purge expired rows from idempotency + rate-limit tables.

    Assumptions:
      - Tables have an `expires_at` column (TEXT ISO8601 or INTEGER epoch seconds).
      - If absent on rate_limit_table, we fallback to `window_end` or `created_at` with a heuristic (older than now).
    """
    stats = {
        "db_path": db_path or DB_PATH,
        "idempotency_deleted": 0,
        "rate_limit_deleted": 0,
        "idempotency_scanned": 0,
        "rate_limit_scanned": 0,
        "dry_run": dry_run,
    }
    reference_time = now or _utc_now()

    with get_conn(db_path) as conn:
        # IDEMPOTENCY
        if _table_exists(conn, idempotency_table):
            stats["idempotency_scanned"] = _count_rows(conn, idempotency_table)
            if _table_has_column(conn, idempotency_table, "expires_at"):
                deleted = _delete_where_expired(conn, idempotency_table, reference_time, dry_run=dry_run)
                stats["idempotency_deleted"] = deleted

        # RATE LIMIT
        if _table_exists(conn, rate_limit_table):
            stats["rate_limit_scanned"] = _count_rows(conn, rate_limit_table)
            if _table_has_column(conn, rate_limit_table, "expires_at"):
                deleted = _delete_where_expired(conn, rate_limit_table, reference_time, dry_run=dry_run)
                stats["rate_limit_deleted"] = deleted
            elif _table_has_column(conn, rate_limit_table, "window_end"):
                deleted = _delete_where_before_timestamp_column(
                    conn, rate_limit_table, "window_end", reference_time, dry_run=dry_run
                )
                stats["rate_limit_deleted"] = deleted
            elif _table_has_column(conn, rate_limit_table, "created_at"):
                # Heuristic: created_at < now minus 2 days is considered stale
                deleted = _delete_where_before_timestamp_column(
                    conn,
                    rate_limit_table,
                    "created_at",
                    reference_time - timedelta(days=2),
                    dry_run=dry_run,
                )
                stats["rate_limit_deleted"] = deleted

    return stats


def _parse_time_value(val) -> Optional[datetime]:
    """
    Accepts INTEGER epoch seconds, or TEXT ISO8601 (with/without 'Z').
    Returns aware datetime in UTC, or None if unparseable.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        try:
            return datetime.fromtimestamp(float(val), tz=timezone.utc)
        except Exception:
            return None
    if isinstance(val, (bytes, bytearray)):
        try:
            val = val.decode("utf-8")
        except Exception:
            return None
    if isinstance(val, str):
        s = val.strip()
        if s.isdigit():
            try:
                return datetime.fromtimestamp(float(s), tz=timezone.utc)
            except Exception:
                return None
        # Normalize trailing Z
        s = re.sub(r"Z$", "+00:00", s)
        try:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                # Assume UTC if naive
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except Exception:
            return None
    return None


def _count_rows(conn: sqlite3.Connection, table: str) -> int:
    cur = conn.execute(f"SELECT COUNT(*) AS c FROM {table};")
    row = cur.fetchone()
    return int(row["c"] if row and "c" in row.keys() else 0)


def _delete_where_expired(
    conn: sqlite3.Connection, table: str, reference_time: datetime, *, dry_run: bool
) -> int:
    """
    Delete rows where expires_at < reference_time.
    Supports INTEGER epoch or TEXT datetime values.
    """
    # fetch ids first to be safe with parsing
    cur = conn.execute(f"SELECT rowid, expires_at FROM {table};")
    stale_ids: List[int] = []
    for r in cur.fetchall():
        exp = _parse_time_value(r["expires_at"])
        if exp is not None and exp < reference_time:
            stale_ids.append(int(r["rowid"]))

    if not stale_ids or dry_run:
        return 0 if not dry_run else len(stale_ids)

    # chunk deletes to avoid giant IN clauses
    total = 0
    with conn:
        for i in range(0, len(stale_ids), 1000):
            chunk = stale_ids[i : i + 1000]
            qmarks = ",".join("?" for _ in chunk)
            conn.execute(f"DELETE FROM {table} WHERE rowid IN ({qmarks});", chunk)
            total += len(chunk)
    return total


def _delete_where_before_timestamp_column(
    conn: sqlite3.Connection,
    table: str,
    col: str,
    before_time: datetime,
    *,
    dry_run: bool,
) -> int:
    """
    Delete rows where <col> < before_time. Column may be INTEGER epoch or TEXT ISO8601.
    """
    cur = conn.execute(f"SELECT rowid, {col} FROM {table};")
    stale_ids: List[int] = []
    for r in cur.fetchall():
        dt = _parse_time_value(r[col])
        if dt is not None and dt < before_time:
            stale_ids.append(int(r["rowid"]))

    if not stale_ids or dry_run:
        return 0 if not dry_run else len(stale_ids)

    total = 0
    with conn:
        for i in range(0, len(stale_ids), 1000):
            chunk = stale_ids[i : i + 1000]
            qmarks = ",".join("?" for _ in chunk)
            conn.execute(f"DELETE FROM {table} WHERE rowid IN ({qmarks});", chunk)
            total += len(chunk)
    return total


# --- Backup job -------------------------------------------------------------

def backup_sqlite_with_rotation(
    db_path: Optional[str] = None,
    *,
    backup_dir: Optional[str] = None,
    prefix: Optional[str] = None,
    copies: Optional[int] = None,
) -> Path:
    """
    Create a consistent snapshot of the SQLite DB using the sqlite3 backup API
    and rotate to keep only `copies` most recent backups.

    Returns the path to the created backup file.
    """
    source = Path(db_path or DB_PATH).resolve()
    if not source.exists():
        raise FileNotFoundError(f"DB not found: {source}")

    bdir = Path(backup_dir or DEFAULT_BACKUP_DIR)
    bdir.mkdir(parents=True, exist_ok=True)

    pref = prefix or DEFAULT_BACKUP_PREFIX
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dest = bdir / f"{pref}_{ts}.db"

    # Use sqlite backup API for consistency under live traffic
    _perform_sqlite_backup(str(source), str(dest))

    # Rotate
    keep = copies if copies is not None else DEFAULT_BACKUP_COPIES
    _rotate_backups(bdir, pref, keep)

    return dest


def _perform_sqlite_backup(source_path: str, dest_path: str) -> None:
    """
    Uses sqlite3 Connection.backup() for a consistent snapshot.
    """
    # Retry a few times in case of busy DB
    attempts = 0
    last_err: Optional[Exception] = None
    while attempts < 5:
        try:
            with sqlite3.connect(source_path, timeout=60.0) as src, sqlite3.connect(dest_path) as dst:
                with dst:
                    src.backup(dst)
            return
        except sqlite3.OperationalError as e:
            last_err = e
            attempts += 1
            time.sleep(0.5 * attempts)
    if last_err:
        raise last_err


def _rotate_backups(backup_dir: Path, prefix: str, keep: int) -> None:
    """
    Keep only the most recent `keep` backup files matching the prefix.
    """
    pattern = re.compile(rf"^{re.escape(prefix)}_\d{{8}}T\d{{6}}Z\.db$")
    files = [p for p in backup_dir.iterdir() if p.is_file() and pattern.match(p.name)]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[keep:]:
        try:
            old.unlink()
        except Exception:
            # Best-effort; continue
            pass


# --- CLI --------------------------------------------------------------------

def _print_stats(stats: dict) -> None:
    print(
        "[cleanup] db={db_path} idempotency: scanned={idempotency_scanned} deleted={idempotency_deleted} | "
        "rate_limits: scanned={rate_limit_scanned} deleted={rate_limit_deleted} | dry_run={dry_run}".format(**stats)
    )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="SQLite Data Hygiene & Backup Jobs")
    sub = parser.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("cleanup", help="Purge expired rows from idempotency/rate-limit tables")
    c.add_argument("--db", dest="db_path", default=None, help="Path to SQLite DB")
    c.add_argument("--dry-run", dest="dry_run", action="store_true", help="Scan only; do not delete")
    c.add_argument("--idempotency-table", default="idempotency_records")
    c.add_argument("--rate-limit-table", default="rate_limit_counters")

    b = sub.add_parser("backup", help="Create a consistent snapshot and rotate backups")
    b.add_argument("--db", dest="db_path", default=None, help="Path to SQLite DB")
    b.add_argument("--dir", dest="backup_dir", default=None, help="Directory for backups (default backups/db)")
    b.add_argument("--prefix", dest="prefix", default=None, help="Filename prefix for backups (default snapshot)")
    b.add_argument("--copies", dest="copies", type=int, default=None, help="How many backups to keep (default 7)")

    args = parser.parse_args()

    if args.cmd == "cleanup":
        stats = cleanup_expired_records(
            db_path=args.db_path,
            idempotency_table=args.idempotency_table,
            rate_limit_table=args.rate_limit_table,
            dry_run=args.dry_run,
        )
        _print_stats(stats)

    elif args.cmd == "backup":
        path = backup_sqlite_with_rotation(
            db_path=args.db_path,
            backup_dir=args.backup_dir,
            prefix=args.prefix,
            copies=args.copies,
        )
        print(f"[backup] created: {path}")

if __name__ == "__main__":
    main()
