"""Task listing and manual run trigger endpoints."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from analyst.api.deps import ActiveRun, active_runs
from analyst.api.models import TaskInfo, TaskRunStatus, TaskRunTrigger
from analyst.core.config import list_task_configs, load_task_config

router = APIRouter()


@router.get("", response_model=list[TaskInfo])
def list_tasks():
    """List all available tasks with config summaries."""
    result = []
    for name in sorted(list_task_configs()):
        try:
            config = load_task_config(name)
            result.append(TaskInfo(
                name=name,
                description=config.description,
                analysis_type=config.analysis_type.value,
                schedule_cron=config.schedule.cron,
                schedule_enabled=config.schedule.enabled,
                has_positions="positions" in config.parameters,
            ))
        except Exception:
            continue
    return result


@router.post("/{task_name}/run", response_model=TaskRunStatus)
async def trigger_run(task_name: str, body: TaskRunTrigger):
    """Trigger a task run asynchronously."""
    if task_name not in list_task_configs():
        raise HTTPException(404, f"Task '{task_name}' nicht gefunden")

    # Prevent duplicate runs of the same task
    for run in active_runs.values():
        if run.task_name == task_name and run.status == "running":
            raise HTTPException(409, f"Task '{task_name}' laeuft bereits")

    run_id = str(uuid.uuid4())

    async def _execute():
        from analyst.executor import execute_task

        try:
            result = await execute_task(task_name, dry_run=body.dry_run)
            active_runs[run_id].status = result.status
            active_runs[run_id].result = result
        except Exception as exc:
            active_runs[run_id].status = "failed"
            # Store a minimal result with the error
            from analyst.executor import TaskRunResult

            active_runs[run_id].result = TaskRunResult(
                task_name=task_name,
                status="failed",
                error_message=str(exc),
            )

    task = asyncio.create_task(_execute())
    active_runs[run_id] = ActiveRun(
        run_id=run_id,
        task_name=task_name,
        status="running",
        task=task,
    )

    return TaskRunStatus(
        run_id=run_id,
        task_name=task_name,
        status="running",
        started_at=datetime.now().isoformat(),
    )


@router.get("/{task_name}/run/{run_id}", response_model=TaskRunStatus)
def get_run_status(task_name: str, run_id: str):
    """Poll the status of an active run."""
    run = active_runs.get(run_id)
    if not run or run.task_name != task_name:
        raise HTTPException(404, "Run nicht gefunden")

    resp = TaskRunStatus(
        run_id=run.run_id,
        task_name=run.task_name,
        status=run.status,
    )

    if run.result:
        resp.duration_seconds = run.result.duration_seconds
        resp.error_message = run.result.error_message
        resp.tokens_input = run.result.tokens_input
        resp.tokens_output = run.result.tokens_output
        resp.analysis_text = run.result.analysis_text

    return resp
