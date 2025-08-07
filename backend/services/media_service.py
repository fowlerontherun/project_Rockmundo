from datetime import datetime

news_storage = {}

def create_news_article(data):
    article = {
        "article_id": data["article_id"],
        "title": data["title"],
        "author": data.get("author", "System"),
        "content": data["content"],
        "category": data["category"],
        "karma_effect": data.get("karma_effect", 0),
        "published_at": str(datetime.utcnow())
    }
    news_storage[data["article_id"]] = article
    return {"status": "created", "article": article}

def get_recent_articles():
    sorted_articles = sorted(news_storage.values(), key=lambda x: x["published_at"], reverse=True)
    return {"articles": sorted_articles[:10]}

def get_news_article(article_id):
    article = news_storage.get(article_id)
    if not article:
        return {"error": "not found"}
    return {"article": article}