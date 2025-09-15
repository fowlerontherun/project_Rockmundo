import sqlite3
import random
from datetime import datetime
from database import DB_PATH

def unlock_ai_manager(band_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Create manager if not exists
    cur.execute(""" 
        INSERT OR IGNORE INTO ai_tour_managers (band_id, unlocked, optimization_level, active_since)
        VALUES (?, 1, 1, ?)
    """, (band_id, datetime.utcnow().isoformat()))
    # If exists, ensure unlocked
    cur.execute(""" 
        UPDATE ai_tour_managers 
        SET unlocked = 1, active_since = ? 
        WHERE band_id = ?
    """, (datetime.utcnow().isoformat(), band_id))
    conn.commit()
    conn.close()
    return get_ai_manager_status(band_id)

def upgrade_ai_manager(band_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Fetch current level
    cur.execute(""" 
        SELECT optimization_level 
        FROM ai_tour_managers 
        WHERE band_id = ?
    """, (band_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"error": "AI Manager not unlocked"}
    level = row[0]
    if level >= 5:
        conn.close()
        return {"error": "Already at max level"}
    new_level = level + 1
    cur.execute(""" 
        UPDATE ai_tour_managers 
        SET optimization_level = ?
        WHERE band_id = ?
    """, (new_level, band_id))
    conn.commit()
    conn.close()
    return get_ai_manager_status(band_id)

def generate_optimized_route(band_id: int, cities: list) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(""" 
        SELECT unlocked, optimization_level 
        FROM ai_tour_managers 
        WHERE band_id = ?
    """, (band_id,))
    row = cur.fetchone()
    conn.close()
    if not row or row[0] != 1:
        return {"error": "AI Manager not unlocked"}
    level = row[1]
    # Simple optimization: shuffle based on level
    weighted = [(city, random.random() * (6 - level)) for city in cities]
    ordered = [city for city, _ in sorted(weighted, key=lambda x: x[1])]
    return {"ordered_cities": ordered}

def get_ai_manager_status(band_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(""" 
        SELECT unlocked, optimization_level, active_since 
        FROM ai_tour_managers 
        WHERE band_id = ?
    """, (band_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"band_id": band_id, "unlocked": False}
    return {
        "band_id": band_id,
        "unlocked": bool(row[0]),
        "optimization_level": row[1],
        "active_since": row[2]
    }