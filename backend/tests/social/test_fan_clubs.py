import asyncio
import json
from datetime import datetime, timedelta

from backend.services.fan_club_service import fan_club_service
from backend.realtime.gateway import hub, _Subscriber, topic_for_user


def test_fan_club_membership_and_notifications():
    # Create club and join member
    club = fan_club_service.create_club(owner_id=1, name="Fans")
    fan_club_service.join_club(club.id, 2)

    assert fan_club_service.get_member_role(club.id, 1) == "owner"
    assert fan_club_service.get_member_role(club.id, 2) == "member"

    # Create thread and subscribe to fan club topic
    thread = fan_club_service.create_thread(club.id, creator_id=1, title="Welcome")
    sub_club = _Subscriber()
    asyncio.get_event_loop().run_until_complete(
        hub.subscribe(f"fanclub:{club.id}", sub_club)
    )

    # Add post and expect notification
    asyncio.get_event_loop().run_until_complete(
        fan_club_service.add_post(thread.id, author_id=1, content="Hello")
    )
    msg = asyncio.get_event_loop().run_until_complete(
        asyncio.wait_for(sub_club.queue.get(), timeout=1.0)
    )
    data = json.loads(msg)
    assert data["data"]["type"] == "fan_club_post"
    assert data["data"]["thread_id"] == thread.id
    asyncio.get_event_loop().run_until_complete(
        hub.unsubscribe(f"fanclub:{club.id}", sub_club)
    )

    # Subscribe to user topic for event invite
    sub_user = _Subscriber()
    asyncio.get_event_loop().run_until_complete(
        hub.subscribe(topic_for_user(2), sub_user)
    )
    when = datetime.utcnow() + timedelta(days=1)
    asyncio.get_event_loop().run_until_complete(
        fan_club_service.schedule_event(club.id, 1, "Meetup", when)
    )
    msg2 = asyncio.get_event_loop().run_until_complete(
        asyncio.wait_for(sub_user.queue.get(), timeout=1.0)
    )
    data2 = json.loads(msg2)
    assert data2["data"]["type"] == "fan_club_event_invite"
    assert data2["data"]["fan_club_id"] == club.id
    asyncio.get_event_loop().run_until_complete(
        hub.unsubscribe(topic_for_user(2), sub_user)
    )
