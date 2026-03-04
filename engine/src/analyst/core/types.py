"""Core data types and Pydantic models for the financial analyst engine."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# --- Enums ---


class AnalysisType(str, Enum):
    MARKET_OVERVIEW = "market_overview"
    COMPANY_DEEP_DIVE = "company_deep_dive"
    INVESTMENT_THESIS_CHECK = "thesis_check"
    INDUSTRY_SCREENER = "industry_screener"


class OutputChannelType(str, Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    EXCEL = "excel"


class Outlook(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# --- Market Data Types ---


class PricePoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int = 0


class StockData(BaseModel):
    ticker: str
    name: str = ""
    price: float
    change_pct: float
    market_cap: float | None = None
    pe_ratio: float | None = None
    volume: int | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None
    history: list[PricePoint] = Field(default_factory=list)


class SectorPerformance(BaseModel):
    sector: str
    change_pct: float


class MacroIndicator(BaseModel):
    name: str
    series_id: str
    value: float
    previous_value: float | None = None
    unit: str = ""
    date: str = ""


class NewsItem(BaseModel):
    """A single news headline with metadata."""

    title: str
    source: str = ""  # e.g., "Reuters", "CNBC"
    published: datetime | None = None
    url: str = ""
    summary: str = ""  # first ~300 chars of description


class CompanyFinancials(BaseModel):
    ticker: str
    name: str = ""
    revenue: float | None = None
    revenue_growth: float | None = None
    net_income: float | None = None
    net_margin: float | None = None
    gross_margin: float | None = None
    operating_margin: float | None = None
    eps: float | None = None
    free_cash_flow: float | None = None
    total_debt: float | None = None
    total_cash: float | None = None
    pe_ratio: float | None = None
    ev_ebitda: float | None = None
    price_to_book: float | None = None
    dividend_yield: float | None = None
    beta: float | None = None


# --- Task Configuration Types ---


class ScheduleConfig(BaseModel):
    cron: str
    timezone: str = "Europe/Berlin"
    enabled: bool = True


class LLMConfig(BaseModel):
    model: str = "gpt-4.1"
    prompt_version: str = "v2"
    prompt_template: str = "market_overview"
    max_tokens: int = 8192
    temperature: float = 0.3


class OutputChannelConfig(BaseModel):
    type: OutputChannelType
    config: dict[str, Any] = Field(default_factory=dict)
    schedule_override: str | None = None


class CacheConfig(BaseModel):
    data_ttl_minutes: int = 60
    analysis_ttl_minutes: int = 1440


class TaskConfig(BaseModel):
    name: str
    description: str = ""
    analysis_type: AnalysisType
    schedule: ScheduleConfig
    parameters: dict[str, Any] = Field(default_factory=dict)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    output_channels: list[OutputChannelConfig] = Field(default_factory=list)
    cache: CacheConfig = Field(default_factory=CacheConfig)


# --- Analysis Result Types ---


class DeliveryResult(BaseModel):
    channel: OutputChannelType
    success: bool
    error: str | None = None


class AnalysisResult(BaseModel):
    task_name: str
    analysis_type: AnalysisType
    timestamp: datetime = Field(default_factory=datetime.now)
    input_data: dict[str, Any] = Field(default_factory=dict)
    analysis_text: str = ""
    structured_data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    deliveries: list[DeliveryResult] = Field(default_factory=list)


# --- Structured LLM Output Types ---


class MarketOverviewResult(BaseModel):
    """Structured output for market overview analysis."""

    summary: str = Field(
        description="3-4 sentence executive summary connecting market moves to key drivers"
    )
    us_markets: str = Field(
        description="US market analysis with drivers, sector rotation, notable movers"
    )
    european_markets: str = Field(
        description="European market analysis with ECB/political context"
    )
    asian_markets: str = Field(
        description="Asian market analysis with China/Japan/trade context"
    )
    commodities_forex: str = Field(
        description="Commodities and forex analysis with supply/demand drivers"
    )
    macro_context: str = Field(
        description="Macro interpretation: connect economic data (CPI, jobs, PMI) to policy "
        "expectations (Fed, ECB). Be SPECIFIC with numbers and causalities."
    )
    geopolitical_context: str = Field(
        default="",
        description="Geopolitical factors affecting markets: trade policy, sanctions, conflicts. "
        "Leave empty if no significant geopolitical drivers."
    )
    forward_outlook: str = Field(
        description="Forward-looking analysis for the next 1-2 weeks: key data releases, "
        "earnings, central bank meetings, and what to watch for"
    )
    key_events: list[str] = Field(
        default_factory=list,
        description="List of 3-7 specific market-moving events WITH concrete impact "
        "(e.g., 'CPI at 3.5% vs 3.3% expected, pushing 10Y yield to 4.35%')"
    )
    risk_factors: list[str] = Field(
        default_factory=list,
        description="Top 2-4 risk factors to monitor going forward"
    )
    overall_sentiment: str = Field(
        description="Overall market sentiment: bullish, bearish, or neutral"
    )
    sentiment_reasoning: str = Field(
        default="",
        description="1-2 sentence justification for the sentiment rating"
    )


class ThesisCheckAlert(BaseModel):
    """Alert for a single position in thesis check."""

    ticker: str
    company_name: str
    status: str = Field(description="'stable' or 'alert'")
    risk_level: RiskLevel = RiskLevel.LOW
    summary: str = Field(description="Brief status summary")
    triggers_detected: list[str] = Field(
        default_factory=list, description="Bear-case triggers that were detected"
    )
    recommendation: str = ""


class ThesisCheckResult(BaseModel):
    """Structured output from Claude for investment thesis check."""

    date: str
    overall_status: str = Field(description="'all_stable' or 'alerts_detected'")
    positions: list[ThesisCheckAlert] = Field(default_factory=list)
    market_context: str = ""


class CompanyDeepDiveResult(BaseModel):
    """Structured output from Claude for company deep dive."""

    ticker: str
    company_name: str
    executive_summary: str
    financial_health: str
    valuation_assessment: str
    competitive_position: str
    risks: list[str] = Field(default_factory=list)
    catalysts: list[str] = Field(default_factory=list)
    recommendation: str = Field(description="Buy, Hold, or Sell")
    confidence: float = Field(ge=0, le=1, description="Confidence score 0-1")
    target_price_reasoning: str = ""


class IndustryScreenerResult(BaseModel):
    """Structured output from Claude for industry screener."""

    industry_name: str
    trend_summary: str
    top_companies: list[dict[str, Any]] = Field(default_factory=list)
    key_metrics: dict[str, Any] = Field(default_factory=dict)
    outlook: Outlook
    confidence: float = Field(ge=0, le=1)
    investment_opportunities: list[str] = Field(default_factory=list)
