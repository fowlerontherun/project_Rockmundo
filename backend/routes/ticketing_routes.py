from fastapi import APIRouter

router = APIRouter()

@router.get("/tickets/status")
async def check_ticketing_status():
    return {"status": "Ticketing system operational."}
