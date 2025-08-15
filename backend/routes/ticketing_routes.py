from fastapi import APIRouter

router = APIRouter()

@router.get("/tickets/status", dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))])
async def check_ticketing_status():
    return {"status": "Ticketing system operational."}
