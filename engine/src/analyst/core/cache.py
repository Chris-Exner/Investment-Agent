"""SQLite-backed cache layer with TTL support."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from analyst.core.config import DATA_DIR


class _DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def _get_db_path() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / "cache.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_get_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create cache tables if they don't exist."""
    conn = _get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS data_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                query_key TEXT NOT NULL,
                data_json TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                UNIQUE(source, query_key)
            );

            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                parameters_json TEXT NOT NULL,
                input_data_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                analysis_text TEXT NOT NULL,
                model_used TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                tokens_input INTEGER DEFAULT 0,
                tokens_output INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS task_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                duration_seconds REAL,
                channels_delivered TEXT,
                error_message TEXT,
                result_id INTEGER REFERENCES analysis_results(id)
            );

            CREATE INDEX IF NOT EXISTS idx_data_cache_lookup
                ON data_cache(source, query_key, expires_at);
            CREATE INDEX IF NOT EXISTS idx_analysis_results_task
                ON analysis_results(task_name, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_task_runs_task
                ON task_runs(task_name, started_at DESC);
        """)
        conn.commit()
    finally:
        conn.close()


def _make_key(source: str, params: dict) -> str:
    """Generate a deterministic cache key from source and parameters."""
    raw = json.dumps(params, sort_keys=True)
    return hashlib.sha256(f"{source}:{raw}".encode()).hexdigest()


def get_cached_data(source: str, params: dict) -> dict | None:
    """Retrieve cached data if it exists and hasn't expired."""
    conn = _get_connection()
    try:
        key = _make_key(source, params)
        now = datetime.now().isoformat()
        row = conn.execute(
            "SELECT data_json FROM data_cache WHERE source = ? AND query_key = ? AND expires_at > ?",
            (source, key, now),
        ).fetchone()
        if row:
            return json.loads(row["data_json"])
        return None
    finally:
        conn.close()


def set_cached_data(source: str, params: dict, data: dict, ttl_minutes: int = 60) -> None:
    """Store data in cache with a TTL."""
    conn = _get_connection()
    try:
        key = _make_key(source, params)
        now = datetime.now()
        expires = now + timedelta(minutes=ttl_minutes)
        conn.execute(
            """INSERT INTO data_cache (source, query_key, data_json, fetched_at, expires_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(source, query_key)
               DO UPDATE SET data_json = excluded.data_json,
                             fetched_at = excluded.fetched_at,
                             expires_at = excluded.expires_at""",
            (source, key, json.dumps(data), now.isoformat(), expires.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def save_analysis_result(
    task_name: str,
    analysis_type: str,
    parameters: dict,
    input_data: dict,
    result: dict,
    analysis_text: str,
    model_used: str,
    prompt_version: str,
    tokens_input: int = 0,
    tokens_output: int = 0,
) -> int:
    """Save an analysis result and return its ID."""
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO analysis_results
               (task_name, analysis_type, parameters_json, input_data_json,
                result_json, analysis_text, model_used, prompt_version,
                tokens_input, tokens_output)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task_name,
                analysis_type,
                json.dumps(parameters, cls=_DateTimeEncoder),
                json.dumps(input_data, cls=_DateTimeEncoder),
                json.dumps(result, cls=_DateTimeEncoder),
                analysis_text,
                model_used,
                prompt_version,
                tokens_input,
                tokens_output,
            ),
        )
        conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]
    finally:
        conn.close()


def log_task_run(task_name: str, status: str, started_at: datetime) -> int:
    """Log a task run start. Returns the run ID."""
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO task_runs (task_name, status, started_at) VALUES (?, ?, ?)",
            (task_name, status, started_at.isoformat()),
        )
        conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]
    finally:
        conn.close()


def update_task_run(
    run_id: int,
    status: str,
    completed_at: datetime | None = None,
    duration_seconds: float | None = None,
    channels_delivered: list[str] | None = None,
    error_message: str | None = None,
    result_id: int | None = None,
) -> None:
    """Update a task run with completion details."""
    conn = _get_connection()
    try:
        conn.execute(
            """UPDATE task_runs SET
                status = ?, completed_at = ?, duration_seconds = ?,
                channels_delivered = ?, error_message = ?, result_id = ?
               WHERE id = ?""",
            (
                status,
                completed_at.isoformat() if completed_at else None,
                duration_seconds,
                json.dumps(channels_delivered) if channels_delivered else None,
                error_message,
                result_id,
                run_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_latest_analysis_result(task_name: str) -> dict | None:
    """Retrieve the most recent analysis result for a given task.

    Returns dict with 'result' (parsed JSON) and 'date', or None if no result exists.
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            """SELECT result_json, created_at
               FROM analysis_results
               WHERE task_name = ?
               ORDER BY created_at DESC LIMIT 1""",
            (task_name,),
        ).fetchone()
        if row:
            return {
                "result": json.loads(row["result_json"]),
                "date": row["created_at"],
            }
        return None
    finally:
        conn.close()


def clear_expired_cache() -> int:
    """Delete expired cache entries. Returns number of rows deleted."""
    conn = _get_connection()
    try:
        now = datetime.now().isoformat()
        cursor = conn.execute("DELETE FROM data_cache WHERE expires_at <= ?", (now,))
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


# Initialize DB on first import
init_db()
