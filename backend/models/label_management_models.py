# Label & Management models

class Label:
    def __init__(self, name, genre_focus, max_roster, reputation, npc_owned=True):
        self.name = name
        self.genre_focus = genre_focus
        self.max_roster = max_roster
        self.reputation = reputation
        self.npc_owned = npc_owned

class ManagementContract:
    def __init__(self, manager_id, band_id, cut_percentage, perks, active=True):
        self.manager_id = manager_id
        self.band_id = band_id
        self.cut_percentage = cut_percentage
        self.perks = perks
        self.active = active

class LabelContract:
    def __init__(self, label_id, band_id, revenue_split, advance_payment, min_releases, active=True):
        self.label_id = label_id
        self.band_id = band_id
        self.revenue_split = revenue_split
        self.advance_payment = advance_payment
        self.min_releases = min_releases
        self.active = active
