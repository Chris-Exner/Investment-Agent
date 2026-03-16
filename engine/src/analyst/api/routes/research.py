"""API routes for the interactive research agent."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from analyst.api.models import (
    ConfirmPositionIn,
    ConversationCreate,
    ConversationDetailOut,
    ConversationOut,
    MessageOut,
    PositionOut,
    SendMessageIn,
    SendMessageOut,
)
from analyst.api.routes.positions import _read_positions, _write_positions, _to_out
from analyst.research.agent import ResearchAgent
from analyst.research.db import (
    add_message,
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    update_conversation_title,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _msg_to_out(m: Any) -> MessageOut:
    """Convert a ConversationMessage to API output."""
    created_at = m.created_at
    if hasattr(created_at, "isoformat"):
        created_at = created_at.isoformat()
    return MessageOut(
        id=m.id or 0,
        role=m.role.value if hasattr(m.role, "value") else str(m.role),
        content=m.content,
        tool_calls=[tc.model_dump() if hasattr(tc, "model_dump") else tc for tc in m.tool_calls] if m.tool_calls else None,
        data_cards=m.data_cards or [],
        created_at=str(created_at),
    )


def _conv_to_out(conv: Any) -> ConversationOut:
    """Convert a ConversationSummary/Detail to API output."""
    return ConversationOut(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=conv.message_count,
        status=conv.status,
    )


# --- Conversations CRUD ---


@router.get("/conversations", response_model=list[ConversationOut])
def get_conversations(limit: int = 50):
    """List all research conversations."""
    convs = list_conversations(limit=limit)
    return [_conv_to_out(c) for c in convs]


@router.post("/conversations", response_model=ConversationOut, status_code=201)
def new_conversation(body: ConversationCreate):
    """Create a new research conversation."""
    conv_id = create_conversation(title=body.title)
    conv = get_conversation(conv_id)
    if not conv:
        raise HTTPException(500, "Konversation konnte nicht erstellt werden")
    return _conv_to_out(conv)


@router.get("/conversations/{conv_id}", response_model=ConversationDetailOut)
def get_conversation_detail(conv_id: int):
    """Get a conversation with all messages."""
    conv = get_conversation(conv_id)
    if not conv:
        raise HTTPException(404, f"Konversation {conv_id} nicht gefunden")
    return ConversationDetailOut(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=conv.message_count,
        status=conv.status,
        messages=[_msg_to_out(m) for m in conv.messages],
    )


@router.delete("/conversations/{conv_id}", status_code=204)
def remove_conversation(conv_id: int):
    """Delete a conversation and all its messages."""
    if not delete_conversation(conv_id):
        raise HTTPException(404, f"Konversation {conv_id} nicht gefunden")


# --- Messages ---


@router.post(
    "/conversations/{conv_id}/messages",
    response_model=SendMessageOut,
)
async def send_message(conv_id: int, body: SendMessageIn):
    """Send a message to the research agent and get the response.

    This endpoint blocks until the agent has fully processed the message,
    including any tool calls. Acceptable for a single-user local app.
    """
    # Verify conversation exists
    conv = get_conversation(conv_id)
    if not conv:
        raise HTTPException(404, f"Konversation {conv_id} nicht gefunden")

    # Store user message
    user_msg_id = add_message(conv_id, role="user", content=body.content)

    # Build OpenAI-format message history from stored conversation
    openai_messages = _build_openai_messages(conv, body.content)

    # Run the research agent
    agent = ResearchAgent()
    try:
        response = await agent.process_message(openai_messages)
    except Exception as e:
        logger.error(f"Research agent error: {e}", exc_info=True)
        # Store error message
        error_text = f"Fehler bei der Verarbeitung: {str(e)}"
        error_msg_id = add_message(
            conv_id,
            role="assistant",
            content=error_text,
        )
        raise HTTPException(500, error_text)

    # Store intermediate messages (tool calls + results) for history fidelity
    for im in response.intermediate_messages:
        role = im.get("role", "tool")
        content = im.get("content", "")
        tool_calls_data = None
        tool_call_id = None

        if role == "assistant" and im.get("tool_calls"):
            tool_calls_data = im["tool_calls"]
        if role == "tool":
            tool_call_id = im.get("tool_call_id")

        add_message(
            conv_id,
            role=role,
            content=content,
            tool_calls=tool_calls_data,
            tool_call_id=tool_call_id,
        )

    # Store the assistant's final response
    assistant_msg_id = add_message(
        conv_id,
        role="assistant",
        content=response.content,
        data_cards=response.data_cards if response.data_cards else None,
    )

    # Auto-generate title from first user message if it's the default
    if conv.title == "Neue Recherche" and conv.message_count == 0:
        # Use first ~60 chars of user message as title
        title = body.content[:60].strip()
        if len(body.content) > 60:
            title += "..."
        update_conversation_title(conv_id, title)

    # Build response
    user_out = MessageOut(
        id=user_msg_id,
        role="user",
        content=body.content,
        created_at="",
        data_cards=[],
    )
    assistant_out = MessageOut(
        id=assistant_msg_id,
        role="assistant",
        content=response.content,
        data_cards=response.data_cards or [],
        created_at="",
    )

    proposal_dict = None
    if response.position_proposal:
        proposal_dict = response.position_proposal.model_dump()

    return SendMessageOut(
        user_message=user_out,
        assistant_message=assistant_out,
        position_proposal=proposal_dict,
        tokens_input=response.tokens_input,
        tokens_output=response.tokens_output,
    )


# --- Position creation ---


@router.post(
    "/conversations/{conv_id}/confirm-position",
    response_model=PositionOut,
    status_code=201,
)
def confirm_position(conv_id: int, body: ConfirmPositionIn):
    """Confirm and create a position proposed by the research agent."""
    # Verify conversation exists
    conv = get_conversation(conv_id)
    if not conv:
        raise HTTPException(404, f"Konversation {conv_id} nicht gefunden")

    # Create position using existing logic from positions.py
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

    # Add confirmation message to conversation
    add_message(
        conv_id,
        role="assistant",
        content=f"Position **{ticker_upper}** ({body.name}) wurde erfolgreich erstellt und wird ab sofort im Investment Thesis Check ueberwacht.",
    )

    return _to_out(new)


# --- Helpers ---


def _build_openai_messages(
    conv: Any,
    new_user_content: str,
) -> list[dict[str, Any]]:
    """Convert stored conversation messages to OpenAI format.

    Builds the complete message history that will be sent to the LLM.
    The system prompt is added by the ResearchAgent itself.
    """
    messages: list[dict[str, Any]] = []

    for m in conv.messages:
        role = m.role.value if hasattr(m.role, "value") else str(m.role)

        if role == "assistant" and m.tool_calls:
            # Assistant message with tool calls
            msg: dict[str, Any] = {
                "role": "assistant",
                "content": m.content or "",
                "tool_calls": m.tool_calls if isinstance(m.tool_calls, list) else [],
            }
            messages.append(msg)
        elif role == "tool" and m.tool_call_id:
            # Tool result message
            messages.append({
                "role": "tool",
                "tool_call_id": m.tool_call_id,
                "content": m.content,
            })
        else:
            # Regular user or assistant message
            messages.append({
                "role": role,
                "content": m.content,
            })

    # Add the new user message
    messages.append({"role": "user", "content": new_user_content})

    return messages
