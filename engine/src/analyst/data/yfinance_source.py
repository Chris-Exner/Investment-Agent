"""Yahoo Finance data source adapter using yfinance."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import pandas as pd
import yfinance as yf

from analyst.core.cache import get_cached_data, set_cached_data
from analyst.core.exceptions import DataFetchError
from analyst.core.types import (
    CompanyFinancials,
    PricePoint,
    SectorPerformance,
    StockData,
)

logger = logging.getLogger(__name__)

# Semaphore to limit concurrent yfinance calls (it's not async-native)
_semaphore = asyncio.Semaphore(5)


class YFinanceSource:
    """Data source adapter for Yahoo Finance via yfinance."""

    source_name = "yfinance"

    def __init__(self, cache_ttl_minutes: int = 60):
        self.cache_ttl = cache_ttl_minutes

    def _fetch_ticker_sync(self, ticker: str) -> dict[str, Any]:
        """Synchronous fetch of ticker data (runs in thread pool)."""
        t = yf.Ticker(ticker)
        info = t.info or {}
        return info

    async def get_stock_data(
        self, ticker: str, period: str = "1mo", include_history: bool = False
    ) -> StockData | None:
        """Fetch stock data for a single ticker."""
        cache_params = {"ticker": ticker, "period": period, "type": "stock_data"}
        cached = get_cached_data(self.source_name, cache_params)
        if cached:
            logger.debug(f"Cache hit for {ticker} stock data")
            return StockData(**cached)

        try:
            async with _semaphore:
                info = await asyncio.to_thread(self._fetch_ticker_sync, ticker)

            price = info.get("regularMarketPrice") or info.get("currentPrice", 0)
            prev_close = info.get("regularMarketPreviousClose") or info.get(
                "previousClose", price
            )
            change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0

            history: list[PricePoint] = []
            if include_history:
                async with _semaphore:
                    hist_df = await asyncio.to_thread(
                        lambda: yf.Ticker(ticker).history(period=period)
                    )
                if hist_df is not None and not hist_df.empty:
                    for date, row in hist_df.iterrows():
                        history.append(
                            PricePoint(
                                date=str(date.date()),
                                open=round(row.get("Open", 0), 2),
                                high=round(row.get("High", 0), 2),
                                low=round(row.get("Low", 0), 2),
                                close=round(row.get("Close", 0), 2),
                                volume=int(row.get("Volume", 0)),
                            )
                        )

            stock = StockData(
                ticker=ticker,
                name=info.get("shortName") or info.get("longName", ticker),
                price=round(price, 2),
                change_pct=round(change_pct, 2),
                market_cap=info.get("marketCap"),
                pe_ratio=info.get("trailingPE"),
                volume=info.get("regularMarketVolume") or info.get("volume"),
                fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
                fifty_two_week_low=info.get("fiftyTwoWeekLow"),
                history=history,
            )

            set_cached_data(self.source_name, cache_params, stock.model_dump(), self.cache_ttl)
            return stock

        except Exception as e:
            logger.error(f"Failed to fetch stock data for {ticker}: {e}")
            raise DataFetchError(self.source_name, f"Ticker {ticker}: {e}") from e

    async def get_financials(self, ticker: str) -> CompanyFinancials | None:
        """Fetch company financial metrics."""
        cache_params = {"ticker": ticker, "type": "financials"}
        cached = get_cached_data(self.source_name, cache_params)
        if cached:
            return CompanyFinancials(**cached)

        try:
            async with _semaphore:
                info = await asyncio.to_thread(self._fetch_ticker_sync, ticker)

            financials = CompanyFinancials(
                ticker=ticker,
                name=info.get("shortName") or info.get("longName", ticker),
                revenue=info.get("totalRevenue"),
                revenue_growth=info.get("revenueGrowth"),
                net_income=info.get("netIncomeToCommon"),
                net_margin=info.get("profitMargins"),
                gross_margin=info.get("grossMargins"),
                operating_margin=info.get("operatingMargins"),
                eps=info.get("trailingEps"),
                free_cash_flow=info.get("freeCashflow"),
                total_debt=info.get("totalDebt"),
                total_cash=info.get("totalCash"),
                pe_ratio=info.get("trailingPE"),
                ev_ebitda=info.get("enterpriseToEbitda"),
                price_to_book=info.get("priceToBook"),
                dividend_yield=info.get("dividendYield"),
                beta=info.get("beta"),
            )

            set_cached_data(
                self.source_name, cache_params, financials.model_dump(), self.cache_ttl
            )
            return financials

        except Exception as e:
            logger.error(f"Failed to fetch financials for {ticker}: {e}")
            return None

    async def get_multiple_stocks(self, tickers: list[str]) -> list[StockData]:
        """Fetch stock data for multiple tickers in parallel."""
        tasks = [self.get_stock_data(t) for t in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        stocks: list[StockData] = []
        for ticker, result in zip(tickers, results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to fetch {ticker}: {result}")
            elif result is not None:
                stocks.append(result)
        return stocks

    async def get_sector_performance(self) -> list[SectorPerformance]:
        """Fetch S&P 500 sector ETF performance as a proxy for sector performance."""
        sector_etfs = {
            "XLK": "Technology",
            "XLV": "Healthcare",
            "XLF": "Financials",
            "XLE": "Energy",
            "XLI": "Industrials",
            "XLP": "Consumer Staples",
            "XLY": "Consumer Discretionary",
            "XLU": "Utilities",
            "XLRE": "Real Estate",
            "XLB": "Materials",
            "XLC": "Communication Services",
        }

        stocks = await self.get_multiple_stocks(list(sector_etfs.keys()))
        sectors: list[SectorPerformance] = []
        for stock in stocks:
            sector_name = sector_etfs.get(stock.ticker, stock.ticker)
            sectors.append(SectorPerformance(sector=sector_name, change_pct=stock.change_pct))

        sectors.sort(key=lambda s: s.change_pct, reverse=True)
        return sectors

    async def get_macro_indicator(self, series_id: str) -> pd.Series | None:
        """yfinance doesn't provide macro indicators - returns None."""
        return None

    async def health_check(self) -> bool:
        """Check if yfinance is responsive."""
        try:
            async with _semaphore:
                info = await asyncio.to_thread(lambda: yf.Ticker("AAPL").info)
            return bool(info and info.get("regularMarketPrice"))
        except Exception:
            return False
