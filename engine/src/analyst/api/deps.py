"""Shared state for the API layer."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from analyst.executor import TaskRunResult


@dataclass
class ActiveRun:
    """Tracks an in-progress or recently completed task run."""

    run_id: str
    task_name: str
    status: str = "running"
    task: asyncio.Task | None = None
    result: TaskRunResult | None = None


# Global in-memory state — fine for single-user local app.
active_runs: dict[str, ActiveRun] = {}
