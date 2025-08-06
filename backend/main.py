from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.character import router as character_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(character_router)

@app.get("/")
def root():
    return {"message": "RockMundo API is live!"}
