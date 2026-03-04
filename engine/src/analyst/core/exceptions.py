"""Custom exception hierarchy for the financial analyst engine."""


class AnalystError(Exception):
    """Base exception for all analyst errors."""


class DataFetchError(AnalystError):
    """Error fetching data from an external source."""

    def __init__(self, source: str, detail: str = ""):
        self.source = source
        self.detail = detail
        super().__init__(f"Data fetch error from {source}: {detail}")


class LLMError(AnalystError):
    """Error communicating with the LLM API."""


class OutputDeliveryError(AnalystError):
    """Error delivering analysis to an output channel."""

    def __init__(self, channel: str, detail: str = ""):
        self.channel = channel
        self.detail = detail
        super().__init__(f"Output delivery error for {channel}: {detail}")


class ConfigError(AnalystError):
    """Error in configuration loading or validation."""


class CacheError(AnalystError):
    """Error in cache operations."""
