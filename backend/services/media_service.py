import sqlite3
import json
from datetime import datetime
from backend.database import DB_PATH

def upload_media(band_id: int, media_type: str, file_path: str, metadata: dict = None) -> dict:
    """
    Store a media asset (e.g., cover art, audio file, video).
    media_type: 'cover_art', 'audio', 'video'
    metadata: optional dictionary for additional info
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    metadata_json = json.dumps(metadata or {})
    cur.execute(""" 
        INSERT INTO media_assets (band_id, media_type, file_path, metadata, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (band_id, media_type, file_path, metadata_json, datetime.utcnow().isoformat()))
    media_id = cur.lastrowid

    conn.commit()
    conn.close()
    return {"status": "ok", "media_id": media_id}


def get_media(media_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(""" 
        SELECT id, band_id, media_type, file_path, metadata, created_at
        FROM media_assets
        WHERE id = ?
    """, (media_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return {"error": "Media not found"}

    id, band_id, media_type, file_path, metadata_json, created_at = row
    metadata = json.loads(metadata_json)
    return {
        "id": id,
        "band_id": band_id,
        "media_type": media_type,
        "file_path": file_path,
        "metadata": metadata,
        "created_at": created_at
    }


def list_media_by_band(band_id: int) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(""" 
        SELECT id, media_type, file_path, metadata, created_at
        FROM media_assets
        WHERE band_id = ?
        ORDER BY created_at DESC
    """, (band_id,))
    rows = cur.fetchall()
    conn.close()

    assets = []
    for id, media_type, file_path, metadata_json, created_at in rows:
        assets.append({
            "id": id,
            "media_type": media_type,
            "file_path": file_path,
            "metadata": json.loads(metadata_json),
            "created_at": created_at
        })
    return assets


def update_media_metadata(media_id: int, metadata: dict) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    metadata_json = json.dumps(metadata)
    cur.execute(""" 
        UPDATE media_assets 
        SET metadata = ?, created_at = ?
        WHERE id = ?
    """, (metadata_json, datetime.utcnow().isoformat(), media_id))
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Metadata updated"}


def delete_media(media_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM media_assets WHERE id = ?", (media_id,))
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Media deleted"}