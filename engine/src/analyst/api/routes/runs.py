"""Endpoints for browsing past task runs and results."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Query

from analyst.api.models import RunDetail, RunSummary
from analyst.core.cache import _get_connection

router = APIRouter()


def _parse_channels(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []


@router.get("", response_model=list[RunSummary])
def list_runs(limit: int = Query(default=30, ge=1, le=200)):
    """List recent task runs."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            """SELECT id, task_name, status, started_at, completed_at,
                      duration_seconds, channels_delivered, error_message, result_id
               FROM task_runs
               ORDER BY started_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [
            RunSummary(
                id=row["id"],
                task_name=row["task_name"],
                status=row["status"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                duration_seconds=row["duration_seconds"],
                channels_delivered=_parse_channels(row["channels_delivered"]),
                error_message=row["error_message"],
                result_id=row["result_id"],
            )
            for row in rows
        ]
    finally:
        conn.close()


@router.get("/{run_id}", response_model=RunDetail)
def get_run_detail(run_id: int):
    """Get full detail of a past run including analysis output."""
    conn = _get_connection()
    try:
        row = conn.execute(
            """SELECT tr.id, tr.task_name, tr.status, tr.started_at, tr.completed_at,
                      tr.duration_seconds, tr.channels_delivered, tr.error_message,
                      tr.result_id,
                      ar.analysis_text, ar.result_json
               FROM task_runs tr
               LEFT JOIN analysis_results ar ON tr.result_id = ar.id
               WHERE tr.id = ?""",
            (run_id,),
        ).fetchone()

        if not row:
            raise HTTPException(404, "Run nicht gefunden")

        structured = None
        if row["result_json"]:
            try:
                structured = json.loads(row["result_json"])
            except (json.JSONDecodeError, TypeError):
                pass

        return RunDetail(
            id=row["id"],
            task_name=row["task_name"],
            status=row["status"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            duration_seconds=row["duration_seconds"],
            channels_delivered=_parse_channels(row["channels_delivered"]),
            error_message=row["error_message"],
            result_id=row["result_id"],
            analysis_text=row["analysis_text"],
            structured_data=structured,
        )
    finally:
        conn.close()
