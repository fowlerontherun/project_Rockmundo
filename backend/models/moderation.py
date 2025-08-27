from datetime import datetime


class Report:
    def __init__(self, id, reporter_id, target_id, reason, status='pending', created_at=None, resolution=None):
        self.id = id
        self.reporter_id = reporter_id
        self.target_id = target_id
        self.reason = reason
        self.status = status
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.resolution = resolution

    def to_dict(self):
        return self.__dict__


class Sanction:
    def __init__(self, id, user_id, type, reason, issued_at=None, expires_at=None, active=True):
        self.id = id
        self.user_id = user_id
        self.type = type  # warning, mute, ban
        self.reason = reason
        self.issued_at = issued_at or datetime.utcnow().isoformat()
        self.expires_at = expires_at
        self.active = active

    def to_dict(self):
        return self.__dict__


class AuditLog:
    def __init__(self, id, action, details, timestamp=None):
        self.id = id
        self.action = action
        self.details = details
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
