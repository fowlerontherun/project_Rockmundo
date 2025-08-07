# Ticketing-related models
class Ticket:
    def __init__(self, band_id, venue_id, price, type, fan_segment, sold, resale_price=None):
        self.band_id = band_id
        self.venue_id = venue_id
        self.price = price
        self.type = type  # standard, vip, presale, etc.
        self.fan_segment = fan_segment  # genre fans, local fans, etc.
        self.sold = sold
        self.resale_price = resale_price

class BookingReputation:
    def __init__(self, band_id, score, cancellations):
        self.band_id = band_id
        self.score = score
        self.cancellations = cancellations

class TicketEvent:
    def __init__(self, ticket_id, event_type, description):
        self.ticket_id = ticket_id
        self.event_type = event_type  # overbooking, glitch, scalping issue
        self.description = description
