"""Core task execution logic, shared by CLI and scheduler."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime

from analyst.core.cache import log_task_run, save_analysis_result, update_task_run
from analyst.core.config import load_task_config
from analyst.core.types import AnalysisType, OutputChannelType

logger = logging.getLogger(__name__)


@dataclass
class TaskRunResult:
    """Result of a task execution."""

    task_name: str
    status: str  # "success" | "failed"
    duration_seconds: float = 0.0
    channels_delivered: list[str] = field(default_factory=list)
    error_message: str | None = None
    tokens_input: int = 0
    tokens_output: int = 0
    analysis_text: str | None = None
    structured_data: dict | None = None


def _get_analyzer(analysis_type: AnalysisType, model: str):
    """Create the appropriate analyzer instance."""
    from analyst.data.aggregator import DataAggregator
    from analyst.llm.client import LLMClient

    llm = LLMClient(model=model)
    data = DataAggregator()

    if analysis_type == AnalysisType.MARKET_OVERVIEW:
        from analyst.analysis.market_overview import MarketOverviewAnalyzer

        return MarketOverviewAnalyzer(llm_client=llm, data_aggregator=data)
    elif analysis_type == AnalysisType.INVESTMENT_THESIS_CHECK:
        from analyst.analysis.thesis_check import ThesisCheckAnalyzer

        return ThesisCheckAnalyzer(llm_client=llm, data_aggregator=data)
    else:
        raise ValueError(f"Analysis type '{analysis_type}' not yet implemented")


def _get_output_channel(channel_type: OutputChannelType):
    """Create the appropriate output channel instance."""
    if channel_type == OutputChannelType.TELEGRAM:
        from analyst.output.telegram import TelegramOutput

        return TelegramOutput()
    else:
        raise ValueError(f"Output channel '{channel_type}' not yet implemented")


async def execute_task(task_name: str, dry_run: bool = False) -> TaskRunResult:
    """Execute a single task end-to-end.

    Loads config, runs analysis, delivers to output channels, logs to cache.
    Returns TaskRunResult (never raises — errors are captured in result.status).
    """
    config = load_task_config(task_name)
    logger.info("Executing task: %s (%s, model=%s)", config.name, config.analysis_type, config.llm.model)

    started_at = datetime.now()
    run_id = log_task_run(task_name, "running", started_at)

    try:
        # Run the analysis
        analyzer = _get_analyzer(config.analysis_type, config.llm.model)
        result = await analyzer.execute(config)

        elapsed = time.time() - started_at.timestamp()
        tokens_in = result.metadata.get("input_tokens", 0)
        tokens_out = result.metadata.get("output_tokens", 0)

        logger.info(
            "Analysis complete for %s (%.1fs, %d/%d tokens)",
            task_name, elapsed, tokens_in, tokens_out,
        )

        # Persist result
        result_id = save_analysis_result(
            task_name=result.task_name,
            analysis_type=result.analysis_type.value,
            parameters=config.parameters,
            input_data=result.input_data,
            result=result.structured_data,
            analysis_text=result.analysis_text,
            model_used=result.metadata.get("model", ""),
            prompt_version=result.metadata.get("prompt_version", ""),
            tokens_input=tokens_in,
            tokens_output=tokens_out,
        )

        # Deliver to output channels
        channels_delivered: list[str] = []
        if not dry_run:
            for ch_config in config.output_channels:
                try:
                    channel = _get_output_channel(ch_config.type)
                    delivery = await channel.deliver(result, ch_config.config)
                    if delivery.success:
                        channels_delivered.append(ch_config.type.value)
                        logger.info("Delivered %s -> %s", task_name, ch_config.type.value)
                    else:
                        logger.error(
                            "Delivery failed %s -> %s: %s",
                            task_name, ch_config.type.value, delivery.error,
                        )
                except Exception as e:
                    logger.error(
                        "Delivery error %s -> %s: %s",
                        task_name, ch_config.type.value, e,
                    )

        # Update task run record
        update_task_run(
            run_id,
            status="success",
            completed_at=datetime.now(),
            duration_seconds=elapsed,
            channels_delivered=channels_delivered,
            result_id=result_id,
        )

        return TaskRunResult(
            task_name=task_name,
            status="success",
            duration_seconds=elapsed,
            channels_delivered=channels_delivered,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            analysis_text=result.analysis_text,
            structured_data=result.structured_data,
        )

    except Exception as e:
        elapsed = time.time() - started_at.timestamp()
        update_task_run(
            run_id,
            status="failed",
            completed_at=datetime.now(),
            duration_seconds=elapsed,
            error_message=str(e),
        )
        logger.error("Task %s failed after %.1fs: %s", task_name, elapsed, e)

        return TaskRunResult(
            task_name=task_name,
            status="failed",
            duration_seconds=elapsed,
            error_message=str(e),
        )
