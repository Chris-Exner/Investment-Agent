"""OpenAI GPT API client wrapper with structured output via function calling."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, TypeVar

from openai import OpenAI, APIError as OpenAIAPIError
from pydantic import BaseModel

from analyst.core.config import get_env
from analyst.core.exceptions import LLMError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """Wrapper around the OpenAI SDK for GPT API calls."""

    def __init__(self, model: str = "gpt-4.1", max_retries: int = 3):
        api_key = get_env("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key, max_retries=max_retries)
        self.model = model
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    async def analyze(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """Send a prompt to GPT and return the text response with metadata.

        Returns:
            dict with keys: text, input_tokens, output_tokens, model
        """
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            text = response.choices[0].message.content or ""
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0

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
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> tuple[T, dict[str, Any]]:
        """Send a prompt to GPT and parse the response into a Pydantic model.

        Uses function calling to get structured JSON output.

        Returns:
            Tuple of (parsed model instance, metadata dict)
        """
        schema = response_model.model_json_schema()
        tool_name = response_model.__name__

        # Resolve $defs references inline for OpenAI compatibility
        schema = self._resolve_schema_refs(schema)

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "description": f"Return the analysis result as structured {tool_name}",
                            "parameters": schema,
                        },
                    }
                ],
                tool_choice={"type": "function", "function": {"name": tool_name}},
            )

            # Extract function call arguments
            message = response.choices[0].message
            if not message.tool_calls or len(message.tool_calls) == 0:
                raise LLMError("GPT did not return a function call")

            arguments_json = message.tool_calls[0].function.arguments
            tool_input = json.loads(arguments_json)
            parsed = response_model.model_validate(tool_input)

            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            self._total_input_tokens += input_tokens
            self._total_output_tokens += output_tokens

            metadata = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": self.model,
            }

            logger.info(
                f"GPT structured call ({tool_name}): "
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

    def _resolve_schema_refs(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Resolve $defs/$ref references inline for OpenAI compatibility.

        Pydantic v2 generates schemas with $defs for nested models and enums.
        OpenAI function calling works better with inline definitions.
        """
        defs = schema.pop("$defs", None) or schema.pop("definitions", None)
        if not defs:
            return schema

        def _resolve(obj: Any) -> Any:
            if isinstance(obj, dict):
                if "$ref" in obj:
                    ref_path = obj["$ref"]  # e.g., "#/$defs/Outlook"
                    ref_name = ref_path.split("/")[-1]
                    if ref_name in defs:
                        return _resolve(defs[ref_name])
                    return obj
                return {k: _resolve(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_resolve(item) for item in obj]
            return obj

        return _resolve(schema)

    @property
    def total_tokens(self) -> dict[str, int]:
        """Return total token usage across all calls."""
        return {
            "input": self._total_input_tokens,
            "output": self._total_output_tokens,
            "total": self._total_input_tokens + self._total_output_tokens,
        }
