# backend/realtime/publish.py
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .gateway import hub, topic_for_user, PULSE_TOPIC, ADMIN_JOBS_TOPIC

logger = logging.getLogger(__name__)


def topic_for_fan_club(fan_club_id: int) -> str:
    return f"fanclub:{int(fan_club_id)}"

async def publish_mail_unread(user_id: int, unread_count: Optional[int] = None) -> int:
    """
    Notify a specific user that their mail unread badge changed.
    Payload includes the unread_count if provided (else clients can refetch).
    Returns number of recipients (active subscribers).
    """
    payload: Dict[str, Any] = {"type": "mail_unread"}
    if unread_count is not None:
        payload["unread"] = int(unread_count)
    topic = topic_for_user(int(user_id))
    return await hub.publish(topic, payload)

async def publish_pulse_update(scoreboard: Dict[str, Any]) -> int:
    """
    Broadcast a public Pulse leaderboard tick to all listeners on 'pulse'.
    'scoreboard' should be a small, UI-ready dict (e.g., top N, deltas).
    """
    payload: Dict[str, Any] = {"type": "pulse_tick", "scoreboard": scoreboard}
    return await hub.publish(PULSE_TOPIC, payload)

async def publish_admin_job_status(event: Dict[str, Any]) -> int:
    """
    Broadcast admin job status messages—e.g., job started/finished, counts,
    errors—to listeners on 'admin:jobs' (e.g., admin dashboard).
    """
    payload: Dict[str, Any] = {"type": "admin_job", **event}
    return await hub.publish(ADMIN_JOBS_TOPIC, payload)

async def publish_friend_request(target_user_id: int, from_user_id: int) -> int:
    """Notify a user of a new friend request."""
    payload: Dict[str, Any] = {"type": "friend_request", "from_user_id": int(from_user_id)}
    topic = topic_for_user(int(target_user_id))
    return await hub.publish(topic, payload)


async def publish_forum_reply(target_user_id: int, thread_id: int, post_id: int) -> int:
    """Notify a user that someone replied to their forum post."""
    payload: Dict[str, Any] = {"type": "forum_reply", "thread_id": int(thread_id), "post_id": int(post_id)}
    topic = topic_for_user(int(target_user_id))
    return await hub.publish(topic, payload)


async def publish_fan_club_post(fan_club_id: int, thread_id: int, post_id: int) -> int:
    """Broadcast a new fan club post to all club subscribers."""
    payload: Dict[str, Any] = {
        "type": "fan_club_post",
        "fan_club_id": int(fan_club_id),
        "thread_id": int(thread_id),
        "post_id": int(post_id),
    }
    topic = topic_for_fan_club(int(fan_club_id))
    return await hub.publish(topic, payload)


async def publish_fan_club_event_invite(
    target_user_id: int, fan_club_id: int, event_id: int
) -> int:
    """Notify a user of a fan club event invitation."""
    payload: Dict[str, Any] = {
        "type": "fan_club_event_invite",
        "fan_club_id": int(fan_club_id),
        "event_id": int(event_id),
    }
    topic = topic_for_user(int(target_user_id))
    return await hub.publish(topic, payload)
