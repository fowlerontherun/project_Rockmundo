import asyncio
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.avatar import Base as AvatarBase
from models.character import Base as CharacterBase, Character
from schemas.avatar import AvatarCreate
from backend.services.avatar_service import AvatarService

Path(__file__).resolve().parents[2].joinpath("database").mkdir(exist_ok=True)

from backend.services.band_service import BandService, Base  # noqa: E402
from backend.services.originality_service import OriginalityService  # noqa: E402
from backend.services.skill_service import SONGWRITING_SKILL, SkillService  # noqa: E402
from backend.services.songwriting_service import SongwritingService  # noqa: E402


class FakeLLM:
    def __init__(self, lyric_resp="la la la", chord_resp="C G Am F") -> None:
        self.lyric_resp = lyric_resp
        self.chord_resp = chord_resp

    async def complete(self, history):
        last = history[-1].content.lower()
        if "chord" in last:
            return self.chord_resp
        return self.lyric_resp


class FakeArt:
    async def generate_album_art(self, title, themes):
        return "/fake/url.png"


class FailingArt:
    async def generate_album_art(self, title, themes):  # pragma: no cover - error path
        raise RuntimeError("boom")


async def _generate(svc: SongwritingService):
    return await svc.generate_draft(
        creator_id=1,
        title="Test",
        genre="rock",
        themes=["love", "hope", "loss"],
    )


def test_list_drafts_includes_co_writers():
    async def run():
        svc = SongwritingService(llm_client=FakeLLM(), originality=OriginalityService())
        d1 = await svc.generate_draft(
            creator_id=1,
            title="A",
            genre="rock",
            themes=["x", "y", "z"],
        )
        svc.add_co_writer(d1.id, user_id=1, co_writer_id=2)
        d2 = await svc.generate_draft(
            creator_id=3,
            title="B",
            genre="rock",
            themes=["x", "y", "z"],
        )
        assert {d.id for d in svc.list_drafts(1)} == {d1.id}
        assert {d.id for d in svc.list_drafts(2)} == {d1.id}
        assert {d.id for d in svc.list_drafts(3)} == {d2.id}

    asyncio.run(run())


def test_theme_validation():
    async def run():
        svc = SongwritingService(llm_client=FakeLLM(), originality=OriginalityService())
        with pytest.raises(ValueError):
            await svc.generate_draft(
                creator_id=1,
                title="t",
                genre="rock",
                themes=["only", "two"],
            )

    asyncio.run(run())


def test_generate_draft_with_art_and_chords():
    async def run():
        svc = SongwritingService(
            llm_client=FakeLLM(), art_service=FakeArt(), originality=OriginalityService()
        )
        draft = await _generate(svc)
        assert draft.lyrics == "la la la"
        assert draft.chord_progression == "C G Am F"
        assert draft.album_art_url == "/fake/url.png"

    asyncio.run(run())


def test_art_fallback_and_chord_default():
    async def run():
        svc = SongwritingService(
            llm_client=FakeLLM(chord_resp=""),
            art_service=FailingArt(),
            originality=OriginalityService(),
        )
        draft = await _generate(svc)
        assert draft.chord_progression == "C G Am F"
        assert draft.album_art_url is None

    asyncio.run(run())


def test_duplicate_detection_triggers_warning_and_dispute():
    class FakeLegal:
        def __init__(self):
            self.cases = []

        def create_case(self, plaintiff_id, defendant_id, description):
            self.cases.append((plaintiff_id, defendant_id, description))

        def register_copyright(self, song_id, lyrics):
            pass

    async def run():
        legal = FakeLegal()
        svc = SongwritingService(
            llm_client=FakeLLM(),
            art_service=FakeArt(),
            legal=legal,
            originality=OriginalityService(),
        )
        await _generate(svc)  # first draft stores hash
        dup = await _generate(svc)  # second draft should warn
        assert dup.plagiarism_warning == "possible_plagiarism"
        assert legal.cases  # dispute logged

    asyncio.run(run())


