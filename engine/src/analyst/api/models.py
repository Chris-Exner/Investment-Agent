"""Pydantic models for API request/response contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


# --- Positions ---


class PositionIn(BaseModel):
    """Create or update a position."""

    ticker: str = Field(min_length=1, max_length=10)
    name: str = Field(min_length=1)
    thesis: str = Field(min_length=1)
    bear_triggers: list[str] = Field(default_factory=list)


class PositionOut(PositionIn):
    """Position as returned by the API."""

    pass


# --- Tasks ---


class TaskInfo(BaseModel):
    """Summary of a task configuration."""

    name: str
    description: str
    analysis_type: str
    schedule_cron: str
    schedule_enabled: bool
    has_positions: bool


class TaskRunTrigger(BaseModel):
    """Request body to trigger a task run."""

    dry_run: bool = True


class TaskRunStatus(BaseModel):
    """Status of an active or recently completed run."""

    run_id: str
    task_name: str
    status: str  # "running" | "success" | "failed"
    started_at: str | None = None
    duration_seconds: float | None = None
    error_message: str | None = None
    tokens_input: int = 0
    tokens_output: int = 0
    analysis_text: str | None = None


# --- Runs ---


class RunSummary(BaseModel):
    """Row in the recent runs table."""

    id: int
    task_name: str
    status: str
    started_at: str
    completed_at: str | None = None
    duration_seconds: float | None = None
    channels_delivered: list[str] = Field(default_factory=list)
    error_message: str | None = None
    result_id: int | None = None


class RunDetail(RunSummary):
    """Full run detail including analysis output."""

    analysis_text: str | None = None
    structured_data: dict | None = None


# --- Research ---


class ConversationCreate(BaseModel):
    """Request to create a new research conversation."""

    title: str = "Neue Recherche"


class ConversationOut(BaseModel):
    """Conversation summary for list views."""

    id: int
    title: str
    created_at: str
    updated_at: str
    message_count: int
    status: str


class MessageOut(BaseModel):
    """A single conversation message."""

    id: int
    role: str
    content: str
    tool_calls: list[dict] | None = None
    data_cards: list[dict] = Field(default_factory=list)
    created_at: str


class ConversationDetailOut(ConversationOut):
    """Full conversation with messages."""

    messages: list[MessageOut] = Field(default_factory=list)


class SendMessageIn(BaseModel):
    """User message to send to the research agent."""

    content: str = Field(min_length=1)


class SendMessageOut(BaseModel):
    """Response after the agent processed a message."""

    user_message: MessageOut
    assistant_message: MessageOut
    position_proposal: dict | None = None
    tokens_input: int = 0
    tokens_output: int = 0


class ConfirmPositionIn(BaseModel):
    """Confirm and create a position proposed by the agent."""

    ticker: str = Field(min_length=1, max_length=10)
    name: str = Field(min_length=1)
    thesis: str = Field(min_length=1)
    bear_triggers: list[str] = Field(default_factory=list)
