"""Configuration loading from .env and YAML task files."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from analyst.core.types import TaskConfig

# Resolve project root (financial-analyst/)
_ENGINE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # engine/
PROJECT_ROOT = _ENGINE_DIR.parent  # financial-analyst/

# Key directories
CONFIG_DIR = PROJECT_ROOT / "config"
TASKS_DIR = CONFIG_DIR / "tasks"
PROMPTS_DIR = CONFIG_DIR / "prompts"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
LOGS_DIR = DATA_DIR / "logs"


def load_env() -> None:
    """Load environment variables from .env file."""
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)
    else:
        # Try parent directories
        load_dotenv(override=True)


def get_env(key: str, default: str | None = None) -> str:
    """Get an environment variable, raising if required and missing."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value


def load_task_config(task_name: str) -> TaskConfig:
    """Load a task configuration from YAML file."""
    yaml_path = TASKS_DIR / f"{task_name}.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"Task config not found: {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return TaskConfig(**raw)


def list_task_configs() -> list[str]:
    """List all available task configuration names."""
    if not TASKS_DIR.exists():
        return []
    return [p.stem for p in TASKS_DIR.glob("*.yaml")]


def ensure_directories() -> None:
    """Ensure all required data directories exist."""
    for d in [DATA_DIR, RESULTS_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


# Load env on import
load_env()
