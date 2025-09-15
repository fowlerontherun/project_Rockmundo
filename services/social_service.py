from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Set

from realtime.social_gateway import publish_forum_reply, publish_friend_request


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


DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class SocialService:
    """Social features with persistent friend data."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.ensure_schema()
        self._groups: Dict[int, Group] = {}
        self._group_members: Dict[int, Set[int]] = {}
        self._threads: Dict[int, ForumThread] = {}
        self._posts: Dict[int, ForumPost] = {}
        self._ids = {"group": 1, "thread": 1, "post": 1}

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS friend_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER NOT NULL,
                    to_user_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """,
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS friendships (
                    user_a INTEGER NOT NULL,
                    user_b INTEGER NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(user_a, user_b)
                )
                """,
            )
            conn.commit()

    # ---- Friend requests ----
    async def send_friend_request(self, from_user_id: int, to_user_id: int) -> FriendRequest:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO friend_requests(from_user_id, to_user_id, status) VALUES (?, ?, 'pending')",
                (from_user_id, to_user_id),
            )
            rid = cur.lastrowid
            conn.commit()
        await publish_friend_request(to_user_id, from_user_id)
        return FriendRequest(rid, from_user_id, to_user_id)

    def list_friends(self, user_id: int) -> List[int]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT user_a, user_b FROM friendships WHERE user_a = ? OR user_b = ?",
                (user_id, user_id),
            )
            rows = cur.fetchall()
            friends: List[int] = []
            for a, b in rows:
                friends.append(b if a == user_id else a)
            return friends

    async def accept_friend_request(self, request_id: int, user_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT from_user_id, to_user_id, status FROM friend_requests WHERE id = ?",
                (request_id,),
            )
            row = cur.fetchone()
            if not row or row[1] != user_id or row[2] != "pending":
                raise ValueError("Invalid friend request")
            from_id, to_id, _ = row
            cur.execute(
                "UPDATE friend_requests SET status = 'accepted' WHERE id = ?",
                (request_id,),
            )
            a, b = sorted((from_id, to_id))
            cur.execute(
                "INSERT OR IGNORE INTO friendships(user_a, user_b) VALUES (?, ?)",
                (a, b),
            )
            conn.commit()

    async def reject_friend_request(self, request_id: int, user_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT to_user_id, status FROM friend_requests WHERE id = ?",
                (request_id,),
            )
            row = cur.fetchone()
            if not row or row[0] != user_id or row[1] != "pending":
                raise ValueError("Invalid friend request")
            cur.execute(
                "UPDATE friend_requests SET status = 'rejected' WHERE id = ?",
                (request_id,),
            )
            conn.commit()

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
