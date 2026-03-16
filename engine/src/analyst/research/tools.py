"""OpenAI function-calling tool definitions and executor for the research agent."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from analyst.data.aggregator import DataAggregator

logger = logging.getLogger(__name__)


# --- OpenAI tool definitions ---

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_quote",
            "description": (
                "Aktuelle Kursdaten fuer eine Aktie abrufen: Kurs, Veraenderung, "
                "Marktkapitalisierung, KGV, 52-Wochen-Hoch/Tief, Volumen."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Aktien-Ticker (z.B. 'AAPL', 'NVDA', 'MSFT')",
                    },
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_financials",
            "description": (
                "Fundamentaldaten eines Unternehmens abrufen: Umsatz, Wachstum, Margen, "
                "EPS, Free Cash Flow, Verschuldung, Bewertungskennzahlen (KGV, EV/EBITDA, P/B)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Aktien-Ticker (z.B. 'AAPL')",
                    },
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_multiple_stocks",
            "description": (
                "Kursdaten fuer mehrere Aktien gleichzeitig abrufen. "
                "Nuetzlich fuer Branchenvergleiche oder Peer-Analysen."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Liste von Ticker-Symbolen (z.B. ['AAPL', 'MSFT', 'GOOGL'])",
                    },
                },
                "required": ["tickers"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sector_performance",
            "description": (
                "Performance aller Marktsektoren abrufen (Technology, Healthcare, etc.). "
                "Zeigt welche Sektoren aktuell stark oder schwach performen."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_macro_indicators",
            "description": (
                "Makrooekonomische Indikatoren abrufen: VIX (Volatilitaet), "
                "Treasury Yields, Dollar-Index etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "indicators": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Liste von Indikator-IDs. Verfuegbar: "
                            "'^VIX' (Volatility Index), "
                            "'^TNX' (10Y Treasury Yield), "
                            "'^TYX' (30Y Treasury Yield), "
                            "'DX-Y.NYB' (US Dollar Index)"
                        ),
                    },
                },
                "required": ["indicators"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_news",
            "description": (
                "Aktuelle Finanznachrichten aus RSS-Feeds durchsuchen "
                "(Google Finance, Yahoo Finance, MarketWatch, CNBC)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "max_items": {
                        "type": "integer",
                        "description": "Maximale Anzahl Nachrichten (Standard: 15)",
                        "default": 15,
                    },
                    "max_age_hours": {
                        "type": "integer",
                        "description": "Maximales Alter in Stunden (Standard: 48)",
                        "default": 48,
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_position",
            "description": (
                "Eine neue Investment-Position vorschlagen, wenn du zu einer Investment-"
                "Ueberzeugung gekommen bist. Der Nutzer muss den Vorschlag bestaetigen, "
                "bevor die Position erstellt wird. Nutze dies nur nach gruendlicher Analyse."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Aktien-Ticker (z.B. 'NVDA')",
                    },
                    "name": {
                        "type": "string",
                        "description": "Vollstaendiger Unternehmensname (z.B. 'NVIDIA Corporation')",
                    },
                    "thesis": {
                        "type": "string",
                        "description": (
                            "Investment-These: Warum ist dieses Investment attraktiv? "
                            "Beschreibe die Kernueberzeugung, Wettbewerbsvorteile und Wachstumstreiber."
                        ),
                    },
                    "bear_triggers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Bear-Case Trigger: 3-5 konkrete Ereignisse oder Entwicklungen, "
                            "die die These gefaehrden wuerden und zum Verkauf fuehren sollten."
                        ),
                    },
                    "reasoning": {
                        "type": "string",
                        "description": (
                            "Ausfuehrliche Begruendung: Zusammenfassung der Recherche, "
                            "Datenlage und warum jetzt der richtige Zeitpunkt ist."
                        ),
                    },
                },
                "required": ["ticker", "name", "thesis", "bear_triggers", "reasoning"],
            },
        },
    },
]


# --- Predefined macro indicator mappings ---

_MACRO_INDICATOR_MAP: dict[str, dict[str, str]] = {
    "^VIX": {"series_id": "^VIX", "name": "VIX Volatility Index", "source": "yfinance"},
    "^TNX": {"series_id": "^TNX", "name": "10Y Treasury Yield", "source": "yfinance"},
    "^TYX": {"series_id": "^TYX", "name": "30Y Treasury Yield", "source": "yfinance"},
    "DX-Y.NYB": {"series_id": "DX-Y.NYB", "name": "US Dollar Index", "source": "yfinance"},
}


# --- Tool executor ---

async def execute_tool(
    function_name: str,
    arguments: dict[str, Any],
    data_aggregator: DataAggregator,
) -> dict[str, Any]:
    """Execute a tool call and return the result as a serializable dict.

    Args:
        function_name: Name of the tool to execute.
        arguments: Tool arguments from the LLM.
        data_aggregator: DataAggregator instance for data fetching.

    Returns:
        dict with the tool result, ready for JSON serialization.
    """
    logger.info(f"Executing tool: {function_name}({arguments})")

    if function_name == "get_stock_quote":
        ticker = arguments["ticker"].upper()
        stock = await data_aggregator.get_stock_data(ticker)
        if stock:
            data = stock.model_dump()
            # Remove verbose history to keep context manageable
            data.pop("history", None)
            return {"status": "success", "data": data}
        return {"status": "error", "message": f"Keine Daten fuer {ticker} gefunden"}

    elif function_name == "get_company_financials":
        ticker = arguments["ticker"].upper()
        financials = await data_aggregator.get_financials(ticker)
        if financials:
            return {"status": "success", "data": financials.model_dump()}
        return {"status": "error", "message": f"Keine Fundamentaldaten fuer {ticker} gefunden"}

    elif function_name == "get_multiple_stocks":
        tickers = [t.upper() for t in arguments["tickers"]]
        stocks = await data_aggregator.get_multiple_stocks(tickers)
        results = []
        for s in stocks:
            d = s.model_dump()
            d.pop("history", None)
            results.append(d)
        return {"status": "success", "data": results, "count": len(results)}

    elif function_name == "get_sector_performance":
        sectors = await data_aggregator.get_sector_performance()
        return {
            "status": "success",
            "data": [s.model_dump() for s in sectors],
            "count": len(sectors),
        }

    elif function_name == "get_macro_indicators":
        indicator_ids = arguments.get("indicators", [])
        indicator_configs = []
        for ind_id in indicator_ids:
            if ind_id in _MACRO_INDICATOR_MAP:
                indicator_configs.append(_MACRO_INDICATOR_MAP[ind_id])
            else:
                # Try as yfinance ticker directly
                indicator_configs.append({
                    "series_id": ind_id,
                    "name": ind_id,
                    "source": "yfinance",
                })
        indicators = await data_aggregator.get_macro_indicators(indicator_configs)
        return {
            "status": "success",
            "data": [i.model_dump() for i in indicators],
            "count": len(indicators),
        }

    elif function_name == "search_news":
        max_items = arguments.get("max_items", 15)
        max_age_hours = arguments.get("max_age_hours", 48)
        news = await data_aggregator.fetch_news(
            max_items=max_items,
            max_age_hours=max_age_hours,
        )
        items = []
        for n in news:
            d = n.model_dump()
            # Convert datetime to string
            if d.get("published") and isinstance(d["published"], datetime):
                d["published"] = d["published"].isoformat()
            items.append(d)
        return {"status": "success", "data": items, "count": len(items)}

    elif function_name == "propose_position":
        # propose_position doesn't fetch data — it returns the proposal for user confirmation
        return {
            "status": "proposal",
            "data": {
                "ticker": arguments["ticker"].upper(),
                "name": arguments["name"],
                "thesis": arguments["thesis"],
                "bear_triggers": arguments["bear_triggers"],
                "reasoning": arguments["reasoning"],
            },
        }

    else:
        return {"status": "error", "message": f"Unbekanntes Tool: {function_name}"}
