from fastapi import APIRouter, Depends, HTTPException
from backend.auth.dependencies import get_current_user_id, require_permission
from backend.services.economy_service import EconomyService
from backend.services.video_service import VideoService
from backend.services.skill_service import SkillService


router = APIRouter(prefix="/videos")

# Create service instances for the simple demo implementation
_economy = EconomyService()
_economy.ensure_schema()
_video_service = VideoService(_economy, SkillService())


async def _current_user(user_id: int = Depends(get_current_user_id)) -> int:
    await require_permission(["user", "band_member", "moderator", "admin"], user_id)
    return user_id


@router.post("/")
def upload_video(title: str, filename: str, user_id: int = Depends(_current_user)):
    video = _video_service.upload_video(user_id, title, filename)
    return video.to_dict()


@router.post("/{video_id}/transcode")
def mark_transcoded(video_id: int):
    if not _video_service.get_video(video_id):
        raise HTTPException(status_code=404, detail="Video not found")
    _video_service.mark_transcoded(video_id)
    return {"status": "ok"}


@router.post("/{video_id}/view")
def record_view(video_id: int):
    try:
        count = _video_service.record_view(video_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"views": count}


@router.get("/{video_id}")
def get_video(video_id: int):
    video = _video_service.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video.to_dict()


@router.get("/")
def list_videos():
    return [v.to_dict() for v in _video_service.list_videos()]


@router.delete("/{video_id}")
def delete_video(video_id: int, user_id: int = Depends(_current_user)):
    video = _video_service.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this video")
    _video_service.delete_video(video_id)
    return {"status": "deleted"}

