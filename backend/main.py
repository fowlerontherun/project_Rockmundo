from fastapi import FastAPI, HTTPException
import sqlite3

app = FastAPI()

DB_PATH = "rockmundo.db"

@app.get("/vehicles/list")
def list_vehicle_types():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicle_types")
    vehicles = cursor.fetchall()
    conn.close()
    return {"vehicles": vehicles}

@app.post("/vehicles/purchase")
def purchase_vehicle(user_id: int, vehicle_type_id: int, nickname: str = ""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_vehicles (user_id, vehicle_type_id, nickname) VALUES (?, ?, ?)",
                   (user_id, vehicle_type_id, nickname))
    conn.commit()
    conn.close()
    return {"message": "Vehicle purchased successfully."}

@app.get("/vehicles/user")
def get_user_vehicles(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_vehicles WHERE user_id = ?", (user_id,))
    result = cursor.fetchall()
    conn.close()
    return {"vehicles": result}