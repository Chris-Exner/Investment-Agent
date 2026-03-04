"""CRUD endpoints for investment positions."""

from __future__ import annotations

from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from analyst.api.models import PositionIn, PositionOut
from analyst.core.config import TASKS_DIR

router = APIRouter()

# Both thesis check configs share the same positions list.
_THESIS_FILES = [
    "investment_thesis_check.yaml",
    "investment_thesis_check_weekend.yaml",
]


def _primary_path() -> Path:
    return TASKS_DIR / _THESIS_FILES[0]


def _read_positions() -> list[dict]:
    """Read positions from the primary thesis check config."""
    path = _primary_path()
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    return config.get("parameters", {}).get("positions", [])


def _write_positions(positions: list[dict]) -> None:
    """Write positions to ALL thesis check config files."""
    for filename in _THESIS_FILES:
        path = TASKS_DIR / filename
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        config.setdefault("parameters", {})["positions"] = positions
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                config, f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )


def _to_out(pos: dict) -> PositionOut:
    return PositionOut(
        ticker=pos.get("ticker", ""),
        name=pos.get("name", ""),
        thesis=pos.get("thesis", ""),
        bear_triggers=pos.get("bear_triggers", []),
    )


@router.get("", response_model=list[PositionOut])
def list_positions():
    """List all investment positions."""
    return [_to_out(p) for p in _read_positions()]


@router.post("", response_model=PositionOut, status_code=201)
def create_position(body: PositionIn):
    """Add a new position."""
    positions = _read_positions()
    ticker_upper = body.ticker.strip().upper()

    if any(p["ticker"].upper() == ticker_upper for p in positions):
        raise HTTPException(409, f"Position '{ticker_upper}' existiert bereits")

    new = {
        "ticker": ticker_upper,
        "name": body.name.strip(),
        "thesis": body.thesis.strip(),
        "bear_triggers": [t.strip() for t in body.bear_triggers if t.strip()],
    }
    positions.append(new)
    _write_positions(positions)
    return _to_out(new)


@router.put("/{ticker}", response_model=PositionOut)
def update_position(ticker: str, body: PositionIn):
    """Update an existing position."""
    positions = _read_positions()
    ticker_upper = ticker.strip().upper()

    for i, pos in enumerate(positions):
        if pos["ticker"].upper() == ticker_upper:
            positions[i] = {
                "ticker": body.ticker.strip().upper(),
                "name": body.name.strip(),
                "thesis": body.thesis.strip(),
                "bear_triggers": [t.strip() for t in body.bear_triggers if t.strip()],
            }
            _write_positions(positions)
            return _to_out(positions[i])

    raise HTTPException(404, f"Position '{ticker_upper}' nicht gefunden")


@router.delete("/{ticker}", status_code=204)
def delete_position(ticker: str):
    """Remove a position."""
    positions = _read_positions()
    ticker_upper = ticker.strip().upper()
    filtered = [p for p in positions if p["ticker"].upper() != ticker_upper]

    if len(filtered) == len(positions):
        raise HTTPException(404, f"Position '{ticker_upper}' nicht gefunden")

    _write_positions(filtered)
