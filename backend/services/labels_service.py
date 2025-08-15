import sqlite3
from datetime import datetime
from backend.database import DB_PATH

def create_label(name: str, founder_user_id: int, sign_up_fee: int = 0) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO labels (name, founder_user_id, sign_up_fee, created_at)
        VALUES (?, ?, ?, ?)
    """, (name, founder_user_id, sign_up_fee, datetime.utcnow().isoformat()))
    label_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"status": "ok", "label_id": label_id}

def sign_band(label_id: int, band_id: int, contract_terms: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Ensure label exists
    cur.execute("SELECT id FROM labels WHERE id = ?", (label_id,))
    if not cur.fetchone():
        conn.close()
        return {"error": "Label not found"}
    # Ensure band exists
    cur.execute("SELECT id FROM bands WHERE id = ?", (band_id,))
    if not cur.fetchone():
        conn.close()
        return {"error": "Band not found"}
    # Sign band
    cur.execute("""
        INSERT OR IGNORE INTO label_bands (label_id, band_id, contract_terms, signed_at)
        VALUES (?, ?, ?, ?)
    """, (label_id, band_id, contract_terms, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return {"status": "ok", "label_id": label_id, "band_id": band_id}

def list_labels() -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, founder_user_id, sign_up_fee, created_at
        FROM labels
        ORDER BY created_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(["label_id", "name", "founder_user_id", "sign_up_fee", "created_at"], row)) for row in rows]

def list_label_bands(label_id: int) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT lb.band_id, b.name, lb.contract_terms, lb.signed_at
        FROM label_bands lb
        JOIN bands b ON lb.band_id = b.id
        WHERE lb.label_id = ?
    """, (label_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(["band_id", "band_name", "contract_terms", "signed_at"], row)) for row in rows]

def dissolve_label(label_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Remove signings
    cur.execute("DELETE FROM label_bands WHERE label_id = ?", (label_id,))
    # Remove label
    cur.execute("DELETE FROM labels WHERE id = ?", (label_id,))
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Label dissolved"}