from datetime import datetime

# TODO: Replace in-memory stores with persistent storage to avoid data loss on
# restart.
chat_store = {}
group_chat_store = {}
group_members = {}


def add_user_to_group(group_id, user_id):
    if group_id not in group_members:
        group_members[group_id] = set()
    group_members[group_id].add(user_id)


def send_message(data):
    sender = data["sender_id"]
    recipient = data["recipient_id"]
    message = {
        "sender_id": sender,
        "recipient_id": recipient,
        "content": data["content"],
        "timestamp": str(datetime.utcnow()),
    }
    if recipient not in chat_store:
        chat_store[recipient] = []
    if sender not in chat_store:
        chat_store[sender] = []
    chat_store[recipient].append(message)
    chat_store[sender].append(message)
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
    user_groups = [
        group_id for group_id, members in group_members.items() if user_id in members
    ]
    return {
        "direct_messages": chat_store.get(user_id, []),
        "group_chats": {group_id: group_chat_store.get(group_id, []) for group_id in user_groups},
    }