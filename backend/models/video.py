from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Video:
    """Represents an uploaded video and its statistics."""

    id: int
    owner_id: int
    title: str
    filename: str
    uploaded_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "processing"  # uploaded -> processing -> ready
    view_count: int = 0

    def to_dict(self) -> dict:
        """Serialize the video to a JSON friendly dict."""
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "title": self.title,
            "filename": self.filename,
            "uploaded_at": self.uploaded_at.isoformat(),
            "status": self.status,
            "view_count": self.view_count,
        }
