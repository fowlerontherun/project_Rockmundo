from auth.dependencies import get_current_user_id, require_role
from fastapi import APIRouter

router = APIRouter()

@router.get("/labels/status", dependencies=[Depends(require_role(["admin"]))])
async def check_label_status():
    return {"status": "Label & Management system operational."}
