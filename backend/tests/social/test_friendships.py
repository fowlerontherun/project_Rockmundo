import asyncio
import sqlite3

from backend.services.social_service import social_service
from backend.realtime import social_gateway


def test_friend_request_flow(tmp_path, monkeypatch):
    async def run():
        social_service.db_path = str(tmp_path / "social.db")
        social_service.ensure_schema()
        with sqlite3.connect(social_service.db_path) as conn:
            conn.execute("DELETE FROM friend_requests")
            conn.execute("DELETE FROM friendships")
            conn.commit()

        async def fake_publish(target_user_id: int, from_user_id: int) -> int:
            return 0

        monkeypatch.setattr(social_gateway, "publish_friend_request", fake_publish)

        req = await social_service.send_friend_request(1, 2)
        await social_service.accept_friend_request(req.id, 2)
        assert social_service.list_friends(1) == [2]
        assert social_service.list_friends(2) == [1]

    asyncio.run(run())
