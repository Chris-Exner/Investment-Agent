"""OpenAI GPT API client wrapper using the Responses API."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Literal, TypeVar

from openai import OpenAI, APIError as OpenAIAPIError
from pydantic import BaseModel

from analyst.core.config import get_env
from analyst.core.exceptions import LLMError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

ReasoningEffort = Literal["none", "low", "medium", "high", "xhigh"]


class LLMClient:
    """Wrapper around the OpenAI SDK using the Responses API (GPT-5+)."""

    def __init__(self, model: str = "gpt-5.5", max_retries: int = 3):
        api_key = get_env("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key, max_retries=max_retries)
        self.model = model
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    async def analyze(
        self,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int = 4096,
        reasoning_effort: ReasoningEffort = "medium",
    ) -> dict[str, Any]:
        """Send a prompt to GPT and return the text response with metadata.

        Returns:
            dict with keys: text, input_tokens, output_tokens, model
        """
        try:
            response = await asyncio.to_thread(
                self.client.responses.create,
                model=self.model,
                instructions=system_prompt,
                input=user_prompt,
                max_output_tokens=max_output_tokens,
                reasoning={"effort": reasoning_effort},
            )

            text = response.output_text or ""
            input_tokens = response.usage.input_tokens if response.usage else 0
            output_tokens = response.usage.output_tokens if response.usage else 0

            self._total_input_tokens += input_tokens
            self._total_output_tokens += output_tokens

            logger.info(
                f"GPT API call: {input_tokens} in / {output_tokens} out tokens "
                f"(model: {self.model})"
            )

            return {
                "text": text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": self.model,
            }

        except OpenAIAPIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMError(f"OpenAI API error: {e}") from e

    async def analyze_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        max_output_tokens: int = 4096,
        reasoning_effort: ReasoningEffort = "medium",
    ) -> tuple[T, dict[str, Any]]:
        """Send a prompt to GPT and parse the response into a Pydantic model.

        Uses the Responses API native structured-output parser.

        Returns:
            Tuple of (parsed model instance, metadata dict)
        """
        try:
            response = await asyncio.to_thread(
                self.client.responses.parse,
                model=self.model,
                instructions=system_prompt,
                input=user_prompt,
                text_format=response_model,
                max_output_tokens=max_output_tokens,
                reasoning={"effort": reasoning_effort},
            )

            parsed = response.output_parsed
            if parsed is None:
                raise LLMError("GPT did not return a parsed structured response")

            input_tokens = response.usage.input_tokens if response.usage else 0
            output_tokens = response.usage.output_tokens if response.usage else 0
            self._total_input_tokens += input_tokens
            self._total_output_tokens += output_tokens

            metadata = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": self.model,
            }

            logger.info(
                f"GPT structured call ({response_model.__name__}): "
                f"{input_tokens} in / {output_tokens} out tokens"
            )

            return parsed, metadata

        except OpenAIAPIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMError(f"OpenAI API error: {e}") from e
        except Exception as e:
            if isinstance(e, LLMError):
                raise
            logger.error(f"Error parsing GPT response: {e}")
            raise LLMError(f"Error parsing structured response: {e}") from e

    async def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_output_tokens: int = 4096,
        reasoning_effort: ReasoningEffort = "medium",
    ) -> dict[str, Any]:
        """Multi-turn chat with optional tool use, on the Responses API.

        Accepts a Chat-Completions-style message history (with 'role' and either
        'content', 'tool_calls', or 'tool_call_id' fields) and converts it to
        the Responses API input-item format internally.

        Args:
            messages: Message history in Chat Completions format (system, user,
                assistant, tool roles).
            tools: Tool definitions in Responses API format (type=function,
                name/description/parameters at top level).
            max_output_tokens: Max response tokens.
            reasoning_effort: Reasoning effort for the model.

        Returns:
            dict with keys: content, tool_calls, input_tokens, output_tokens, model
        """
        instructions, input_items = _convert_messages_to_responses_input(messages)

        kwargs: dict[str, Any] = {
            "model": self.model,
            "input": input_items,
            "max_output_tokens": max_output_tokens,
            "reasoning": {"effort": reasoning_effort},
        }
        if instructions is not None:
            kwargs["instructions"] = instructions
        if tools:
            kwargs["tools"] = tools

        try:
            response = await asyncio.to_thread(
                self.client.responses.create, **kwargs
            )

            input_tokens = response.usage.input_tokens if response.usage else 0
            output_tokens = response.usage.output_tokens if response.usage else 0

            self._total_input_tokens += input_tokens
            self._total_output_tokens += output_tokens

            tool_calls: list[dict[str, Any]] | None = None
            collected_calls: list[dict[str, Any]] = []
            for item in response.output or []:
                item_type = getattr(item, "type", None)
                if item_type == "function_call":
                    arguments_raw = getattr(item, "arguments", "") or "{}"
                    try:
                        arguments = json.loads(arguments_raw)
                    except json.JSONDecodeError:
                        arguments = {}
                    collected_calls.append({
                        "id": getattr(item, "call_id", None) or getattr(item, "id", ""),
                        "function_name": getattr(item, "name", ""),
                        "arguments": arguments,
                    })
            if collected_calls:
                tool_calls = collected_calls

            content = response.output_text or None

            logger.info(
                f"GPT chat call: {input_tokens} in / {output_tokens} out tokens "
                f"(model: {self.model}, tools: {len(tool_calls) if tool_calls else 0})"
            )

            return {
                "content": content,
                "tool_calls": tool_calls,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": self.model,
            }

        except OpenAIAPIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMError(f"OpenAI API error: {e}") from e

    @property
    def total_tokens(self) -> dict[str, int]:
        """Return total token usage across all calls."""
        return {
            "input": self._total_input_tokens,
            "output": self._total_output_tokens,
            "total": self._total_input_tokens + self._total_output_tokens,
        }


def _convert_messages_to_responses_input(
    messages: list[dict[str, Any]],
) -> tuple[str | None, list[dict[str, Any]]]:
    """Translate Chat-Completions-style messages to Responses API input items.

    - The leading system message (if any) is returned as `instructions`.
    - User/assistant text messages become `{"role": ..., "content": ...}` items.
    - Assistant messages with `tool_calls` are expanded into
      `{"type": "function_call", "call_id": ..., "name": ..., "arguments": ...}` items.
    - Tool result messages (`role: "tool"`) become
      `{"type": "function_call_output", "call_id": ..., "output": ...}` items.
    """
    instructions: str | None = None
    items: list[dict[str, Any]] = []

    for idx, msg in enumerate(messages):
        role = msg.get("role")
        if role == "system" and idx == 0 and instructions is None:
            instructions = msg.get("content") or ""
            continue

        if role == "tool":
            items.append({
                "type": "function_call_output",
                "call_id": msg.get("tool_call_id", ""),
                "output": msg.get("content", ""),
            })
            continue

        if role == "assistant" and msg.get("tool_calls"):
            text = msg.get("content") or ""
            if text:
                items.append({"role": "assistant", "content": text})
            for tc in msg["tool_calls"]:
                fn = tc.get("function", {})
                items.append({
                    "type": "function_call",
                    "call_id": tc.get("id", ""),
                    "name": fn.get("name", ""),
                    "arguments": fn.get("arguments", "{}"),
                })
            continue

        if role in ("user", "assistant", "system"):
            items.append({"role": role, "content": msg.get("content") or ""})

    return instructions, items
