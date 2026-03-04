"""Abstract base for analysis modules."""

from __future__ import annotations

from abc import ABC, abstractmethod

from analyst.core.types import AnalysisResult, TaskConfig
from analyst.data.aggregator import DataAggregator
from analyst.llm.client import LLMClient


class BaseAnalyzer(ABC):
    """Base class for all analysis modules."""

    analysis_type: str = ""

    def __init__(self, llm_client: LLMClient, data_aggregator: DataAggregator):
        self.llm = llm_client
        self.data = data_aggregator

    @abstractmethod
    async def execute(self, config: TaskConfig) -> AnalysisResult:
        """Execute the analysis and return results."""
        ...
