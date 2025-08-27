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
