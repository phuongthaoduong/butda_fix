from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    query: str = Field(...)
    options: Optional[dict[str, Any]] = None


class SearchResult(BaseModel):
    id: str
    title: str
    url: str
    snippet: str
    publishedAt: datetime
    source: str
    relevanceScore: float


class Source(BaseModel):
    name: str
    url: str
    reliability: str
    type: str


class ResearchStatistics(BaseModel):
    totalResults: int
    processingTime: int
    searchTime: int
    summaryTime: int


class ResearchData(BaseModel):
    query: str
    summary: str
    results: list[SearchResult]
    sources: list[Source]
    statistics: ResearchStatistics
    cached: bool


class ErrorDetails(BaseModel):
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class ResearchResponse(BaseModel):
    success: bool
    data: Optional[ResearchData] = None
    error: Optional[ErrorDetails] = None

