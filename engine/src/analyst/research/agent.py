"""Core research agent with multi-turn conversation and tool use."""

from __future__ import annotations

import logging
from typing import Any

from analyst.data.aggregator import DataAggregator
from analyst.llm.client import LLMClient
from analyst.llm.prompts import SYSTEM_PROMPT, load_prompt
from analyst.research.tools import TOOL_DEFINITIONS, execute_tool
from analyst.research.types import AgentResponse, PositionProposal

logger = logging.getLogger(__name__)

# Maximum tool-calling iterations per user message
MAX_TOOL_ITERATIONS = 5


def _build_system_prompt() -> str:
    """Build the full system prompt for the research agent."""
    try:
        research_instructions = load_prompt(
            "research_agent", version="v2"
        )
    except Exception:
        logger.warning("Could not load research_agent prompt template, using fallback")
        research_instructions = _FALLBACK_RESEARCH_INSTRUCTIONS

    return f"{SYSTEM_PROMPT}\n\n{research_instructions}"


_FALLBACK_RESEARCH_INSTRUCTIONS = """\
## Forschungsmodus

Du befindest dich im interaktiven Forschungsmodus. Du arbeitest mit dem Nutzer zusammen, \
um neue Investment-Ideen zu identifizieren und zu analysieren.

Deine Werkzeuge:
- get_stock_quote(ticker) — Aktuelle Kursdaten abrufen
- get_company_financials(ticker) — Fundamentaldaten abrufen
- get_multiple_stocks(tickers) — Mehrere Kurse gleichzeitig
- get_sector_performance() — Sektorperformance
- get_macro_indicators(indicators) — Makro-Indikatoren
- search_news(max_items, max_age_hours) — Aktuelle Nachrichten
- propose_position(ticker, name, thesis, bear_triggers, reasoning) — Position vorschlagen

Arbeitsweise:
- Nutze Werkzeuge proaktiv, wenn Daten die Diskussion bereichern
- Frage den Nutzer bei jedem Schritt nach Input — dies ist ein kollaborativer Prozess
- Fokussiere auf Branchen in Disruption und Langzeit-Trends (1-5 Jahre Haltedauer)
- Wenn du zu einer Investment-Ueberzeugung kommst, nutze propose_position
- Sei direkt mit deiner Meinung, aber respektiere die Entscheidung des Nutzers
- Recherchiere gruendlich bevor du eine Position vorschlaegst
"""


def _data_card_type(function_name: str) -> str:
    """Map a tool function name to a data card type for frontend rendering."""
    mapping = {
        "get_stock_quote": "stock_quote",
        "get_company_financials": "company_financials",
        "get_multiple_stocks": "multiple_stocks",
        "get_sector_performance": "sector_performance",
        "get_macro_indicators": "macro_indicators",
        "search_news": "news",
        "propose_position": "position_proposal",
    }
    return mapping.get(function_name, "unknown")


class ResearchAgent:
    """Multi-turn research agent with tool-use capabilities."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        data_aggregator: DataAggregator | None = None,
    ):
        self.llm = llm_client or LLMClient()
        self.data = data_aggregator or DataAggregator()

    async def process_message(
        self,
        conversation_messages: list[dict[str, Any]],
    ) -> AgentResponse:
        """Process one user turn in a conversation.

        Takes the full conversation history (already in OpenAI message format),
        sends it to the LLM with tools, handles any tool calls in a loop,
        and returns the final response.

        Args:
            conversation_messages: Full message history in OpenAI format
                (list of dicts with role, content, tool_calls, tool_call_id).

        Returns:
            AgentResponse with the final text, data cards, and optional position proposal.
        """
        system_prompt = _build_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_messages)

        total_input = 0
        total_output = 0
        data_cards: list[dict[str, Any]] = []
        intermediate_messages: list[dict[str, Any]] = []
        position_proposal: PositionProposal | None = None

        for iteration in range(MAX_TOOL_ITERATIONS):
            response = await self.llm.chat_with_tools(
                messages=messages,
                tools=TOOL_DEFINITIONS,
                max_output_tokens=4096,
                reasoning_effort="medium",
            )

            total_input += response["input_tokens"]
            total_output += response["output_tokens"]

            tool_calls = response.get("tool_calls")

            if not tool_calls:
                # No tool calls — final response
                return AgentResponse(
                    content=response["content"] or "",
                    data_cards=data_cards,
                    position_proposal=position_proposal,
                    tokens_input=total_input,
                    tokens_output=total_output,
                    intermediate_messages=intermediate_messages,
                )

            # Build the assistant message with tool_calls for the message history
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": response["content"] or "",
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["function_name"],
                            "arguments": _serialize_arguments(tc["arguments"]),
                        },
                    }
                    for tc in tool_calls
                ],
            }
            messages.append(assistant_msg)
            intermediate_messages.append(assistant_msg)

            # Execute each tool call
            for tc in tool_calls:
                fn_name = tc["function_name"]
                fn_args = tc["arguments"]
                tc_id = tc["id"]

                result = await execute_tool(fn_name, fn_args, self.data)

                # Collect data card for frontend rendering
                card = {
                    "type": _data_card_type(fn_name),
                    "function_name": fn_name,
                    "arguments": fn_args,
                    "data": result.get("data", result),
                }
                data_cards.append(card)

                # Check for position proposal
                if fn_name == "propose_position" and result.get("status") == "proposal":
                    position_proposal = PositionProposal(**result["data"])

                # Build tool result message for the LLM
                import json
                tool_msg: dict[str, Any] = {
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                }
                messages.append(tool_msg)
                intermediate_messages.append(tool_msg)

        # Max iterations reached — ask LLM for final summary
        messages.append({
            "role": "user",
            "content": (
                "[System: Maximale Tool-Aufrufe erreicht. "
                "Fasse zusammen was du bisher herausgefunden hast und frage den Nutzer, "
                "wie du weiter vorgehen sollst.]"
            ),
        })
        response = await self.llm.chat_with_tools(
            messages=messages,
            tools=None,  # No tools for final summary
            max_output_tokens=4096,
            reasoning_effort="medium",
        )
        total_input += response["input_tokens"]
        total_output += response["output_tokens"]

        return AgentResponse(
            content=response["content"] or "",
            data_cards=data_cards,
            position_proposal=position_proposal,
            tokens_input=total_input,
            tokens_output=total_output,
            intermediate_messages=intermediate_messages,
        )


def _serialize_arguments(args: dict[str, Any]) -> str:
    """Serialize tool arguments to JSON string for OpenAI message format."""
    import json
    return json.dumps(args, ensure_ascii=False)
