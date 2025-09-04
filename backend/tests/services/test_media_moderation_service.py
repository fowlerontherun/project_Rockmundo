import tempfile

import pytest

from services.economy_service import EconomyService
from services.media_moderation_service import media_moderation_service
from services.video_service import VideoService


def _setup_video_service():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    economy = EconomyService(db_path=tmp.name)
    economy.ensure_schema()
    return VideoService(economy)


def test_scan_bytes_detects_banned_word():
    res = media_moderation_service.scan_bytes(b"scene of murder")
    assert not res.allowed
    assert "murder" in res.reasons


def test_upload_video_rejects_inappropriate_title():
    svc = _setup_video_service()
    with pytest.raises(ValueError):
        svc.upload_video(owner_id=1, title="Murder Scene", filename="clip.mp4")

