# services/lifestyle_service.py

from datetime import datetime
import random

def calculate_lifestyle_score(data):
    # Composite score from normalized attributes
    score = (
        (min(data["sleep_hours"], 8) / 8.0) * 20 +
        (100 - data["stress"]) * 0.2 +
        data["training_discipline"] * 0.2 +
        data["mental_health"] * 0.4
    )
    return round(score, 2)

def evaluate_lifestyle_risks(data):
    events = []
    if data["stress"] > 85 and random.random() < 0.2:
        events.append("burnout")
    if data["drinking"] == "heavy" and random.random() < 0.15:
        events.append("illness")
    if data["sleep_hours"] < 6 and random.random() < 0.2:
        events.append("mental fatigue")
    return events
