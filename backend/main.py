# backend/main.py

from fastapi import FastAPI
from routes import event_routes, lifestyle_routes, sponsorship, social_routes, admin_routes
from database import init_db
from middleware.locale import LocaleMiddleware
from utils.i18n import _

app = FastAPI(title="RockMundo API with Events, Lifestyle, and Sponsorships")
app.add_middleware(LocaleMiddleware)

@app.on_event("startup")
def startup():
    init_db()

# Existing routers
app.include_router(event_routes.router, prefix="/api/events", tags=["Events"])
app.include_router(lifestyle_routes.router, prefix="/api", tags=["Lifestyle"])
app.include_router(admin_routes.router, prefix="/admin", tags=["Admin"])

# New sponsorship router
app.include_router(sponsorship.router, prefix="/api/sponsorships", tags=["Sponsorships"])
app.include_router(social_routes.router, prefix="/api/social", tags=["Social"])

@app.get("/")
def root():
    return {"message": _("Welcome to RockMundo API")}
