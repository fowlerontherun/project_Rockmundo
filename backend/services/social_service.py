from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from backend.realtime.social_gateway import publish_forum_reply, publish_friend_request


@dataclass
class FriendRequest:
    id: int
    from_user_id: int
    to_user_id: int
    status: str = "pending"


@dataclass
class Group:
    id: int
    name: str
    owner_id: int


@dataclass
class ForumThread:
    id: int
    title: str
    creator_id: int
    group_id: Optional[int]


@dataclass
class ForumPost:
    id: int
    thread_id: int
    author_id: int
    content: str
    parent_post_id: Optional[int]


class SocialService:
    """In-memory social features for friend requests, groups and forums."""

    def __init__(self) -> None:
        self._friend_requests: Dict[int, FriendRequest] = {}
        self._friendships: Set[Tuple[int, int]] = set()
        self._groups: Dict[int, Group] = {}
        self._group_members: Dict[int, Set[int]] = {}
        self._threads: Dict[int, ForumThread] = {}
        self._posts: Dict[int, ForumPost] = {}
        self._ids = {"friend_request": 1, "group": 1, "thread": 1, "post": 1}

    # ---- Friend requests ----
    async def send_friend_request(self, from_user_id: int, to_user_id: int) -> FriendRequest:
        rid = self._ids["friend_request"]
        self._ids["friend_request"] += 1
        req = FriendRequest(rid, from_user_id, to_user_id)
        self._friend_requests[rid] = req
        await publish_friend_request(to_user_id, from_user_id)
        return req

    def list_friends(self, user_id: int) -> List[int]:
        friends: List[int] = []
        for a, b in self._friendships:
            if a == user_id:
                friends.append(b)
            elif b == user_id:
                friends.append(a)
        return friends

    async def accept_friend_request(self, request_id: int, user_id: int) -> None:
        req = self._friend_requests.get(request_id)
        if not req or req.to_user_id != user_id or req.status != "pending":
            raise ValueError("Invalid friend request")
        req.status = "accepted"
        self._friendships.add(tuple(sorted((req.from_user_id, req.to_user_id))))

    async def reject_friend_request(self, request_id: int, user_id: int) -> None:
        req = self._friend_requests.get(request_id)
        if not req or req.to_user_id != user_id or req.status != "pending":
            raise ValueError("Invalid friend request")
        req.status = "rejected"

    # ---- Groups ----
    def create_group(self, owner_id: int, name: str) -> Group:
        gid = self._ids["group"]
        self._ids["group"] += 1
        grp = Group(gid, name, owner_id)
        self._groups[gid] = grp
        self._group_members[gid] = {owner_id}
        return grp

    def join_group(self, group_id: int, user_id: int) -> None:
        if group_id not in self._groups:
            raise ValueError("Group not found")
        self._group_members.setdefault(group_id, set()).add(user_id)

    def leave_group(self, group_id: int, user_id: int) -> None:
        members = self._group_members.get(group_id)
        if not members or user_id not in members:
            raise ValueError("Not a member")
        if self._groups[group_id].owner_id == user_id:
            raise ValueError("Owner cannot leave group")
        members.remove(user_id)

    def list_group_members(self, group_id: int) -> List[int]:
        return sorted(self._group_members.get(group_id, set()))

    # ---- Forum threads ----
    def create_thread(self, creator_id: int, title: str, group_id: Optional[int] = None) -> ForumThread:
        tid = self._ids["thread"]
        self._ids["thread"] += 1
        thread = ForumThread(tid, title, creator_id, group_id)
        self._threads[tid] = thread
        return thread

    async def add_post(
        self,
        thread_id: int,
        author_id: int,
        content: str,
        parent_post_id: Optional[int] = None,
    ) -> ForumPost:
        if thread_id not in self._threads:
            raise ValueError("Thread not found")
        pid = self._ids["post"]
        self._ids["post"] += 1
        post = ForumPost(pid, thread_id, author_id, content, parent_post_id)
        self._posts[pid] = post
        if parent_post_id:
            parent = self._posts.get(parent_post_id)
            if parent:
                await publish_forum_reply(parent.author_id, thread_id, pid)
        return post

    def get_thread_posts(self, thread_id: int) -> List[ForumPost]:
        return [p for p in self._posts.values() if p.thread_id == thread_id]


social_service = SocialService()
