import tempfile
import tempfile

from fastapi import HTTPException
import tempfile
from routes import video_routes
from backend.services.economy_service import EconomyService
from backend.services.skill_service import SkillService
from backend.services.video_service import VideoService


async def _require_permission_stub(roles, user_id):
    return True


def setup_services():
    video_routes.require_permission = _require_permission_stub

    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    economy = EconomyService(tmp.name)
    economy.ensure_schema()
    video_routes._economy = economy
    video_routes._video_service = VideoService(economy, SkillService())
    return economy


def test_upload_view_delete_authorization():
    economy = setup_services()

    vid = video_routes.upload_video(title="Demo", filename="demo.mp4", user_id=1)
    video_id = vid["id"]

    res = video_routes.record_view(video_id)
    assert res["views"] == 1
    assert economy.get_balance(1) == 1

    try:
        video_routes.delete_video(video_id, user_id=2)
    except HTTPException as e:
        assert e.status_code == 403
    else:
        assert False, "Expected HTTPException for unauthorized delete"

    res = video_routes.delete_video(video_id, user_id=1)
    assert res["status"] == "deleted"

