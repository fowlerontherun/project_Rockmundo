import asyncio
import pytest

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
        svc = SongwritingService(llm_client=FakeLLM())
        with pytest.raises(ValueError):
            await svc.generate_draft(1, "t", "rock", ["only", "two"])

    asyncio.run(run())


def test_generate_draft_with_art_and_chords():
    async def run():
        svc = SongwritingService(llm_client=FakeLLM(), art_service=FakeArt())
        draft = await _generate(svc)
        assert draft.lyrics == "la la la"
        assert draft.chord_progression == "C G Am F"
        assert draft.album_art_url == "/fake/url.png"

    asyncio.run(run())


def test_art_fallback_and_chord_default():
    async def run():
        svc = SongwritingService(llm_client=FakeLLM(chord_resp=""), art_service=FailingArt())
        draft = await _generate(svc)
        assert draft.chord_progression == "C G Am F"
        assert draft.album_art_url is None

    asyncio.run(run())



def test_versioning_and_co_writers():
    async def run():
        svc = SongwritingService(llm_client=FakeLLM())
        draft = await svc.generate_draft(creator_id=1, prompt="collab", style="rock")
        # initial version saved
        assert len(svc.list_versions(draft.id)) == 1

        # add a co-writer and allow edits
        svc.add_co_writer(draft.id, user_id=1, co_writer_id=2)
        svc.update_draft(draft.id, user_id=2, lyrics="co-write", chords="A B")
        versions = svc.list_versions(draft.id)
        assert len(versions) == 2
        assert versions[-1].author_id == 2

        # unauthorized user
        with pytest.raises(PermissionError):
            svc.update_draft(draft.id, user_id=3, lyrics="hack")

    asyncio.run(run())

