"""Data aggregator that combines data from multiple sources."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from analyst.core.types import (
    CompanyFinancials,
    MacroIndicator,
    NewsItem,
    SectorPerformance,
    StockData,
)
from analyst.data.news_source import NewsSource
from analyst.data.yfinance_source import YFinanceSource

logger = logging.getLogger(__name__)


class DataAggregator:
    """Orchestrates data fetching from multiple sources with fallback."""

    def __init__(self, cache_ttl_minutes: int = 60):
        self.yfinance = YFinanceSource(cache_ttl_minutes=cache_ttl_minutes)
        self.news = NewsSource()
        # Future: self.fred = FredSource(...)
        # Future: self.fmp = FMPSource(...)

    async def get_stock_data(self, ticker: str, **kwargs: Any) -> StockData | None:
        """Fetch stock data, trying sources in priority order."""
        return await self.yfinance.get_stock_data(ticker, **kwargs)

    async def get_multiple_stocks(self, tickers: list[str]) -> list[StockData]:
        """Fetch stock data for multiple tickers."""
        return await self.yfinance.get_multiple_stocks(tickers)

    async def get_financials(self, ticker: str) -> CompanyFinancials | None:
        """Fetch company financials."""
        # Try yfinance first, future: fall back to FMP
        return await self.yfinance.get_financials(ticker)

    async def get_sector_performance(self) -> list[SectorPerformance]:
        """Fetch sector performance data."""
        return await self.yfinance.get_sector_performance()

    async def get_macro_indicators(
        self, indicators: list[dict[str, str]]
    ) -> list[MacroIndicator]:
        """Fetch macro indicators from configured sources.

        Args:
            indicators: List of dicts with 'series_id', 'name', and optionally 'source'.
        """
        results: list[MacroIndicator] = []

        for ind in indicators:
            series_id = ind["series_id"]
            name = ind.get("name", series_id)
            source = ind.get("source", "yfinance")

            if source == "yfinance":
                # Use yfinance for ticker-based indicators (VIX, yields via ETFs)
                stock = await self.yfinance.get_stock_data(series_id)
                if stock:
                    results.append(
                        MacroIndicator(
                            name=name,
                            series_id=series_id,
                            value=stock.price,
                            unit="",
                            date="",
                        )
                    )
            elif source == "fred":
                # Future: self.fred.get_macro_indicator(series_id)
                logger.warning(f"FRED source not yet implemented, skipping {series_id}")

        return results

    async def fetch_news(
        self,
        max_items: int = 25,
        max_age_hours: int = 24,
        feed_keys: list[str] | None = None,
    ) -> list[NewsItem]:
        """Fetch financial news from RSS feeds."""
        return await self.news.fetch_news(
            feed_keys=feed_keys,
            max_total=max_items,
            max_age_hours=max_age_hours,
        )

    async def fetch_market_overview_data(
        self,
        index_tickers: list[dict[str, str]],
        commodity_tickers: list[dict[str, str]] | None = None,
        forex_tickers: list[dict[str, str]] | None = None,
        macro_indicators: list[dict[str, str]] | None = None,
        include_sectors: bool = True,
        news_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Fetch all data needed for a market overview analysis.

        Returns a dict with keys: indices, sectors, commodities, forex, macro, news.
        """
        # Build parallel tasks
        tasks: dict[str, Any] = {}

        # Indices
        index_symbols = [i["ticker"] for i in index_tickers]
        tasks["indices"] = self.get_multiple_stocks(index_symbols)

        # Sectors
        if include_sectors:
            tasks["sectors"] = self.get_sector_performance()

        # Commodities
        if commodity_tickers:
            commodity_symbols = [c["ticker"] for c in commodity_tickers]
            tasks["commodities"] = self.get_multiple_stocks(commodity_symbols)

        # Forex
        if forex_tickers:
            forex_symbols = [f["ticker"] for f in forex_tickers]
            tasks["forex"] = self.get_multiple_stocks(forex_symbols)

        # Macro
        if macro_indicators:
            tasks["macro"] = self.get_macro_indicators(macro_indicators)

        # News (parallel with market data)
        if news_config and news_config.get("enabled", True):
            tasks["news"] = self.fetch_news(
                max_items=news_config.get("max_items", 25),
                max_age_hours=news_config.get("max_age_hours", 24),
            )

        # Execute all in parallel
        keys = list(tasks.keys())
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        data: dict[str, Any] = {}
        for key, result in zip(keys, results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to fetch {key}: {result}")
                data[key] = []
            else:
                data[key] = result

        # Map names back to index data
        if "indices" in data:
            index_name_map = {i["ticker"]: i.get("name", i["ticker"]) for i in index_tickers}
            for stock in data["indices"]:
                if stock.ticker in index_name_map and not stock.name:
                    stock.name = index_name_map[stock.ticker]

        # Ensure news key exists even if not requested
        if "news" not in data:
            data["news"] = []

        return data
