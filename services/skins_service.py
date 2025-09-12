skins = []
user_inventory = {}

def submit_new_skin(data):
    skins.append({
        "name": data["name"],
        "creator_id": data["creator_id"],
        "type": data["type"],
        "image_url": data["image_url"],
        "description": data["description"],
        "status": "pending",
        "price": data["price"],
        "votes": 0
    })
    return {"status": "submitted", "skin": data["name"]}

def get_pending_skins():
    return [s for s in skins if s["status"] == "pending"]

def vote_on_skin(data):
    for skin in skins:
        if skin["name"] == data["skin_name"]:
            if data["vote_type"] == "up":
                skin["votes"] += 1
            elif data["vote_type"] == "down":
                skin["votes"] -= 1
            return {"status": "voted", "skin": skin}
    return {"error": "skin not found"}

def purchase_user_skin(data):
    user_id = data["user_id"]
    if user_id not in user_inventory:
        user_inventory[user_id] = []
    user_inventory[user_id].append(data["skin_name"])
    return {"status": "purchased", "user_id": user_id, "skin": data["skin_name"]}