def test_registration_calls_legal_service():
    class RecordingLegal:
        def __init__(self):
            self.registered = []

        def create_case(self, *a, **k):
            pass

        def register_copyright(self, song_id, lyrics):
            self.registered.append((song_id, lyrics))

    async def run():
        legal = RecordingLegal()
        svc = SongwritingService(
            llm_client=FakeLLM(),
            art_service=FakeArt(),
            legal=legal,
            originality=OriginalityService(),
        )
        draft = await svc.generate_draft(
            creator_id=1,
            title="Test",
            genre="rock",
            themes=["love", "hope", "loss"],
            register_copyright=True,
        )
        assert legal.registered and legal.registered[0][0] == draft.id


def test_xp_gain_and_quality_modifier():
    async def run():
        skills = SkillService()
        skills.train(1, SONGWRITING_SKILL, 400)
        svc = SongwritingService(
            llm_client=FakeLLM(), art_service=FakeArt(), skill_service=skills
        )
        draft = await _generate(svc)
        assert draft.metadata.quality_modifier == pytest.approx(1.4)
        assert skills.get_songwriting_skill(1).xp == 410
        svc.update_draft(draft.id, 1, lyrics="new lyrics")
        assert skills.get_songwriting_skill(1).xp == 415

def _get_band_service() -> BandService:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return BandService(SessionLocal)


def test_versioning_and_band_mates():
    async def run():
        band_service = _get_band_service()
        band = band_service.create_band(user_id=1, band_name="AI Band", genre="rock")
        svc = SongwritingService(llm_client=FakeLLM(), band_service=band_service)
        draft = await svc.generate_draft(
            creator_id=band.id,
            title="collab",
            genre="rock",
            themes=["a", "b", "c"],
        )
        # initial version saved
        assert len(svc.list_versions(draft.id)) == 1


        # unauthorized user cannot edit until added to band
        with pytest.raises(PermissionError):
            svc.update_draft(draft.id, user_id=2, lyrics="hack")

        # add a band member and allow edits
        band_service.add_member(band.id, user_id=2)
        svc.update_draft(draft.id, user_id=2, lyrics="co-write", chord_progression="A B")

        # add a co-writer and allow edits
        svc.add_co_writer(draft.id, user_id=1, co_writer_id=2)
        svc.update_draft(draft.id, user_id=2, lyrics="co-write", chord_progression="A B")

        versions = svc.list_versions(draft.id)
        assert len(versions) == 3
        assert versions[-1].author_id == 2

        # cannot add non-bandmate
        with pytest.raises(PermissionError):
            svc.add_co_writer(draft.id, user_id=1, co_writer_id=3)

        # unauthorized user
        with pytest.raises(PermissionError):
            svc.update_draft(draft.id, user_id=3, lyrics="hack")

    asyncio.run(run())


def test_theme_updates_persist_and_versioned():
    async def run():
        svc = SongwritingService(
            llm_client=FakeLLM(), art_service=FakeArt(), originality=OriginalityService()
        )
        draft = await _generate(svc)
        new_themes = ["peace", "joy", "truth"]
        svc.update_draft(draft.id, user_id=1, themes=new_themes)
        assert svc.get_draft(draft.id).themes == new_themes
        assert svc.get_song(draft.id).themes == new_themes
        versions = svc.list_versions(draft.id)
        assert len(versions) == 2
        assert versions[-1].themes == new_themes

    asyncio.run(run())


def test_update_draft_invalid_themes():
    async def run():
        svc = SongwritingService(
            llm_client=FakeLLM(), art_service=FakeArt(), originality=OriginalityService()
        )
        draft = await _generate(svc)
        with pytest.raises(ValueError, match="exactly_three_themes_required"):
            svc.update_draft(draft.id, user_id=1, themes=["only", "two"])
        with pytest.raises(ValueError, match="unknown_theme"):
            svc.update_draft(
                draft.id,
                user_id=1,
                themes=["love", "hope", "invalid"],
            )

    asyncio.run(run())


