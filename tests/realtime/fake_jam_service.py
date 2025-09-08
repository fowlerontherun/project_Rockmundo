from __future__ import annotations

"""Test helpers providing a fake JamService for websocket tests."""

from dataclasses import dataclass
from typing import Dict, Set, Tuple


@dataclass
class FakeStream:
    user_id: int
    stream_id: str
    codec: str
    premium: bool
    started_at: str = "now"
    paused: bool = False


class FakeJamService:
    def __init__(self) -> None:
        self.sessions: Dict[str, Set[int]] = {}
        self.streams: Dict[Tuple[str, int], FakeStream] = {}
        self.invites: Dict[str, Set[int]] = {}

    def invite(self, session_id: str, inviter_id: int, invitee_id: int) -> None:
        self.invites.setdefault(session_id, set()).add(invitee_id)

    def join_session(self, session_id: str, user_id: int) -> None:
        self.sessions.setdefault(session_id, set()).add(user_id)

    def leave_session(self, session_id: str, user_id: int) -> None:
        users = self.sessions.get(session_id)
        if users:
            users.discard(user_id)
            self.streams.pop((session_id, user_id), None)
            if not users:
                self.sessions.pop(session_id, None)
                self.invites.pop(session_id, None)
                for key in list(self.streams):
                    if key[0] == session_id:
                        del self.streams[key]

    def start_stream(
        self, session_id: str, user_id: int, stream_id: str, codec: str, premium: bool = False
    ) -> FakeStream:
        stream = FakeStream(user_id, stream_id, codec, premium)
        self.streams[(session_id, user_id)] = stream
        return stream

    def stop_stream(self, session_id: str, user_id: int) -> None:
        self.streams.pop((session_id, user_id), None)

    def pause_stream(self, session_id: str, user_id: int) -> None:
        stream = self.streams.get((session_id, user_id))
        if stream:
            stream.paused = True

    def resume_stream(self, session_id: str, user_id: int) -> None:
        stream = self.streams.get((session_id, user_id))
        if stream:
            stream.paused = False
