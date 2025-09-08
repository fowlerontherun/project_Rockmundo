from datetime import datetime

# TODO: Replace in-memory stores with persistent storage to avoid data loss on
# restart.
chat_store: dict[int, list] = {}
group_chat_store: dict[int, list] = {}
group_members: dict[int, set[int]] = {}
# Registry to track which groups a user belongs to
user_groups: dict[int, set[int]] = {}


def add_user_to_group(group_id, user_id):
    if group_id not in group_members:
        group_members[group_id] = set()
    group_members[group_id].add(user_id)

    if user_id not in user_groups:
        user_groups[user_id] = set()
    user_groups[user_id].add(group_id)


def send_message(data):
    sender = data["sender_id"]
    recipient = data["recipient_id"]
    message = {
        "sender_id": sender,
        "recipient_id": recipient,
        "content": data["content"],
        "timestamp": str(datetime.utcnow()),
    }
    chat_store.setdefault(recipient, []).append(message)
    chat_store.setdefault(sender, []).append(message)
    return {"status": "message_sent", "message": message}


def send_group_chat(data):
    group_id = data["group_id"]
    add_user_to_group(group_id, data["sender_id"])
    if group_id not in group_chat_store:
        group_chat_store[group_id] = []
    group_chat_store[group_id].append(
        {
            "sender_id": data["sender_id"],
            "content": data["content"],
            "timestamp": str(datetime.utcnow()),
        }
    )
    return {"status": "group_message_sent"}


def get_user_chat_history(user_id):
    groups = user_groups.get(user_id, set())
    return {
        "direct_messages": chat_store.get(user_id, []),
        "group_chats": {gid: group_chat_store.get(gid, []) for gid in groups},
    }