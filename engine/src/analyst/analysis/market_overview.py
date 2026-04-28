"""Market Overview analysis module."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from analyst.analysis.base import BaseAnalyzer
from analyst.core.types import (
    AnalysisResult,
    AnalysisType,
    MarketOverviewResult,
    TaskConfig,
)
from analyst.llm.prompts import SYSTEM_PROMPT, load_prompt

logger = logging.getLogger(__name__)


class MarketOverviewAnalyzer(BaseAnalyzer):
    """Produces a daily/weekly market overview analysis."""

    analysis_type = AnalysisType.MARKET_OVERVIEW

    async def execute(self, config: TaskConfig) -> AnalysisResult:
        """Execute market overview analysis."""
        params = config.parameters

        # 1. Fetch all market data + news in parallel
        logger.info("Fetching market overview data + news...")
        market_data = await self.data.fetch_market_overview_data(
            index_tickers=params.get("indices", []),
            commodity_tickers=params.get("commodities"),
            forex_tickers=params.get("forex"),
            macro_indicators=params.get("macro_indicators"),
            include_sectors=params.get("sectors", True),
            news_config=params.get("news"),
        )

        news_count = len(market_data.get("news", []))
        logger.info(f"Data fetched: {news_count} news items included")

        # 2. Prepare template variables
        template_vars = self._prepare_template_vars(market_data)

        # 3. Load and render prompt (use prompt_template from config)
        prompt_template = config.llm.prompt_template
        user_prompt = load_prompt(
            prompt_template,
            version=config.llm.prompt_version,
            variables=template_vars,
        )

        # 4. Call GPT for structured analysis
        result, metadata = await self.llm.analyze_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=MarketOverviewResult,
            max_output_tokens=config.llm.max_output_tokens,
            reasoning_effort=config.llm.reasoning_effort,
        )

        # 5. Build the narrative text from structured result
        analysis_text = self._format_narrative(result)

        # 6. Package everything into AnalysisResult
        return AnalysisResult(
            task_name=config.name,
            analysis_type=AnalysisType.MARKET_OVERVIEW,
            timestamp=datetime.now(),
            input_data=self._serialize_input(market_data),
            analysis_text=analysis_text,
            structured_data=result.model_dump(),
            metadata={
                "model": metadata["model"],
                "input_tokens": metadata["input_tokens"],
                "output_tokens": metadata["output_tokens"],
                "prompt_version": config.llm.prompt_version,
            },
        )

    def _prepare_template_vars(self, market_data: dict[str, Any]) -> dict[str, Any]:
        """Convert market data to template-friendly format."""
        return {
            "indices": [s.model_dump() for s in market_data.get("indices", [])],
            "sectors": [s.model_dump() for s in market_data.get("sectors", [])],
            "commodities": [s.model_dump() for s in market_data.get("commodities", [])],
            "forex": [s.model_dump() for s in market_data.get("forex", [])],
            "macro": [m.model_dump() for m in market_data.get("macro", [])],
            "news": [n.model_dump() for n in market_data.get("news", [])],
        }

    def _serialize_input(self, market_data: dict[str, Any]) -> dict[str, Any]:
        """Serialize market data for storage (Pydantic models → dicts)."""
        result: dict[str, Any] = {}
        for key, value in market_data.items():
            if isinstance(value, list):
                result[key] = [
                    item.model_dump() if hasattr(item, "model_dump") else item for item in value
                ]
            else:
                result[key] = value
        return result

    def _format_narrative(self, result: MarketOverviewResult) -> str:
        """Format the structured result into a readable narrative."""
        sections = [
            f"\U0001f4ca <b>Marktueberblick</b>\n\n{result.summary}",
            f"\n\n\U0001f1fa\U0001f1f8 <b>US-Maerkte</b>\n{result.us_markets}",
            f"\n\n\U0001f1ea\U0001f1fa <b>Europaeische Maerkte</b>\n{result.european_markets}",
            f"\n\n\U0001f30f <b>Asiatische Maerkte</b>\n{result.asian_markets}",
            f"\n\n\U0001f6e2\ufe0f <b>Rohstoffe & Devisen</b>\n{result.commodities_forex}",
            f"\n\n\U0001f4c8 <b>Makro-Kontext</b>\n{result.macro_context}",
        ]

        if result.geopolitical_context:
            sections.append(
                f"\n\n\U0001f310 <b>Geopolitik</b>\n{result.geopolitical_context}"
            )

        sections.append(f"\n\n\U0001f52e <b>Ausblick</b>\n{result.forward_outlook}")

        if result.key_events:
            events = "\n".join(f"\u2022 {e}" for e in result.key_events)
            sections.append(f"\n\n\U0001f511 <b>Key Events</b>\n{events}")

        if result.risk_factors:
            risks = "\n".join(f"\u26a0\ufe0f {r}" for r in result.risk_factors)
            sections.append(f"\n\n<b>Risikofaktoren</b>\n{risks}")

        sentiment_emoji = {"bullish": "\U0001f7e2", "bearish": "\U0001f534", "neutral": "\U0001f7e1"}
        emoji = sentiment_emoji.get(result.overall_sentiment.lower(), "\u26aa")
        sections.append(f"\n\n{emoji} <b>Sentiment</b>: {result.overall_sentiment.upper()}")

        if result.sentiment_reasoning:
            sections.append(f"\n{result.sentiment_reasoning}")

        return "".join(sections)
