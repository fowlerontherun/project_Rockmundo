# backend/main.py

from fastapi import FastAPI
from routes import event_routes, lifestyle_routes
from database import init_db

app = FastAPI(title="RockMundo API with Events and Lifestyle")

@app.on_event("startup")
def startup():
    init_db()

app.include_router(event_routes.router, prefix="/api/events", tags=["Events"])
app.include_router(lifestyle_routes.router, prefix="/api", tags=["Lifestyle"])

@app.get("/")
def root():
    return {"message": "Welcome to RockMundo API"}
