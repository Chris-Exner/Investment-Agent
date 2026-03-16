"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from analyst.api.routes import positions, runs, tasks, research
from analyst.research.db import init_research_db


def create_app() -> FastAPI:
    app = FastAPI(title="Financial Analyst Dashboard", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize research database tables
    init_research_db()

    app.include_router(positions.router, prefix="/api/positions", tags=["positions"])
    app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
    app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
    app.include_router(research.router, prefix="/api/research", tags=["research"])

    return app


app = create_app()
