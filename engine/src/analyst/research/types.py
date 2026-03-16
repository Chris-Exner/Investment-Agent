"""Data types for the interactive research agent."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCallRequest(BaseModel):
    """A tool call the LLM wants to make."""

    id: str
    function_name: str
    arguments: dict[str, Any]


class ToolCallResult(BaseModel):
    """Result of executing a tool call."""

    tool_call_id: str
    function_name: str
    result: dict[str, Any]


class ConversationMessage(BaseModel):
    """A single message in a research conversation."""

    id: int | None = None
    role: MessageRole
    content: str = ""
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    data_cards: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class ConversationSummary(BaseModel):
    """Lightweight summary for listing conversations."""

    id: int
    title: str
    created_at: str
    updated_at: str
    message_count: int
    status: str  # "active" | "completed" | "archived"


class ConversationDetail(ConversationSummary):
    """Full conversation with messages."""

    messages: list[ConversationMessage] = Field(default_factory=list)


class PositionProposal(BaseModel):
    """Agent's proposal to create a new investment position."""

    ticker: str
    name: str
    thesis: str
    bear_triggers: list[str]
    reasoning: str


class AgentResponse(BaseModel):
    """Response from the research agent after processing a user message."""

    content: str
    data_cards: list[dict[str, Any]] = Field(default_factory=list)
    position_proposal: PositionProposal | None = None
    tokens_input: int = 0
    tokens_output: int = 0
    # Intermediate messages (tool calls + results) for DB storage
    intermediate_messages: list[dict[str, Any]] = Field(default_factory=list)
