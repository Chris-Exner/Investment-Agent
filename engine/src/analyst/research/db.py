"""SQLite persistence for research conversations."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from analyst.core.config import DATA_DIR
from analyst.research.types import (
    ConversationDetail,
    ConversationMessage,
    ConversationSummary,
    MessageRole,
)


def _get_db_path():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / "cache.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_get_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_research_db() -> None:
    """Create research tables if they don't exist."""
    conn = _get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS research_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT 'Neue Recherche',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS research_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL
                    REFERENCES research_conversations(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                tool_calls_json TEXT,
                tool_call_id TEXT,
                data_cards_json TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_research_messages_conv
                ON research_messages(conversation_id, created_at);
        """)
        conn.commit()
    finally:
        conn.close()


def create_conversation(title: str = "Neue Recherche") -> int:
    """Create a new conversation and return its ID."""
    conn = _get_connection()
    try:
        now = datetime.now().isoformat()
        cursor = conn.execute(
            "INSERT INTO research_conversations (title, created_at, updated_at) VALUES (?, ?, ?)",
            (title, now, now),
        )
        conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]
    finally:
        conn.close()


def add_message(
    conversation_id: int,
    role: str,
    content: str = "",
    tool_calls: list[dict] | None = None,
    tool_call_id: str | None = None,
    data_cards: list[dict] | None = None,
) -> int:
    """Add a message to a conversation and return its ID."""
    conn = _get_connection()
    try:
        now = datetime.now().isoformat()
        cursor = conn.execute(
            """INSERT INTO research_messages
               (conversation_id, role, content, tool_calls_json, tool_call_id, data_cards_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                conversation_id,
                role,
                content,
                json.dumps(tool_calls) if tool_calls else None,
                tool_call_id,
                json.dumps(data_cards) if data_cards else None,
                now,
            ),
        )
        # Update conversation timestamp
        conn.execute(
            "UPDATE research_conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )
        conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]
    finally:
        conn.close()


def get_conversation(conversation_id: int) -> ConversationDetail | None:
    """Load a full conversation with all messages."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM research_conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()
        if not row:
            return None

        msg_rows = conn.execute(
            """SELECT * FROM research_messages
               WHERE conversation_id = ?
               ORDER BY created_at ASC""",
            (conversation_id,),
        ).fetchall()

        messages = []
        for m in msg_rows:
            messages.append(
                ConversationMessage(
                    id=m["id"],
                    role=MessageRole(m["role"]),
                    content=m["content"],
                    tool_calls=json.loads(m["tool_calls_json"]) if m["tool_calls_json"] else None,
                    tool_call_id=m["tool_call_id"],
                    data_cards=json.loads(m["data_cards_json"]) if m["data_cards_json"] else [],
                    created_at=datetime.fromisoformat(m["created_at"]),
                )
            )

        return ConversationDetail(
            id=row["id"],
            title=row["title"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            message_count=len(messages),
            messages=messages,
        )
    finally:
        conn.close()


def list_conversations(limit: int = 50, offset: int = 0) -> list[ConversationSummary]:
    """List conversations ordered by most recent update."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            """SELECT c.*,
                      (SELECT COUNT(*) FROM research_messages WHERE conversation_id = c.id) as msg_count
               FROM research_conversations c
               ORDER BY c.updated_at DESC
               LIMIT ? OFFSET ?""",
            (limit, offset),
        ).fetchall()

        return [
            ConversationSummary(
                id=r["id"],
                title=r["title"],
                status=r["status"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                message_count=r["msg_count"],
            )
            for r in rows
        ]
    finally:
        conn.close()


def update_conversation_title(conversation_id: int, title: str) -> None:
    """Update a conversation's title."""
    conn = _get_connection()
    try:
        conn.execute(
            "UPDATE research_conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, datetime.now().isoformat(), conversation_id),
        )
        conn.commit()
    finally:
        conn.close()


def update_conversation_status(conversation_id: int, status: str) -> None:
    """Update a conversation's status."""
    conn = _get_connection()
    try:
        conn.execute(
            "UPDATE research_conversations SET status = ?, updated_at = ? WHERE id = ?",
            (status, datetime.now().isoformat(), conversation_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_conversation(conversation_id: int) -> bool:
    """Delete a conversation and its messages. Returns True if found."""
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM research_conversations WHERE id = ?",
            (conversation_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
