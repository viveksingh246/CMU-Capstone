"""Pydantic schemas for competitive intelligence data."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    OFFICIAL_WEBSITE = "official_website"
    OFFICIAL_DOCUMENTATION = "official_documentation"
    REGULATORY_FILING = "regulatory_filing"
    OFFICIAL_BLOG = "official_blog"
    PRESS_RELEASE = "press_release"
    NEWS = "news"
    RESEARCH_PAPER = "research_paper"
    GITHUB = "github"
    JOB_POSTING = "job_posting"
    OTHER = "other"


SOURCE_CREDIBILITY_SCORES: dict[SourceType, int] = {
    SourceType.OFFICIAL_DOCUMENTATION: 5,
    SourceType.REGULATORY_FILING: 5,
    SourceType.OFFICIAL_WEBSITE: 5,
    SourceType.PRESS_RELEASE: 4,
    SourceType.OFFICIAL_BLOG: 4,
    SourceType.NEWS: 4,
    SourceType.RESEARCH_PAPER: 4,
    SourceType.GITHUB: 3,
    SourceType.JOB_POSTING: 3,
    SourceType.OTHER: 1,
}


class ResearchRequest(BaseModel):
    industry: str
    companies: list[str] = Field(min_length=2, max_length=5)
    categories: list[str] = Field(min_length=1)
    date_range_days: int = Field(default=90, ge=1, le=365)
    geographic_market: str = "Global"
    report_depth: str = "standard"
    include_historical_comparison: bool = True
    generate_alerts: bool = True


class SearchResult(BaseModel):
    title: str
    url: str
    source_name: str
    snippet: str
    published_date: Optional[str] = None
    content: str = ""
    source_type: SourceType = SourceType.OTHER
    credibility_score: int = 1


class ExtractedFact(BaseModel):
    company: str
    category: str
    claim: str
    evidence: str
    source_url: str
    source_title: str
    published_date: Optional[str] = None
    source_type: SourceType = SourceType.OTHER
    confidence: float = Field(ge=0.0, le=1.0)
    is_company_claim: bool = False


class CategoryCompleteness(BaseModel):
    category: str
    status: str  # complete | incomplete | insufficient_evidence
    findings_count: int
    notes: str = ""


class SWOTPoint(BaseModel):
    point: str
    evidence_ids: list[int] = Field(default_factory=list)


class CompanySWOT(BaseModel):
    company: str
    strengths: list[SWOTPoint] = Field(default_factory=list)
    weaknesses: list[SWOTPoint] = Field(default_factory=list)
    opportunities: list[SWOTPoint] = Field(default_factory=list)
    threats: list[SWOTPoint] = Field(default_factory=list)


class CompanyScore(BaseModel):
    company: str
    product_breadth: float = Field(ge=1.0, le=5.0)
    feature_differentiation: float = Field(ge=1.0, le=5.0)
    pricing_attractiveness: float = Field(ge=1.0, le=5.0)
    ai_maturity: float = Field(ge=1.0, le=5.0)
    partnerships: float = Field(ge=1.0, le=5.0)
    innovation_momentum: float = Field(ge=1.0, le=5.0)
    hiring_momentum: float = Field(ge=1.0, le=5.0)
    rationale: dict[str, str] = Field(default_factory=dict)

    @property
    def overall_score(self) -> float:
        return round(
            self.product_breadth * 0.20
            + self.feature_differentiation * 0.20
            + self.pricing_attractiveness * 0.15
            + self.ai_maturity * 0.20
            + self.partnerships * 0.10
            + self.innovation_momentum * 0.10
            + self.hiring_momentum * 0.05,
            2,
        )


class Recommendation(BaseModel):
    recommendation: str
    evidence: str
    impact: str
    priority: str
    time_horizon: str


class Alert(BaseModel):
    company: str
    alert_type: str
    description: str
    source_url: Optional[str] = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    priority: str = "medium"


class ResearchPlanTask(BaseModel):
    category: str
    questions: list[str]
    preferred_sources: list[str]
    search_queries: list[str]
    evidence_required: str
    completion_criteria: str


class ResearchPlan(BaseModel):
    companies: list[str]
    categories: list[str]
    tasks: list[ResearchPlanTask]
    date_range: dict[str, str]


class HistoricalChange(BaseModel):
    company: str
    change_type: str
    description: str
    previous_value: Optional[str] = None
    current_value: Optional[str] = None


class CompetitiveReport(BaseModel):
    executive_summary: str
    market_overview: str
    company_profiles: dict[str, str]
    feature_matrix: dict[str, Any]
    pricing_comparison: dict[str, Any]
    strategic_moves: list[dict[str, Any]]
    hiring_signals: dict[str, Any]
    ai_analysis: dict[str, Any]
    swot: list[CompanySWOT]
    scorecard: list[CompanyScore]
    key_trends: list[str]
    recommendations: list[Recommendation]
    sources: list[dict[str, str]]
    historical_changes: list[HistoricalChange] = Field(default_factory=list)
    alerts: list[Alert] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
