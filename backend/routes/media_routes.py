from fastapi import APIRouter
from services.media_service import *
from schemas.media_schemas import NewsSubmissionSchema

router = APIRouter()

@router.post("/media/submit_news")
def submit_news(payload: NewsSubmissionSchema):
    return create_news_article(payload.dict())

@router.get("/media/latest")
def get_latest_news():
    return get_recent_articles()

@router.get("/media/{article_id}")
def get_article(article_id: str):
    return get_news_article(article_id)