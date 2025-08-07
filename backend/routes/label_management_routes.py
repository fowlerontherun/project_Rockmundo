from fastapi import APIRouter

router = APIRouter()

@router.get("/labels/status")
async def check_label_status():
    return {"status": "Label & Management system operational."}
