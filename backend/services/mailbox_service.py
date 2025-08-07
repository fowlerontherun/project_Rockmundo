from datetime import datetime

mail_store = {}

def send_mail(payload):
    recipient_id = payload["recipient_id"]
    if recipient_id not in mail_store:
        mail_store[recipient_id] = []
    mail = {
        "sender_id": payload["sender_id"],
        "subject": payload["subject"],
        "message": payload["message"],
        "message_type": payload.get("message_type", "system"),
        "timestamp": datetime.utcnow(),
        "archived": False
    }
    mail_store[recipient_id].append(mail)
    return {"status": "sent", "mail": mail}

def get_inbox(user_id):
    return {"inbox": mail_store.get(user_id, [])}

def archive_mail(payload):
    user_id = payload["user_id"]
    index = payload["message_index"]
    if user_id in mail_store and 0 <= index < len(mail_store[user_id]):
        mail_store[user_id][index]["archived"] = True
        return {"status": "archived", "message": mail_store[user_id][index]}
    return {"error": "Invalid request"}