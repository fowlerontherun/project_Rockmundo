from pydantic import BaseModel

class TrendingGenresResponse(BaseModel):
    genres: list  # each item: {"genre_id": int, "subgenre_id": int | None, "count": int}

class KarmaHeatmapResponse(BaseModel):
    heatmap: dict

class EventStreamResponse(BaseModel):
    events: list

class TopInfluencersResponse(BaseModel):
    influencers: list