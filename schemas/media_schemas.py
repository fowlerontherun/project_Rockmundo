from pydantic import BaseModel
from typing import Optional

class NewsSubmissionSchema(BaseModel):
    article_id: str
    title: str
    author: Optional[str]
    content: str
    category: str  # e.g., news, gossip, tour, podcast
    karma_effect: Optional[int] = 0