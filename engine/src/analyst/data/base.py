"""Abstract base for data source adapters."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import pandas as pd

from analyst.core.types import CompanyFinancials, StockData


@runtime_checkable
class DataSource(Protocol):
    """Protocol that all data source adapters must implement."""

    source_name: str

    async def get_stock_data(self, ticker: str, period: str = "1mo") -> StockData | None:
        """Fetch stock price data and basic info."""
        ...

    async def get_financials(self, ticker: str) -> CompanyFinancials | None:
        """Fetch company financial statements/metrics."""
        ...

    async def get_macro_indicator(self, series_id: str) -> pd.Series | None:
        """Fetch a macroeconomic indicator time series."""
        ...

    async def health_check(self) -> bool:
        """Check if the data source is available."""
        ...
