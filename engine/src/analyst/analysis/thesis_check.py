"""Investment Thesis Check analysis module."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from analyst.analysis.base import BaseAnalyzer
from analyst.core.cache import get_latest_analysis_result
from analyst.core.types import (
    AnalysisResult,
    AnalysisType,
    CompanyFinancials,
    StockData,
    TaskConfig,
    ThesisCheckResult,
)
from analyst.llm.prompts import SYSTEM_PROMPT, load_prompt

# Map each thesis task to its sibling for cross-task continuity
_SIBLING_TASKS = {
    "investment_thesis_check": "investment_thesis_check_weekend",
    "investment_thesis_check_weekend": "investment_thesis_check",
}

logger = logging.getLogger(__name__)


class ThesisCheckAnalyzer(BaseAnalyzer):
    """Checks investment theses against current market data and news."""

    analysis_type = AnalysisType.INVESTMENT_THESIS_CHECK

    async def execute(self, config: TaskConfig) -> AnalysisResult:
        """Execute thesis check analysis."""
        params = config.parameters
        positions = params.get("positions", [])

        if not positions:
            raise ValueError("No positions configured in task parameters")

        tickers = [p["ticker"] for p in positions]

        # 1. Fetch all data in parallel
        logger.info("Fetching data for %d positions: %s", len(tickers), tickers)

        tasks: dict[str, Any] = {
            "stocks": self.data.get_multiple_stocks(tickers),
        }

        # Financials per ticker (parallel)
        for ticker in tickers:
            tasks[f"fin_{ticker}"] = self.data.get_financials(ticker)

        # News
        news_config = params.get("news")
        if news_config and news_config.get("enabled", True):
            tasks["news"] = self.data.fetch_news(
                max_items=news_config.get("max_items", 20),
                max_age_hours=news_config.get("max_age_hours", 24),
            )

        keys = list(tasks.keys())
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        data: dict[str, Any] = {}
        for key, result in zip(keys, results):
            if isinstance(result, Exception):
                logger.warning("Failed to fetch %s: %s", key, result)
                data[key] = [] if key in ("stocks", "news") else None
            else:
                data[key] = result

        # Build stock lookup
        stock_map: dict[str, StockData] = {}
        for stock in data.get("stocks", []):
            if isinstance(stock, StockData):
                stock_map[stock.ticker] = stock

        # Build financials lookup
        fin_map: dict[str, CompanyFinancials] = {}
        for ticker in tickers:
            fin = data.get(f"fin_{ticker}")
            if isinstance(fin, CompanyFinancials):
                fin_map[ticker] = fin

        news = data.get("news", [])
        logger.info(
            "Data fetched: %d stocks, %d financials, %d news items",
            len(stock_map), len(fin_map), len(news),
        )

        # 2. Load previous thesis check result for continuity
        previous_check = self._get_previous_check(config.name)
        if previous_check:
            logger.info("Previous check loaded from %s", previous_check["date"])
        else:
            logger.info("No previous thesis check found")

        # 3. Prepare template variables
        template_vars = self._prepare_template_vars(positions, stock_map, fin_map, news)
        template_vars["previous_check"] = previous_check

        # 4. Load and render prompt
        prompt_template = config.llm.prompt_template
        user_prompt = load_prompt(
            prompt_template,
            version=config.llm.prompt_version,
            variables=template_vars,
        )

        # 5. Call LLM for structured analysis
        result, metadata = await self.llm.analyze_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=ThesisCheckResult,
            max_tokens=config.llm.max_tokens,
            temperature=config.llm.temperature,
        )

        # 6. Build narrative
        analysis_text = self._format_narrative(result)

        # 7. Package result
        return AnalysisResult(
            task_name=config.name,
            analysis_type=AnalysisType.INVESTMENT_THESIS_CHECK,
            timestamp=datetime.now(),
            input_data=self._serialize_input(stock_map, fin_map, news, positions),
            analysis_text=analysis_text,
            structured_data=result.model_dump(),
            metadata={
                "model": metadata["model"],
                "input_tokens": metadata["input_tokens"],
                "output_tokens": metadata["output_tokens"],
                "prompt_version": config.llm.prompt_version,
                "positions_count": len(positions),
            },
        )

    def _get_previous_check(self, task_name: str) -> dict | None:
        """Load the most recent thesis check result for prompt continuity.

        Checks both the current task and its sibling (daily↔weekend) and
        returns whichever is more recent, so alerts carry over across variants.
        """
        own = get_latest_analysis_result(task_name)
        sibling_name = _SIBLING_TASKS.get(task_name)
        sibling = get_latest_analysis_result(sibling_name) if sibling_name else None

        # Pick the more recent one
        if own and sibling:
            latest = own if own["date"] >= sibling["date"] else sibling
        else:
            latest = own or sibling

        if not latest:
            return None

        # Return the structured result directly (it's already a dict matching ThesisCheckResult)
        result = latest["result"]
        result["date"] = latest["date"]
        return result

    def _prepare_template_vars(
        self,
        positions: list[dict[str, Any]],
        stock_map: dict[str, StockData],
        fin_map: dict[str, CompanyFinancials],
        news: list[Any],
    ) -> dict[str, Any]:
        """Merge config positions with live market data for template rendering."""
        enriched = []
        for pos in positions:
            ticker = pos["ticker"]
            stock = stock_map.get(ticker)
            fin = fin_map.get(ticker)

            entry: dict[str, Any] = {
                "ticker": ticker,
                "name": pos.get("name", ticker),
                "thesis": pos.get("thesis", ""),
                "bear_triggers": pos.get("bear_triggers", []),
            }

            if stock:
                entry["price"] = stock.price
                entry["change_pct"] = stock.change_pct
                entry["market_cap"] = stock.market_cap
                entry["pe_ratio"] = stock.pe_ratio
                entry["volume"] = stock.volume
                entry["fifty_two_week_high"] = stock.fifty_two_week_high
                entry["fifty_two_week_low"] = stock.fifty_two_week_low
            else:
                entry["price"] = None

            if fin:
                entry["financials"] = fin.model_dump()
            else:
                entry["financials"] = None

            enriched.append(entry)

        return {
            "positions": enriched,
            "news": [n.model_dump() for n in news],
        }

    def _serialize_input(
        self,
        stock_map: dict[str, StockData],
        fin_map: dict[str, CompanyFinancials],
        news: list[Any],
        positions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Serialize input data for cache storage."""
        return {
            "stocks": {k: v.model_dump() for k, v in stock_map.items()},
            "financials": {k: v.model_dump() for k, v in fin_map.items()},
            "news": [n.model_dump() if hasattr(n, "model_dump") else n for n in news],
            "positions_config": [
                {"ticker": p["ticker"], "name": p.get("name", "")}
                for p in positions
            ],
        }

    def _format_narrative(self, result: ThesisCheckResult) -> str:
        """Format the structured result into Telegram-friendly HTML."""
        # Header with overall status
        if result.overall_status == "all_stable":
            header = "\u2705 <b>Thesis Check: Alle Positionen stabil</b>"
        else:
            alert_count = sum(1 for p in result.positions if p.status == "alert")
            header = f"\u26a0\ufe0f <b>Thesis Check: {alert_count} Alert(s) erkannt</b>"

        sections = [f"\U0001f4cb {header}\n\n{result.date}"]

        # Each position
        for pos in result.positions:
            if pos.status == "alert":
                risk_emoji = {
                    "low": "\U0001f7e1",
                    "medium": "\U0001f7e0",
                    "high": "\U0001f534",
                    "critical": "\u2757",
                }.get(pos.risk_level.value, "\u26a0\ufe0f")
                status_line = f"{risk_emoji} <b>{pos.company_name}</b> ({pos.ticker}) — ALERT"
            else:
                status_line = f"\u2705 <b>{pos.company_name}</b> ({pos.ticker}) — Stabil"

            sections.append(f"\n\n{status_line}\n{pos.summary}")

            if pos.triggers_detected:
                triggers = "\n".join(f"  \u2022 {t}" for t in pos.triggers_detected)
                sections.append(f"\n<b>Erkannte Trigger:</b>\n{triggers}")

            if pos.recommendation:
                sections.append(f"\n<b>Empfehlung:</b> {pos.recommendation}")

        # Market context
        if result.market_context:
            sections.append(
                f"\n\n\U0001f310 <b>Marktkontext</b>\n{result.market_context}"
            )

        return "".join(sections)
