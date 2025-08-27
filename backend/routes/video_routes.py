from backend.auth.dependencies import get_current_user_id, require_role  # noqa: F401
from backend.services.economy_service import EconomyService
from backend.services.video_service import VideoService
from fastapi import APIRouter, Depends, HTTPException, Request  # noqa: F401

router = APIRouter()

# Create service instances for the simple demo implementation
_economy = EconomyService()
_economy.ensure_schema()
_video_service = VideoService(_economy)


@router.post("/videos")
def upload_video(owner_id: int, title: str, filename: str):
    video = _video_service.upload_video(owner_id, title, filename)
    return video.to_dict()


@router.post("/videos/{video_id}/transcode")
def mark_transcoded(video_id: int):
    if not _video_service.get_video(video_id):
        raise HTTPException(status_code=404, detail="Video not found")
    _video_service.mark_transcoded(video_id)
    return {"status": "ok"}


@router.post("/videos/{video_id}/view")
def record_view(video_id: int):
    try:
        count = _video_service.record_view(video_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"views": count}


@router.get("/videos/{video_id}")
def get_video(video_id: int):
    video = _video_service.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video.to_dict()


@router.get("/videos")
def list_videos():
    return [v.to_dict() for v in _video_service.list_videos()]


@router.delete("/videos/{video_id}")
def delete_video(video_id: int):
    if not _video_service.get_video(video_id):
        raise HTTPException(status_code=404, detail="Video not found")
    _video_service.delete_video(video_id)
    return {"status": "deleted"}
