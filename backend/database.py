import sqlite3

def initialize_database():
    conn = sqlite3.connect("rockmundo.db")
    cursor = conn.cursor()

    # Vehicle types
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicle_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        description TEXT,
        speed INTEGER,
        capacity INTEGER,
        maintenance_cost INTEGER,
        base_cost INTEGER
    )
    """)

    # User-owned vehicles
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        vehicle_type_id INTEGER,
        nickname TEXT,
        upgrades TEXT,
        condition INTEGER DEFAULT 100,
        FOREIGN KEY(vehicle_type_id) REFERENCES vehicle_types(id)
    )
    """)

    # Vehicle upgrades
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicle_upgrades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        effect TEXT,
        cost INTEGER
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()
    print("Database initialized.")