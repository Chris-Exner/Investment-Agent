"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from analyst.api.routes import positions, runs, tasks


def create_app() -> FastAPI:
    app = FastAPI(title="Financial Analyst Dashboard", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(positions.router, prefix="/api/positions", tags=["positions"])
    app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
    app.include_router(runs.router, prefix="/api/runs", tags=["runs"])

    return app


app = create_app()
