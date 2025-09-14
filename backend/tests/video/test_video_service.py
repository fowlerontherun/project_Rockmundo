import tempfile

from services.economy_service import EconomyService
from services.skill_service import SkillService
from services.video_service import SERVICE_LATENCY_MS, VideoService, XP_PER_VIEW
from seeds.skill_seed import SEED_SKILLS
CONTENT_CREATION_SKILL = next(s for s in SEED_SKILLS if s.name == "content_creation")

from backend.utils.metrics import generate_latest


def setup_service(ad_rate_cents: int = 1):
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    economy = EconomyService(db_path=tmp.name)
    economy.ensure_schema()
    skills = SkillService()
    service = VideoService(economy, skills, ad_rate_cents=ad_rate_cents)
    return service, economy, skills


def test_upload_and_transcode():
    svc, _, _ = setup_service()
    video = svc.upload_video(owner_id=1, title="Intro", filename="intro.mp4")
    assert video.status == "processing"
    svc.mark_transcoded(video.id)
    assert svc.get_video(video.id).status == "ready"


def test_view_tracking_and_revenue_distribution():
    svc, economy, skills = setup_service()
    video = svc.upload_video(owner_id=1, title="Demo", filename="demo.mp4")
    svc.mark_transcoded(video.id)
    for _ in range(3):
        svc.record_view(video.id)
    assert svc.get_video(video.id).view_count == 3
    assert economy.get_balance(1) == 3
    skill = skills.train(1, CONTENT_CREATION_SKILL, 0)
    assert skill.xp == XP_PER_VIEW * 3


def test_record_view_latency_metric():
    svc, _, _ = setup_service()
    video = svc.upload_video(owner_id=1, title="Demo", filename="demo.mp4")
    svc.mark_transcoded(video.id)
    before = SERVICE_LATENCY_MS._values.get(("video_service", "record_view"), {"count": 0})["count"]
    svc.record_view(video.id)
    after = SERVICE_LATENCY_MS._values[("video_service", "record_view")]["count"]
    assert after == before + 1
    output = generate_latest().decode()
    assert 'service_latency_ms_count{service="video_service",operation="record_view"}' in output


def test_high_skill_increases_revenue():
    svc, economy, skills = setup_service(ad_rate_cents=100)
    video = svc.upload_video(owner_id=1, title="Demo", filename="demo.mp4")
    svc.mark_transcoded(video.id)
    svc.record_view(video.id)  # baseline view at level 1
    base = economy.get_balance(1)
    skills.train(1, CONTENT_CREATION_SKILL, 500)
    svc.record_view(video.id)
    after = economy.get_balance(1)
    assert after - base == 106
