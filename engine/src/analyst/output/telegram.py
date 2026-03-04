"""Telegram Bot output channel using direct HTTP API calls."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from analyst.core.config import get_env
from analyst.core.exceptions import OutputDeliveryError
from analyst.core.types import AnalysisResult, DeliveryResult, OutputChannelType
from analyst.output.base import BaseOutputChannel

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"
MAX_MESSAGE_LENGTH = 4096


class TelegramOutput(BaseOutputChannel):
    """Send analysis results as Telegram messages."""

    channel_name = "telegram"

    async def deliver(
        self, result: AnalysisResult, config: dict[str, Any]
    ) -> DeliveryResult:
        """Send analysis text to a Telegram chat."""
        try:
            # Resolve bot token and chat ID from env vars
            token_env = config.get("bot_token_env", "TELEGRAM_BOT_TOKEN_BRIEFING")
            chat_id_env = config.get("chat_id_env", "TELEGRAM_CHAT_ID")

            bot_token = get_env(token_env)
            chat_id = get_env(chat_id_env)
            parse_mode = config.get("parse_mode", "HTML")

            text = result.analysis_text
            if not text:
                return DeliveryResult(
                    channel=OutputChannelType.TELEGRAM,
                    success=False,
                    error="No analysis text to send",
                )

            # Split long messages
            chunks = self._split_message(text, MAX_MESSAGE_LENGTH)

            async with httpx.AsyncClient(timeout=30.0) as client:
                for i, chunk in enumerate(chunks):
                    url = f"{TELEGRAM_API_BASE}/bot{bot_token}/sendMessage"
                    payload = {
                        "chat_id": chat_id,
                        "text": chunk,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": True,
                    }

                    response = await client.post(url, json=payload)

                    if response.status_code != 200:
                        error_body = response.text
                        # If HTML parse fails, retry without parse mode
                        if "can't parse entities" in error_body.lower():
                            logger.warning("HTML parse failed, retrying as plain text")
                            payload["parse_mode"] = ""
                            response = await client.post(url, json=payload)

                        if response.status_code != 200:
                            raise OutputDeliveryError(
                                "telegram",
                                f"API returned {response.status_code}: {response.text}",
                            )

                    logger.info(
                        f"Telegram message {i+1}/{len(chunks)} sent "
                        f"({len(chunk)} chars)"
                    )

            return DeliveryResult(channel=OutputChannelType.TELEGRAM, success=True)

        except OutputDeliveryError:
            raise
        except Exception as e:
            logger.error(f"Telegram delivery failed: {e}")
            return DeliveryResult(
                channel=OutputChannelType.TELEGRAM,
                success=False,
                error=str(e),
            )

    def _split_message(self, text: str, max_length: int) -> list[str]:
        """Split a long message into chunks, trying to break at paragraph boundaries."""
        if len(text) <= max_length:
            return [text]

        chunks: list[str] = []
        remaining = text

        while remaining:
            if len(remaining) <= max_length:
                chunks.append(remaining)
                break

            # Try to split at double newline (paragraph)
            split_pos = remaining.rfind("\n\n", 0, max_length)
            if split_pos == -1:
                # Try single newline
                split_pos = remaining.rfind("\n", 0, max_length)
            if split_pos == -1:
                # Force split at max length
                split_pos = max_length

            chunks.append(remaining[:split_pos].rstrip())
            remaining = remaining[split_pos:].lstrip()

        return chunks


async def send_test_message(message: str = "Test message from Financial Analyst") -> bool:
    """Send a test message to verify Telegram bot configuration."""
    output = TelegramOutput()
    dummy_result = AnalysisResult(
        task_name="test",
        analysis_type="market_overview",  # type: ignore[arg-type]
        analysis_text=message,
    )
    delivery = await output.deliver(dummy_result, {})
    return delivery.success
