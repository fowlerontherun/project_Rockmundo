import asyncio

import pytest

from backend.services.originality_service import OriginalityService
from backend.services.skill_service import SONGWRITING_SKILL, SkillService
from backend.services.songwriting_service import SongwritingService


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


def test_theme_validation():
    async def run():
        svc = SongwritingService(llm_client=FakeLLM(), originality=OriginalityService())
        with pytest.raises(ValueError):
            await svc.generate_draft(1, "t", "rock", ["only", "two"])

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

def test_versioning_and_co_writers():
    async def run():
        svc = SongwritingService(llm_client=FakeLLM())
        draft = await svc.generate_draft(
            creator_id=1,
            title="collab",
            genre="rock",
            themes=["a", "b", "c"],
        )
        # initial version saved
        assert len(svc.list_versions(draft.id)) == 1

        # add a co-writer and allow edits
        svc.add_co_writer(draft.id, user_id=1, co_writer_id=2)
        svc.update_draft(draft.id, user_id=2, lyrics="co-write", chord_progression="A B")
        versions = svc.list_versions(draft.id)
        assert len(versions) == 2
        assert versions[-1].author_id == 2

        # unauthorized user
        with pytest.raises(PermissionError):
            svc.update_draft(draft.id, user_id=3, lyrics="hack")
    asyncio.run(run())

