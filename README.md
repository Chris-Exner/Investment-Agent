# Financial Analyst Engine

AI-powered market analysis and investment monitoring with automated Telegram delivery.

## Features

- **Daily Market Overview** — Indices, sectors, commodities, forex, macro indicators and news context via GPT-4.1
- **Investment Thesis Check** — Monitors positions against defined bear triggers with continuity between runs
- **Cron Scheduler** — APScheduler with catch-up for missed executions
- **React Dashboard** — Manage positions, trigger analyses manually, browse results
- **Telegram Delivery** — Formatted analyses straight to your phone

## Tech Stack

| Area | Technologies |
|------|-------------|
| Backend | Python 3.11+, FastAPI, APScheduler, Pydantic |
| AI | OpenAI GPT-4.1 (Structured Output) |
| Data | yfinance, RSS/News Scraping, FRED API |
| Frontend | React 19, TypeScript, Vite |
| Storage | SQLite (runs & cache), YAML (configuration) |
| Output | Telegram Bot API |

## Project Structure

```
financial-analyst/
├── engine/                        # Python backend
│   └── src/analyst/
│       ├── analysis/              # Analyzers (Market Overview, Thesis Check)
│       ├── api/                   # FastAPI REST endpoints
│       ├── core/                  # Config, types, cache (SQLite)
│       ├── data/                  # Data sources (yfinance, news, FRED)
│       ├── llm/                   # OpenAI client & prompt rendering
│       ├── output/                # Telegram delivery
│       ├── executor.py            # Task execution logic
│       ├── scheduler.py           # Cron scheduler with catch-up
│       └── cli.py                 # CLI (run, list, serve, scheduler)
├── dashboard/                     # React frontend (Vite)
│   └── src/
│       ├── pages/                 # Positions, Runs, Run Detail
│       ├── components/            # Cards, forms, trigger buttons
│       └── api/                   # Typed API client
├── config/
│   ├── tasks/                     # Task definitions (YAML)
│   └── prompts/                   # Jinja2 prompt templates
└── data/                          # SQLite DB, logs, results
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API Key
- Telegram Bot Token + Chat ID

### Installation

```bash
# Create .env in project root
cp .env.example .env
# Fill in the following keys:
#   OPENAI_API_KEY, TELEGRAM_BOT_TOKEN_BRIEFING,
#   TELEGRAM_BOT_TOKEN_THESIS, TELEGRAM_CHAT_ID

# Backend
cd engine
pip install -e .

# Frontend
cd ../dashboard
npm install
```

## Usage

### CLI

```bash
analyst list                              # Show all tasks
analyst run market_overview --dry-run     # Run analysis (skip Telegram)
analyst run investment_thesis_check       # Thesis check with delivery
analyst scheduler start                   # Start cron scheduler
analyst scheduler status                  # Show next runs & last status
```

### Dashboard

```bash
# Terminal 1: API server
analyst serve                             # http://localhost:8000

# Terminal 2: React dev server
cd dashboard && npm run dev               # http://localhost:5173
```

The dashboard provides:
- **Positions** — Manage stocks with investment thesis and bear triggers
- **Runs** — Trigger analyses manually (dry run or with Telegram delivery)
- **History** — Browse past runs with full result details

## Task Configuration

Tasks are defined as YAML in `config/tasks/`. See `*.yaml.example` for templates:

```yaml
schedule:
  cron: "0 22 * * 1-5"           # Mon-Fri at 22:00
  timezone: "Europe/Berlin"

parameters:
  positions:                      # Thesis check only
    - ticker: "NVDA"
      name: "NVIDIA"
      thesis: "AI infrastructure monopolist..."
      bear_triggers:
        - "AI investment slowdown"
        - "Export restrictions"

llm:
  model: "gpt-4.1"
  prompt_template: "thesis_check"

output_channels:
  - type: telegram
    config:
      bot_token_env: "TELEGRAM_BOT_TOKEN_THESIS"
      chat_id_env: "TELEGRAM_CHAT_ID"
```

## Analyses

### Market Overview

Daily analysis (Mon-Fri 22:00) and Monday morning briefing (06:00) with weekly outlook.
Covers S&P 500, DAX, Nikkei, Gold, Oil, EUR/USD, VIX, Treasury yields, sector performance
and current financial news. GPT produces a structured market assessment with sentiment
ratings and risk indicators.

### Investment Thesis Check

Daily review (Mon-Fri 22:00) and Monday morning review (06:00) of your positions.
For each stock, price, fundamentals and news are checked against the defined thesis and
bear triggers. The system remembers previous checks — warnings cannot silently disappear
but must be explicitly resolved.
