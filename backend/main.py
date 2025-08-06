from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.character import router as character_router
from routes.avatar import router as avatar_router
from routes.skin import router as skin_router
from routes.band import router as band_router
from routes.music import router as music_router
from routes.distribution import router as distribution_router

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(character_router)
app.include_router(avatar_router)
app.include_router(skin_router)
app.include_router(band_router)
app.include_router(music_router)
app.include_router(distribution_router)

@app.get("/")
def root():
    return {"message": "RockMundo API is live!"}
