from datetime import datetime

labels = {}
contracts = {}

def create_music_label(data):
    label = {
        "label_id": data["label_id"],
        "name": data["name"],
        "owner_id": data.get("owner_id"),
        "founded": str(datetime.utcnow()),
        "fame": 0,
        "is_npc": data.get("is_npc", True)
    }
    labels[data["label_id"]] = label
    return {"status": "label_created", "label": label}

def offer_label_contract(data):
    contract = {
        "contract_id": data["contract_id"],
        "label_id": data["label_id"],
        "band_id": data["band_id"],
        "revenue_split": data["revenue_split"],
        "duration_weeks": data["duration_weeks"],
        "signed_on": str(datetime.utcnow()),
        "active": True
    }
    contracts[data["contract_id"]] = contract
    return {"status": "contract_offered", "contract": contract}

def get_all_labels():
    return {"labels": list(labels.values())}

def get_contracts_for_band(band_id):
    band_contracts = [c for c in contracts.values() if c["band_id"] == band_id]
    return {"contracts": band_contracts}