def test_chemistry_quality_modifier():
    class StubChem:
        def __init__(self, score):
            self.score = score

        def initialize_pair(self, a, b):
            return type("P", (), {"score": self.score})()

        def adjust_pair(self, a, b, d):
            return self.initialize_pair(a, b)

    async def run():
        high = SongwritingService(llm_client=FakeLLM(), chemistry_service=StubChem(90))
        low = SongwritingService(llm_client=FakeLLM(), chemistry_service=StubChem(10))
        high._co_writers[high._counter] = {2}
        low._co_writers[low._counter] = {2}
        draft_high = await _generate(high)
        draft_low = await _generate(low)
        assert draft_high.metadata.quality_modifier == pytest.approx(1.4)
        assert draft_low.metadata.quality_modifier == pytest.approx(0.6)
        assert draft_high.metadata.chemistry == 90
        assert draft_low.metadata.chemistry == 10

    asyncio.run(run())


def test_add_co_writer_self_invite():
    async def run():
        svc = SongwritingService(llm_client=FakeLLM(), originality=OriginalityService())
        draft = await _generate(svc)
        with pytest.raises(ValueError):
            svc.add_co_writer(draft.id, user_id=1, co_writer_id=1)
        assert not svc.get_co_writers(draft.id)

    asyncio.run(run())


def test_add_co_writer_duplicate_invite():
    async def run():
        svc = SongwritingService(llm_client=FakeLLM(), originality=OriginalityService())
        draft = await _generate(svc)
        svc.add_co_writer(draft.id, user_id=1, co_writer_id=2)
        with pytest.raises(ValueError):
            svc.add_co_writer(draft.id, user_id=1, co_writer_id=2)
        assert svc.get_co_writers(draft.id) == {2}

    asyncio.run(run())


def test_intelligence_boosts_quality():
    async def run():
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        CharacterBase.metadata.create_all(bind=engine)
        AvatarBase.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        avatar_svc = AvatarService(SessionLocal)
        with SessionLocal() as session:
            char = Character(name="Smart", genre="rock", trait="wise", birthplace="Earth")
            session.add(char)
            session.commit()
            cid = char.id
        avatar_svc.create_avatar(
            AvatarCreate(
                character_id=cid,
                nickname="Brain",
                body_type="slim",
                skin_tone="pale",
                face_shape="oval",
                hair_style="short",
                hair_color="black",
                top_clothing="tshirt",
                bottom_clothing="jeans",
                shoes="boots",
                intelligence=80,
            )
        )
        skills = SkillService()
        svc = SongwritingService(
            llm_client=FakeLLM(),
            originality=OriginalityService(),
            avatar_service=avatar_svc,
            skill_service=skills,
        )
        draft = await svc.generate_draft(
            creator_id=1,
            title="Test",
            genre="rock",
            themes=["love", "hope", "loss"],
        )
        assert draft.metadata.quality_modifier == pytest.approx(1.3, rel=1e-2)

    asyncio.run(run())


def test_creativity_boosts_quality():
    async def run():
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        CharacterBase.metadata.create_all(bind=engine)
        AvatarBase.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        avatar_svc = AvatarService(SessionLocal)
        with SessionLocal() as session:
            char = Character(name="Muse", genre="rock", trait="inspired", birthplace="Earth")
            session.add(char)
            session.commit()
            cid = char.id
        avatar_svc.create_avatar(
            AvatarCreate(
                character_id=cid,
                nickname="Muse",
                body_type="slim",
                skin_tone="pale",
                face_shape="oval",
                hair_style="short",
                hair_color="black",
                top_clothing="tshirt",
                bottom_clothing="jeans",
                shoes="boots",
                creativity=80,
            )
        )
        skills = SkillService()
        svc = SongwritingService(
            llm_client=FakeLLM(),
            originality=OriginalityService(),
            avatar_service=avatar_svc,
            skill_service=skills,
        )
        draft = await svc.generate_draft(
            creator_id=1,
            title="Test",
            genre="rock",
            themes=["love", "hope", "loss"],
        )
        assert draft.metadata.quality_modifier == pytest.approx(1.3, rel=1e-2)

    asyncio.run(run())



