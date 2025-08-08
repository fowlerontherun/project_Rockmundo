
from models.ai_tour_manager import AITourManager
from datetime import datetime
import random

class AITourManagerService:
    def __init__(self, db):
        self.db = db

    def unlock_ai_manager(self, band_id):
        manager = AITourManager(id=None, band_id=band_id, unlocked=True, optimization_level=1)
        self.db.insert_ai_tour_manager(manager)
        return manager.to_dict()

    def upgrade_manager(self, band_id):
        manager = self.db.get_ai_tour_manager(band_id)
        if not manager or not manager['unlocked']:
            raise ValueError("AI Manager not unlocked")
        if manager['optimization_level'] >= 5:
            raise ValueError("Already maxed out")
        self.db.update_optimization_level(band_id, manager['optimization_level'] + 1)
        return self.db.get_ai_tour_manager(band_id)

    def generate_optimized_route(self, band_id, upcoming_cities):
        manager = self.db.get_ai_tour_manager(band_id)
        if not manager or not manager['unlocked']:
            raise ValueError("AI Manager not unlocked")
        level = manager['optimization_level']
        sorted_cities = sorted(upcoming_cities, key=lambda x: random.random() * (6 - level))
        return sorted_cities
