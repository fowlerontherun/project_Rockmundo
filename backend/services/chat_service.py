from datetime import datetime

chat_store = {}
group_chat_store = {}

def send_message(data):
    sender = data["sender_id"]
    recipient = data["recipient_id"]
    message = {
        "sender_id": sender,
        "recipient_id": recipient,
        "content": data["content"],
        "timestamp": str(datetime.utcnow())
    }
    if recipient not in chat_store:
        chat_store[recipient] = []
    chat_store[recipient].append(message)
    return {"status": "message_sent", "message": message}

def send_group_chat(data):
    group_id = data["group_id"]
    if group_id not in group_chat_store:
        group_chat_store[group_id] = []
    group_chat_store[group_id].append({
        "sender_id": data["sender_id"],
        "content": data["content"],
        "timestamp": str(datetime.utcnow())
    })
    return {"status": "group_message_sent"}

def get_user_chat_history(user_id):
    return {
        "direct_messages": chat_store.get(user_id, []),
        "group_chats": {
            group_id: msgs for group_id, msgs in group_chat_store.items()
            if any(msg["sender_id"] == user_id for msg in msgs)
        }
    }