"""Cron-based task scheduler using APScheduler."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from analyst.core.cache import _get_connection
from analyst.core.config import ensure_directories, list_task_configs, load_task_config
from analyst.executor import execute_task

logger = logging.getLogger(__name__)


def _convert_cron_dow(field: str) -> str:
    """Convert day_of_week from standard cron (0=Sun) to APScheduler (0=Mon).

    Standard cron: 0/7=Sun, 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri, 6=Sat
    APScheduler:   0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun

    Handles: single numbers, ranges (1-5), comma lists (0,6), wildcards (*),
    and named days (mon, tue — passed through unchanged).
    """
    if field == "*":
        return field

    # If the field contains letters, it's using named days — pass through
    if any(c.isalpha() for c in field):
        return field

    def _convert_single(val: str) -> str:
        n = int(val)
        return str((n - 1) % 7)

    # Handle comma-separated values: "0,6" -> "6,5"
    parts = field.split(",")
    converted = []
    for part in parts:
        if "-" in part:
            # Range: "1-5" -> "0-4"
            start, end = part.split("-", 1)
            converted.append(f"{_convert_single(start)}-{_convert_single(end)}")
        else:
            converted.append(_convert_single(part))
    return ",".join(converted)


def _parse_cron_fields(cron_expr: str) -> dict[str, str]:
    """Parse a standard 5-field cron expression into APScheduler CronTrigger kwargs.

    Format: minute hour day month day_of_week
    Example: "0 22 * * 1-5" -> Mon-Fri at 22:00

    Note: Converts day_of_week from standard cron (0=Sun) to APScheduler (0=Mon).
    """
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Expected 5-field cron expression, got {len(parts)} fields: {cron_expr!r}")
    return {
        "minute": parts[0],
        "hour": parts[1],
        "day": parts[2],
        "month": parts[3],
        "day_of_week": _convert_cron_dow(parts[4]),
    }


async def _run_scheduled_task(task_name: str) -> None:
    """Wrapper called by APScheduler for each scheduled task execution."""
    logger.info("=== Scheduler firing task: %s ===", task_name)
    try:
        result = await execute_task(task_name)
        if result.status == "success":
            channels = ", ".join(result.channels_delivered) if result.channels_delivered else "none"
            logger.info(
                "Task %s completed: %.1fs, %d/%d tokens, delivered to: %s",
                task_name,
                result.duration_seconds,
                result.tokens_input,
                result.tokens_output,
                channels,
            )
        else:
            logger.error("Task %s FAILED: %s", task_name, result.error_message)
    except Exception:
        logger.exception("Unexpected error in scheduled task %s", task_name)


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the scheduler with all enabled tasks from config/tasks/."""
    scheduler = AsyncIOScheduler(
        job_defaults={
            "coalesce": True,             # If multiple misfires, run only once
            "max_instances": 1,           # Don't overlap runs of the same task
            "misfire_grace_time": 3600,   # Allow up to 1h late execution (e.g. after sleep)
        }
    )

    task_names = list_task_configs()
    loaded = 0
    skipped = 0

    for name in task_names:
        try:
            config = load_task_config(name)

            if not config.schedule.enabled:
                logger.info("Skipping disabled task: %s", name)
                skipped += 1
                continue

            cron_fields = _parse_cron_fields(config.schedule.cron)
            trigger = CronTrigger(**cron_fields, timezone=config.schedule.timezone)

            scheduler.add_job(
                _run_scheduled_task,
                trigger=trigger,
                args=[name],
                id=name,
                name=config.name,
                replace_existing=True,
            )

            next_run = trigger.get_next_fire_time(None, datetime.now())
            logger.info(
                "Scheduled: %s | cron: %s | tz: %s | next: %s",
                name, config.schedule.cron, config.schedule.timezone, next_run,
            )
            loaded += 1

        except Exception:
            logger.exception("Failed to load task config: %s", name)

    logger.info("Scheduler configured: %d tasks loaded, %d skipped", loaded, skipped)
    return scheduler


async def _check_catchup_tasks() -> None:
    """Check if any tasks were due today but haven't run yet, and execute them immediately.

    For each enabled task, checks if the cron schedule had a fire time today that has
    already passed. If so, queries task_runs to see if a successful run exists after
    that fire time. If not, runs the task immediately as a catch-up.
    """
    task_names = list_task_configs()
    catchup_count = 0

    for name in task_names:
        try:
            config = load_task_config(name)
            if not config.schedule.enabled:
                continue

            # Use the task's timezone for aware datetime comparisons
            tz = ZoneInfo(config.schedule.timezone)
            now = datetime.now(tz)
            start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # Build a CronTrigger and check: was there a fire time today that's already past?
            cron_fields = _parse_cron_fields(config.schedule.cron)
            trigger = CronTrigger(**cron_fields, timezone=config.schedule.timezone)
            scheduled_today = trigger.get_next_fire_time(None, start_of_today)

            if scheduled_today is None or scheduled_today >= now:
                # No fire time today yet, or it's still in the future — nothing to catch up
                continue

            # There was a fire time today that's already past. Check if it ran successfully.
            scheduled_today_str = scheduled_today.strftime("%Y-%m-%d %H:%M:%S")
            conn = _get_connection()
            try:
                row = conn.execute(
                    """SELECT 1 FROM task_runs
                       WHERE task_name = ? AND status = 'success' AND started_at > ?
                       LIMIT 1""",
                    (name, scheduled_today_str),
                ).fetchone()
            finally:
                conn.close()

            if row:
                logger.info("Catch-up: %s already ran after %s — skipping", name, scheduled_today_str)
                continue

            # Task was due today but hasn't run → catch up now
            logger.info(
                "Catch-up: %s was due at %s but hasn't run — executing now",
                name, scheduled_today_str,
            )
            print(f"  ⚡ Catching up: {name} (was due {scheduled_today_str})", flush=True)
            await _run_scheduled_task(name)
            catchup_count += 1

        except Exception:
            logger.exception("Catch-up check failed for task: %s", name)

    if catchup_count > 0:
        print(f"\n  Caught up {catchup_count} missed task(s).\n", flush=True)


async def _async_main() -> None:
    """Async entry point for the scheduler."""
    scheduler = create_scheduler()

    # Start scheduler (requires running event loop)
    scheduler.start()

    # Print summary (next_run_time available after start)
    jobs = scheduler.get_jobs()
    print("\n=== Financial Analyst Scheduler ===", flush=True)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"Tasks loaded: {len(jobs)}", flush=True)
    print(flush=True)

    for job in jobs:
        next_time = job.next_run_time.strftime("%Y-%m-%d %H:%M %Z") if job.next_run_time else "?"
        print(f"  {job.id}", flush=True)
        print(f"    Next run: {next_time}", flush=True)
        print(flush=True)

    if not jobs:
        print("  No enabled tasks found. Nothing to schedule.", flush=True)
        print("  Check config/tasks/*.yaml and set enabled: true", flush=True)
        scheduler.shutdown()
        return

    # Check for missed tasks that should have run today
    await _check_catchup_tasks()

    print("Press Ctrl+C to stop.\n", flush=True)

    # Keep running forever — APScheduler fires jobs in the background
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    except asyncio.CancelledError:
        pass
    finally:
        scheduler.shutdown(wait=True)


def run_scheduler() -> None:
    """Start the scheduler and run until interrupted with Ctrl+C."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    ensure_directories()

    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        print("\nScheduler stopped.")
