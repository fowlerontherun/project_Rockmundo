"""Realtime helpers for social notifications."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple  # noqa: F401

from .gateway import hub, topic_for_user

logger = logging.getLogger(__name__)


@dataclass
class FriendRequestEvent:
    """Payload sent when a user receives a friend request."""

    type: str = "friend_request"
    from_user_id: int = 0


@dataclass
class ForumReplyEvent:
    """Payload sent when a user's forum post receives a reply."""

    type: str = "forum_reply"
    thread_id: int = 0
    post_id: int = 0


async def publish_friend_request(target_user_id: int, from_user_id: int) -> int:
    """Notify a user of a new friend request."""

    payload: Dict[str, int] = FriendRequestEvent(from_user_id=int(from_user_id)).__dict__
    topic = topic_for_user(int(target_user_id))
    return await hub.publish(topic, payload)


async def publish_forum_reply(target_user_id: int, thread_id: int, post_id: int) -> int:
    """Notify a user that someone replied to their forum post."""

    payload: Dict[str, int] = ForumReplyEvent(
        thread_id=int(thread_id), post_id=int(post_id)
    ).__dict__
    topic = topic_for_user(int(target_user_id))
    return await hub.publish(topic, payload)

