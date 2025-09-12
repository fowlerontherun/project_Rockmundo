
from datetime import datetime

class Merchandise:
    def __init__(self, id, band_id, item_name, price, stock, total_sold=0, created_at=None):
        self.id = id
        self.band_id = band_id
        self.item_name = item_name
        self.price = price
        self.stock = stock
        self.total_sold = total_sold
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
