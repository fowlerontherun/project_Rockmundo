import sqlite3
from datetime import datetime
from backend.database import DB_PATH


def create_tour(band_id: int, route: list, start_date: str, vehicle_type: str) -> dict:
    if len(route) < 2:
        return {"error": "A tour must include at least two cities."}

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO tours (band_id, start_date, vehicle_type, status)
        VALUES (?, ?, ?, 'planned')
    """, (band_id, start_date, vehicle_type))
    tour_id = cur.lastrowid

    for stop_order, city in enumerate(route):
        cur.execute("""
            INSERT INTO tour_stops (tour_id, city, stop_order)
            VALUES (?, ?, ?)
        """, (tour_id, city, stop_order))

    conn.commit()
    conn.close()
    return {"status": "ok", "tour_id": tour_id}


def list_tours_by_band(band_id: int) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, start_date, vehicle_type, status
        FROM tours
        WHERE band_id = ?
        ORDER BY start_date DESC
    """, (band_id,))
    rows = cur.fetchall()
    conn.close()

    return [dict(zip(["tour_id", "start_date", "vehicle", "status"], row)) for row in rows]


def get_tour_details(tour_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT band_id, start_date, vehicle_type, status
        FROM tours
        WHERE id = ?
    """, (tour_id,))
    tour = cur.fetchone()

    cur.execute("""
        SELECT city, stop_order
        FROM tour_stops
        WHERE tour_id = ?
        ORDER BY stop_order
    """, (tour_id,))
    stops = cur.fetchall()

    conn.close()
    return {
        "band_id": tour[0],
        "start_date": tour[1],
        "vehicle": tour[2],
        "status": tour[3],
        "route": [city for city, _ in sorted(stops, key=lambda x: x[1])]
    }


def update_tour_status(tour_id: int, status: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        UPDATE tours SET status = ?
        WHERE id = ?
    """, (status, tour_id))

    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Tour status updated"}


def cancel_tour(tour_id: int) -> dict:
    return update_tour_status(tour_id, "cancelled")