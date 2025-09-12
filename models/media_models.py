from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NewsArticle(BaseModel):
    article_id: str
    title: str
    author: Optional[str]
    content: str
    category: str  # e.g., news, gossip, tour, podcast
    published_at: datetime
    karma_effect: Optional[int] = 0