# backend/main.py

from fastapi import FastAPI
from routes import event_routes, lifestyle_routes, sponsorship, social_routes  # ← added social_routes import
from database import init_db

app = FastAPI(title="RockMundo API with Events, Lifestyle, and Sponsorships")

@app.on_event("startup")
def startup():
    init_db()

# Existing routers
app.include_router(event_routes.router, prefix="/api/events", tags=["Events"])
app.include_router(lifestyle_routes.router, prefix="/api", tags=["Lifestyle"])

# New sponsorship router
app.include_router(sponsorship.router, prefix="/api/sponsorships", tags=["Sponsorships"])
app.include_router(social_routes.router, prefix="/api/social", tags=["Social"])

@app.get("/")
def root():
    return {"message": "Welcome to RockMundo API"}
