from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from backend.realtime.publish import (
    publish_fan_club_event_invite,
    publish_fan_club_post,
)
from services.avatar_service import AvatarService


@dataclass
class FanClub:
    id: int
    name: str
    owner_id: int
    description: Optional[str] = None


@dataclass
class FanClubThread:
    id: int
    fan_club_id: int
    title: str
    creator_id: int


@dataclass
class FanClubPost:
    id: int
    thread_id: int
    author_id: int
    content: str
    engagement: int = 0


@dataclass
class FanClubEvent:
    id: int
    fan_club_id: int
    title: str
    scheduled_at: datetime
    creator_id: int


class FanClubService:
    """In-memory fan club management with posts and events."""

    def __init__(self, avatar_service: AvatarService | None = None) -> None:
        self.avatar_service = avatar_service or AvatarService()
        self._clubs: Dict[int, FanClub] = {}
        self._members: Dict[int, Dict[int, str]] = {}
        self._threads: Dict[int, FanClubThread] = {}
        self._posts: Dict[int, FanClubPost] = {}
        self._events: Dict[int, FanClubEvent] = {}
        self._ids = {"club": 1, "thread": 1, "post": 1, "event": 1}

    # ---- Clubs ----
    def create_club(self, owner_id: int, name: str, description: Optional[str] = None) -> FanClub:
        cid = self._ids["club"]
        self._ids["club"] += 1
        club = FanClub(cid, name, owner_id, description)
        self._clubs[cid] = club
        self._members[cid] = {owner_id: "owner"}
        return club

    def join_club(self, club_id: int, user_id: int, role: str = "member") -> None:
        if club_id not in self._clubs:
            raise ValueError("Fan club not found")
        self._members.setdefault(club_id, {})[user_id] = role

    def get_member_role(self, club_id: int, user_id: int) -> Optional[str]:
        return self._members.get(club_id, {}).get(user_id)

    def list_members(self, club_id: int) -> List[int]:
        return list(self._members.get(club_id, {}).keys())

    # ---- Threads & Posts ----
    def create_thread(self, club_id: int, creator_id: int, title: str) -> FanClubThread:
        if creator_id not in self._members.get(club_id, {}):
            raise ValueError("Not a club member")
        tid = self._ids["thread"]
        self._ids["thread"] += 1
        thread = FanClubThread(tid, club_id, title, creator_id)
        self._threads[tid] = thread
        return thread

    async def add_post(self, thread_id: int, author_id: int, content: str) -> FanClubPost:
        thread = self._threads.get(thread_id)
        if not thread or author_id not in self._members.get(thread.fan_club_id, {}):
            raise ValueError("Thread not found or user not a member")
        pid = self._ids["post"]
        self._ids["post"] += 1
        avatar = self.avatar_service.get_avatar(author_id)
        charisma = avatar.charisma if avatar else 50
        engagement = max(1, charisma // 10)
        post = FanClubPost(pid, thread_id, author_id, content, engagement)
        self._posts[pid] = post
        await publish_fan_club_post(thread.fan_club_id, thread_id, pid)
        return post

    # ---- Events ----
    async def schedule_event(
        self, club_id: int, creator_id: int, title: str, scheduled_at: datetime
    ) -> FanClubEvent:
        if creator_id not in self._members.get(club_id, {}):
            raise ValueError("Not a club member")
        eid = self._ids["event"]
        self._ids["event"] += 1
        event = FanClubEvent(eid, club_id, title, scheduled_at, creator_id)
        self._events[eid] = event
        for uid in self.list_members(club_id):
            await publish_fan_club_event_invite(uid, club_id, eid)
        return event


fan_club_service = FanClubService()
