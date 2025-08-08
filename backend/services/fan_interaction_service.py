
from models.fan_interaction import FanInteraction

class FanInteractionService:
    def __init__(self, db):
        self.db = db

    def record_interaction(self, band_id, fan_id, interaction_type, content):
        interaction = FanInteraction(
            id=None,
            band_id=band_id,
            fan_id=fan_id,
            interaction_type=interaction_type,
            content=content
        )
        self.db.insert_fan_interaction(interaction)
        return interaction.to_dict()

    def get_band_interactions(self, band_id, interaction_type=None):
        return self.db.get_interactions_by_band(band_id, interaction_type)

    def get_petition_summary(self):
        return self.db.aggregate_petitions_by_city()
