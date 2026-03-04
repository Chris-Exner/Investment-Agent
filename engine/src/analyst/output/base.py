"""Abstract base for output channel adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from analyst.core.types import AnalysisResult, DeliveryResult


class BaseOutputChannel(ABC):
    """Base class for all output channel adapters."""

    channel_name: str = ""

    @abstractmethod
    async def deliver(
        self, result: AnalysisResult, config: dict[str, Any]
    ) -> DeliveryResult:
        """Deliver analysis result through this channel."""
        ...
