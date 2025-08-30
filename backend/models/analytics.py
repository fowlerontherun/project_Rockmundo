from __future__ import annotations

from typing import List
from pydantic import BaseModel


class MetricPoint(BaseModel):
    """Single point in a time series."""

    date: str
    value: int


class AggregatedMetrics(BaseModel):
    """Time-series metrics across several domains."""

    economy: List[MetricPoint]
    events: List[MetricPoint]
    skills: List[MetricPoint]


class AgeBucket(BaseModel):
    """Number of fans grouped by age range."""

    bucket: str
    fans: int


class RegionBucket(BaseModel):
    """Number of fans grouped by region."""

    region: str
    fans: int


class SpendBucket(BaseModel):
    """Number of fans grouped by spend level."""

    bucket: str
    fans: int


class FanSegmentSummary(BaseModel):
    """Summary counts for various fan segments."""

    age: List[AgeBucket]
    region: List[RegionBucket]
    spend: List[SpendBucket]
    engagement: List["EngagementBucket"]


class FanTrends(BaseModel):
    """Time-series engagement metrics for fans."""

    events: List[MetricPoint]
    purchases: List[MetricPoint]
    streams: List[MetricPoint]
    likes: List[MetricPoint]
    comments: List[MetricPoint]
    shares: List[MetricPoint]


class EngagementBucket(BaseModel):
    """Number of fans grouped by engagement level."""

    bucket: str
    fans: int


class EngagementTrends(BaseModel):
    """Time-series metrics for engagement signals."""

    likes: List[MetricPoint]
    comments: List[MetricPoint]
    shares: List[MetricPoint]
