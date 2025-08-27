import tempfile

from services.video_service import VideoService
from services.economy_service import EconomyService


def setup_service():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    economy = EconomyService(db_path=tmp.name)
    economy.ensure_schema()
    service = VideoService(economy)
    return service, economy


def test_upload_and_transcode():
    svc, _ = setup_service()
    video = svc.upload_video(owner_id=1, title="Intro", filename="intro.mp4")
    assert video.status == "processing"
    svc.mark_transcoded(video.id)
    assert svc.get_video(video.id).status == "ready"


def test_view_tracking_and_revenue_distribution():
    svc, economy = setup_service()
    video = svc.upload_video(owner_id=1, title="Demo", filename="demo.mp4")
    svc.mark_transcoded(video.id)
    for _ in range(3):
        svc.record_view(video.id)
    assert svc.get_video(video.id).view_count == 3
    assert economy.get_balance(1) == 3
