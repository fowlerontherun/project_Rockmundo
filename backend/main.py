# backend/main.py

from database import init_db
from fastapi import FastAPI, Response
from routes import (  # ← added social_routes import
    event_routes,
    lifestyle_routes,
    social_routes,
    sponsorship,
)

from backend.utils.logging import setup_logging
from backend.utils.metrics import CONTENT_TYPE_LATEST, generate_latest
from backend.utils.tracing import setup_tracing

app = FastAPI(title="RockMundo API with Events, Lifestyle, and Sponsorships")

@app.on_event("startup")
def startup():
    setup_logging()
    setup_tracing()
    init_db()

# Existing routers
app.include_router(event_routes.router, prefix="/api/events", tags=["Events"])
app.include_router(lifestyle_routes.router, prefix="/api", tags=["Lifestyle"])

# New sponsorship router
app.include_router(sponsorship.router, prefix="/api/sponsorships", tags=["Sponsorships"])
app.include_router(social_routes.router, prefix="/api/social", tags=["Social"])


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
def root():
    return {"message": "Welcome to RockMundo API"}
