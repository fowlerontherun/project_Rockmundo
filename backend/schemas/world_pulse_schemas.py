from pydantic import BaseModel

class TrendingGenresResponse(BaseModel):
    genres: list

class KarmaHeatmapResponse(BaseModel):
    heatmap: dict

class EventStreamResponse(BaseModel):
    events: list

class TopInfluencersResponse(BaseModel):
    influencers: list