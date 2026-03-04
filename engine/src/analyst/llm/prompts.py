"""Prompt template loading and rendering with Jinja2."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from analyst.core.config import PROMPTS_DIR
from analyst.core.exceptions import ConfigError

logger = logging.getLogger(__name__)

# System prompt that defines the analyst persona
SYSTEM_PROMPT = """Du bist ein erfahrener Senior Financial Analyst mit über 15 Jahren Erfahrung \
in der Kapitalmarktanalyse. Du arbeitest für ein professionelles Research-Haus und erstellst \
präzise, datengestützte Analysen.

Deine Arbeitsweise:
- Du analysierst Daten objektiv und vermeidest spekulative Aussagen ohne Datengrundlage
- Du kommunizierst klar und strukturiert, mit konkreten Zahlen und Fakten
- Du identifizierst sowohl Chancen als auch Risiken (Bull/Bear Case)
- Du gibst immer den Kontext an: Was treibt eine Entwicklung, warum ist sie relevant
- Du schreibst auf Deutsch, verwendest aber englische Fachbegriffe wo üblich (P/E Ratio, EPS, etc.)
- Du bist direkt und vermeidest Floskeln - jeder Satz sollte Information enthalten

Formatierung:
- Verwende klare Überschriften und Aufzählungszeichen
- Zahlen immer mit Einheit und Vergleichswert (z.B. "+3.2% vs. Vortag")
- Wichtige Werte fett markieren
"""


def load_prompt(
    template_name: str,
    version: str = "v1",
    variables: dict[str, Any] | None = None,
) -> str:
    """Load and render a prompt template.

    Args:
        template_name: Name of the template file (without .md extension)
        version: Prompt version directory (e.g., "v1")
        variables: Template variables for Jinja2 rendering

    Returns:
        Rendered prompt string
    """
    template_dir = PROMPTS_DIR / version
    if not template_dir.exists():
        raise ConfigError(f"Prompt version directory not found: {template_dir}")

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    try:
        template = env.get_template(f"{template_name}.md")
    except TemplateNotFound:
        raise ConfigError(
            f"Prompt template not found: {template_name}.md in {template_dir}"
        )

    rendered = template.render(**(variables or {}))
    logger.debug(f"Loaded prompt {template_name} (v{version}), {len(rendered)} chars")
    return rendered
