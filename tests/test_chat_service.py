import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from backend.services import chat_service  # noqa: E402


def setup_function() -> None:  # type: ignore[override]
    chat_service.chat_store.clear()
    chat_service.group_chat_store.clear()
    chat_service.group_members.clear()
    chat_service.user_groups.clear()


def test_sender_sees_message() -> None:
    chat_service.send_message(
        {"sender_id": 1, "recipient_id": 2, "content": "hello"}
    )
    history_sender = chat_service.get_user_chat_history(1)
    history_recipient = chat_service.get_user_chat_history(2)

    assert history_sender["direct_messages"][0]["content"] == "hello"
    assert history_recipient["direct_messages"][0]["content"] == "hello"


def test_group_history_available_after_join() -> None:
    chat_service.add_user_to_group(100, 3)
    history = chat_service.get_user_chat_history(3)

    assert 100 in history["group_chats"]
    assert history["group_chats"][100] == []