def test_co_writer_invite_requires_acceptance_before_access():
    async def run():
        svc = SongwritingService(llm_client=FakeLLM(), originality=OriginalityService())
        draft = await _generate(svc)

        svc.invite_co_writer(draft.id, user_id=1, co_writer_id=2)

        assert svc.get_co_writers(draft.id) == set()
        assert svc.get_pending_invitees(draft.id) == {2}
        assert svc.list_pending_invites(2) == [
            {
                "draft_id": draft.id,
                "title": draft.title,
                "genre": draft.genre,
                "inviter_id": 1,
            }
        ]

        with pytest.raises(PermissionError):
            svc.update_draft(draft.id, user_id=2, lyrics="too early")

        svc.accept_co_writer_invite(draft.id, user_id=2)
        assert svc.get_pending_invitees(draft.id) == set()
        assert svc.get_co_writers(draft.id) == {2}

        svc.update_draft(draft.id, user_id=2, lyrics="accepted")
        assert svc.get_draft(draft.id).lyrics == "accepted"

    asyncio.run(run())


def test_co_writer_invite_can_be_declined_and_reinvited():
    async def run():
        svc = SongwritingService(llm_client=FakeLLM(), originality=OriginalityService())
        draft = await _generate(svc)

        svc.invite_co_writer(draft.id, user_id=1, co_writer_id=2)
        with pytest.raises(ValueError, match="already_invited"):
            svc.invite_co_writer(draft.id, user_id=1, co_writer_id=2)

        svc.decline_co_writer_invite(draft.id, user_id=2)
        assert svc.list_pending_invites(2) == []
        assert svc.get_co_writers(draft.id) == set()

        svc.invite_co_writer(draft.id, user_id=1, co_writer_id=2)
        assert svc.get_pending_invitees(draft.id) == {2}

    asyncio.run(run())


def test_accept_or_decline_missing_invite_fails():
    svc = SongwritingService(llm_client=FakeLLM(), originality=OriginalityService())
    with pytest.raises(KeyError, match="invite_not_found"):
        svc.accept_co_writer_invite(999, user_id=2)
    with pytest.raises(KeyError, match="invite_not_found"):
        svc.decline_co_writer_invite(999, user_id=2)

def test_completion_tracks_time_quality_and_single_polish_session():
    class StubRandom:
        def __init__(self):
            self.values = iter([60, 40, 5])

        def randint(self, low, high):
            return next(self.values)

    async def run():
        svc = SongwritingService(llm_client=FakeLLM(), originality=OriginalityService())
        svc.rng = StubRandom()
        draft = await _generate(svc)

        svc.update_draft(draft.id, user_id=1, lyrics="final lyrics")
        completed = svc.complete_song(draft.id, user_id=1)

        assert completed["newly_completed"] is True
        assert completed["quality_score"] == 50
        assert completed["writing_time"] == {
            "initial_minutes": 60,
            "revision_sessions": 1,
            "revision_minutes": 30,
            "polish_minutes": 0,
            "total_minutes": 90,
        }
        assert completed["polish"]["available"] is True
        assert completed["polish"]["success_chance"] == 60

        # Re-fetching completion is idempotent and does not re-roll the chance.
        again = svc.complete_song(draft.id, user_id=1)
        assert again["newly_completed"] is False
        assert again["polish"]["success_chance"] == 60

        polished = svc.polish_song(draft.id, user_id=1)
        assert polished["polish"]["attempted"] is True
        assert polished["polish"]["succeeded"] is True
        assert polished["polish"]["quality_bonus"] == 5
        assert polished["quality_score"] == 55
        assert polished["writing_time"]["polish_minutes"] == 60
        assert polished["writing_time"]["total_minutes"] == 150

        with pytest.raises(ValueError, match="polish_already_attempted"):
            svc.polish_song(draft.id, user_id=1)

        with pytest.raises(ValueError, match="song_already_completed"):
            svc.update_draft(draft.id, user_id=1, lyrics="too late")

    asyncio.run(run())
