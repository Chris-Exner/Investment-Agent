"""CLI entry point for the financial analyst engine."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime

import click

from analyst.core.cache import clear_expired_cache
from analyst.core.config import ensure_directories, list_task_configs, load_task_config


def _setup_logging(level: str = "INFO") -> None:
    """Configure logging for CLI usage."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


async def _run_task(task_name: str, dry_run: bool = False, output_json: bool = False) -> None:
    """Execute a single task with CLI presentation."""
    from analyst.executor import execute_task

    config = load_task_config(task_name)
    click.echo(f"Running task: {config.name} ({config.analysis_type})")
    click.echo(f"  Model: {config.llm.model}")
    click.echo(f"  Outputs: {', '.join(ch.type.value for ch in config.output_channels)}")
    click.echo("\nFetching data & running analysis...")

    result = await execute_task(task_name, dry_run=dry_run)

    click.echo(f"\nAnalysis complete ({result.duration_seconds:.1f}s)")
    click.echo(f"  Tokens: {result.tokens_input} in / {result.tokens_output} out")

    if result.status == "failed":
        raise click.ClickException(result.error_message or "Task failed")

    if output_json and result.structured_data:
        click.echo("\n" + json.dumps(result.structured_data, indent=2, ensure_ascii=False))
        return

    if dry_run:
        click.echo("\n--- DRY RUN: Analysis text ---")
        if result.analysis_text:
            sys.stdout.buffer.write(result.analysis_text.encode("utf-8"))
            sys.stdout.buffer.write(b"\n")
            sys.stdout.buffer.flush()
        click.echo("\n--- Skipping output delivery (dry run) ---")
    else:
        click.echo(f"\nDone! Delivered to: {', '.join(result.channels_delivered) or 'none'}")


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def main(verbose: bool) -> None:
    """Financial Analyst Engine - AI-powered market analysis."""
    _setup_logging("DEBUG" if verbose else "INFO")
    ensure_directories()


@main.command()
@click.argument("task_name")
@click.option("--dry-run", is_flag=True, help="Run analysis but skip output delivery")
@click.option("--json", "output_json", is_flag=True, help="Output structured result as JSON")
def run(task_name: str, dry_run: bool, output_json: bool) -> None:
    """Run a specific analysis task."""
    asyncio.run(_run_task(task_name, dry_run=dry_run, output_json=output_json))


@main.command("list")
def list_tasks() -> None:
    """List all available task configurations."""
    tasks = list_task_configs()
    if not tasks:
        click.echo("No task configurations found in config/tasks/")
        return

    click.echo("Available tasks:")
    for name in sorted(tasks):
        try:
            config = load_task_config(name)
            status = "[ON]" if config.schedule.enabled else "[OFF]"
            outputs = ", ".join(ch.type.value for ch in config.output_channels)
            click.echo(f"  {status} {name} ({config.analysis_type.value}) -> {outputs}")
            click.echo(f"    Schedule: {config.schedule.cron} ({config.schedule.timezone})")
        except Exception as e:
            click.echo(f"  [!] {name} (error: {e})")


@main.command("test-output")
@click.option("--channel", type=click.Choice(["telegram"]), default="telegram")
@click.option("--message", default="Test message from Financial Analyst Engine")
def test_output(channel: str, message: str) -> None:
    """Send a test message to verify output channel configuration."""

    async def _test():
        if channel == "telegram":
            from analyst.output.telegram import send_test_message

            success = await send_test_message(message)
            if success:
                click.echo("[OK] Telegram test message sent successfully")
            else:
                click.echo("[FAIL] Failed to send Telegram test message")
                sys.exit(1)

    asyncio.run(_test())


@main.command()
@click.option("--older-than", type=int, default=0, help="Clear cache entries older than N days")
def cache(older_than: int) -> None:
    """Manage the data cache."""
    cleared = clear_expired_cache()
    click.echo(f"Cleared {cleared} expired cache entries")


# ── Scheduler subgroup ──────────────────────────────────────────────


@main.group()
def scheduler() -> None:
    """Manage the automatic task scheduler."""
    pass


@scheduler.command("start")
def scheduler_start() -> None:
    """Start the scheduler (runs in foreground until Ctrl+C)."""
    from analyst.scheduler import run_scheduler

    run_scheduler()


@scheduler.command("status")
def scheduler_status() -> None:
    """Show task schedules and last run info."""
    from analyst.core.cache import _get_connection
    from analyst.scheduler import _parse_cron_fields

    from apscheduler.triggers.cron import CronTrigger

    tasks = list_task_configs()
    if not tasks:
        click.echo("No tasks configured.")
        return

    click.echo("=== Task Schedule Status ===\n")

    for name in sorted(tasks):
        try:
            config = load_task_config(name)
            status_flag = "[ON]" if config.schedule.enabled else "[OFF]"
            click.echo(f"{status_flag} {name}")
            click.echo(f"  Schedule: {config.schedule.cron} ({config.schedule.timezone})")
            click.echo(f"  Model:    {config.llm.model}")

            # Calculate next run time using APScheduler CronTrigger
            if config.schedule.enabled:
                try:
                    cron_fields = _parse_cron_fields(config.schedule.cron)
                    trigger = CronTrigger(**cron_fields, timezone=config.schedule.timezone)
                    next_run = trigger.get_next_fire_time(None, datetime.now())
                    click.echo(f"  Next run: {next_run.strftime('%Y-%m-%d %H:%M %Z')}")
                except Exception as e:
                    click.echo(f"  Next run: (error: {e})")

            # Show last run from database
            conn = _get_connection()
            try:
                row = conn.execute(
                    """SELECT status, started_at, duration_seconds, error_message
                       FROM task_runs WHERE task_name = ?
                       ORDER BY started_at DESC LIMIT 1""",
                    (name,),
                ).fetchone()
                if row:
                    run_status = "[OK]" if row["status"] == "success" else "[FAIL]"
                    duration = f"{row['duration_seconds']:.1f}s" if row["duration_seconds"] else "?"
                    click.echo(f"  Last run: {row['started_at']} {run_status} ({duration})")
                    if row["error_message"]:
                        click.echo(f"  Error:    {row['error_message'][:120]}")
                else:
                    click.echo("  Last run: never")
            finally:
                conn.close()

            click.echo()
        except Exception as e:
            click.echo(f"  [!] Error loading {name}: {e}\n")


@main.command()
@click.option("--port", default=8000, help="API server port")
@click.option("--host", default="127.0.0.1", help="Bind address")
def serve(port: int, host: str) -> None:
    """Start the dashboard API server."""
    import uvicorn

    from analyst.api.app import app

    click.echo(f"Starting API server at http://{host}:{port}")
    click.echo(f"API docs: http://{host}:{port}/docs")
    uvicorn.run(app, host=host, port=port, log_level="info")


@main.command("__main__")
def main_module() -> None:
    """Entry point for python -m analyst."""
    pass


if __name__ == "__main__":
    main()
