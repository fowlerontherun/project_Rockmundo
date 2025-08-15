import sqlite3
from backend.database import DB_PATH


def create_venue(name: str, city: str, country: str, capacity: int, rental_cost: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO venues (name, city, country, capacity, rental_cost)
        VALUES (?, ?, ?, ?, ?)
    """, (name, city, country, capacity, rental_cost))

    venue_id = cur.lastrowid
    conn.commit()
    conn.close()

    return {"status": "ok", "venue_id": venue_id}


def list_venues_by_city(city: str) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, capacity, rental_cost
        FROM venues
        WHERE city = ?
    """, (city,))
    venues = cur.fetchall()
    conn.close()

    return [dict(zip(["venue_id", "name", "capacity", "rental_cost"], row)) for row in venues]


def get_venue_details(venue_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT name, city, country, capacity, rental_cost
        FROM venues
        WHERE id = ?
    """, (venue_id,))
    venue = cur.fetchone()

    cur.execute("""
        SELECT id, band_id, date, ticket_price
        FROM shows
        WHERE venue_id = ? AND date >= date('now')
        ORDER BY date ASC
    """, (venue_id,))
    upcoming_shows = cur.fetchall()
    conn.close()

    return {
        "name": venue[0],
        "city": venue[1],
        "country": venue[2],
        "capacity": venue[3],
        "rental_cost": venue[4],
        "upcoming_shows": [dict(zip(["show_id", "band_id", "date", "ticket_price"], show)) for show in upcoming_shows]
    }


def update_venue(venue_id: int, updates: dict) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for field, value in updates.items():
        cur.execute(f"UPDATE venues SET {field} = ? WHERE id = ?", (value, venue_id))

    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Venue updated"}


def delete_venue(venue_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DELETE FROM shows WHERE venue_id = ?", (venue_id,))
    cur.execute("DELETE FROM venues WHERE id = ?", (venue_id,))

    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Venue deleted"}