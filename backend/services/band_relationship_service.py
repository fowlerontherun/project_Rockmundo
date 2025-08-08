
from models.band_relationship import BandRelationship
from datetime import datetime

class BandRelationshipService:
    def __init__(self, db):
        self.db = db

    def create_relationship(self, band_a_id, band_b_id, relationship_type):
        rel = BandRelationship(
            id=None,
            band_a_id=band_a_id,
            band_b_id=band_b_id,
            type=relationship_type
        )
        self.db.insert_band_relationship(rel)
        return rel.to_dict()

    def get_relationships(self, band_id, relationship_type=None):
        return self.db.get_band_relationships(band_id, relationship_type)

    def end_relationship(self, band_a_id, band_b_id):
        self.db.deactivate_relationship(band_a_id, band_b_id)
        return {"status": "relationship ended"}
