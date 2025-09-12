import sqlite3
from pathlib import Path

from passlib.hash import bcrypt

# Use the shared application database so auth data stays consistent with
# other services.  The previous path pointed to ``database.db`` which is not
# used anywhere else in the project and would create a separate, empty
# database file.  This caused newly created users to be invisible to
# components that relied on the main ``rockmundo.db`` file.
DB_PATH = Path(__file__).resolve().parent.parent / "rockmundo.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_user(username: str, password: str, role: str = "user"):
    conn = get_db_connection()
    cur = conn.cursor()
    password_hash = bcrypt.hash(password)
    cur.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        (username, password_hash, role)
    )
    conn.commit()
    conn.close()

def get_user_by_username(username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()
    return user

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.verify(password, hashed)