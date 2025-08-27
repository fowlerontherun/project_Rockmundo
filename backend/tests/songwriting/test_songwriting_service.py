import pytest

import asyncio
import pytest

from backend.services.songwriting_service import SongwritingService


class FakeLLM:
    async def complete(self, history):
        last = history[-1].content
        if "chord" in last.lower():
            return "C G Am F"
        return "la la la"


def test_generate_and_store_draft():
    async def run():
        svc = SongwritingService(llm_client=FakeLLM())
        draft = await svc.generate_draft(creator_id=1, prompt="love story", style="rock")
        assert draft.lyrics == "la la la"
        assert draft.chords == "C G Am F"
        song = svc.get_song(draft.id)
        assert song is not None
        assert song.lyrics == draft.lyrics
        assert song.owner_band_id == 1

    asyncio.run(run())


def test_permission_on_update():
    async def run():
        svc = SongwritingService(llm_client=FakeLLM())
        draft = await svc.generate_draft(creator_id=1, prompt="sad", style="blues")
        svc.update_draft(draft.id, user_id=1, lyrics="updated")
        assert svc.get_draft(draft.id).lyrics == "updated"
        with pytest.raises(PermissionError):
            svc.update_draft(draft.id, user_id=2, lyrics="hack")

    asyncio.run(run())
