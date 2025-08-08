from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import importlib
import sqlite3
from database import initialize_database

app = FastAPI()
DB_PATH = "rockmundo.db"

# Enable CORS (adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Initialize Database on Startup ===
@app.on_event("startup")
def startup_event():
    if not os.path.exists(DB_PATH):
        print("Initializing database...")
        initialize_database()

# === Dynamically Load and Include All Routes ===
def load_routes():
    import os
    import glob
    route_files = glob.glob("backend/routes/*.py")
    for file in route_files:
        if "__init__" in file:
            continue
        module_name = file.replace("/", ".").replace(".py", "")
        module = importlib.import_module(module_name)
        for attr in dir(module):
            obj = getattr(module, attr)
            if hasattr(obj, "router"):
                app.include_router(obj.router)
            elif hasattr(obj, "blueprint") or hasattr(obj, "routes"):
                try:
                    app.include_router(obj)
                except Exception:
                    pass

load_routes()