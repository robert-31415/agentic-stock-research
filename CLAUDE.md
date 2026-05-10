# CLAUDE.md — Agentic Stock Research Assistant

This file tells Claude Code everything it needs to know about this project.
Read this file at the start of every session before writing or editing any code.

---

## What This Project Does

This is a Python CLI application that uses Claude's tool-use API to autonomously
research a stock ticker. The user types a ticker symbol (e.g., AAPL) and an AI
agent automatically calls multiple tools to gather price data, news, fundamentals,
analyst ratings, and technical signals — then synthesizes everything into a
plain-English research brief printed to the terminal.

This is a learning project. The developer has no prior coding experience.
Every code change must include clear comments explaining what the code does and why.

---

## Tech Stack

- **Language:** Python 3.10+
- **AI Model:** claude-sonnet-4-20250514 (always use this exact model string)
- **AI SDK:** anthropic (official Anthropic Python SDK)
- **Stock Data:** yfinance (Yahoo Finance wrapper — no API key required)
- **News Data:** NewsAPI (REST API — requires NEWS_API_KEY)
- **CLI:** argparse (Python stdlib)
- **Environment Variables:** python-dotenv
- **Terminal Output:** rich (colored panels and formatted text)

---

## Folder Structure

```
agentic-stock-researcher/
├── main.py              # Entry point — parses CLI args, calls run_agent()
├── agent.py             # Core agentic loop — Claude API calls and tool dispatch
├── formatter.py         # Renders research brief to terminal using rich
├── tool_definitions.py  # JSON Schema definitions for all 5 tools
├── config.py            # Loads API keys from .env, defines constants
├── requirements.txt     # Python dependencies
├── .env                 # API keys — NEVER read, edit, or commit this file
├── .env.example         # Safe template showing required variable names only
├── .gitignore           # Excludes .env, venv/, __pycache__
├── README.md            # Setup guide, architecture diagram, sample output
├── sample_output/
│   └── AAPL_brief.txt   # Example output committed to repo for portfolio
└── tools/
    ├── __init__.py      # Exports all tool functions
    ├── price.py         # get_stock_price(ticker)
    ├── news.py          # get_company_news(ticker)
    ├── fundamentals.py  # get_fundamentals(ticker)
    ├── ratings.py       # get_analyst_ratings(ticker)
    └── technicals.py    # calculate_technicals(ticker)
```

---

## The Agentic Loop — Core Architecture

The heart of this project is the agentic loop in agent.py. Understand this
before touching that file:

```
1. Send user message + tool definitions to Claude API
2. Claude responds with stop_reason == 'tool_use' (wants to call a tool)
   OR stop_reason == 'end_turn' (has enough info, ready to write the brief)
3. If tool_use: call the matching Python function, append result to messages
4. If end_turn: pass Claude's text to formatter.py and print the brief
5. Repeat with MAX_ITERATIONS = 10 as a safety guard against infinite loops
```

The messages list must carry the full conversation history on every API call.
Never clear or reset messages mid-loop.

---

## Tool Conventions

Every tool function in tools/ must follow these rules without exception:

**Success return format:**
```python
return {
    "status": "success",
    "ticker": ticker,
    # ... data fields specific to this tool
}
```

**Error return format:**
```python
return {
    "status": "error",
    "ticker": ticker,
    "message": "Human-readable explanation of what went wrong"
}
```

**Never raise exceptions from tool functions.** Always catch exceptions with
try/except and return an error dictionary instead. Claude handles error dicts
gracefully; uncaught exceptions crash the agent loop.

---

## Coding Conventions

- **Comments are mandatory.** Every function needs a docstring. Every non-obvious
  line needs an inline comment. This is a learning project — the code must teach.
- **Never hardcode API keys.** Always load from environment variables via config.py.
- **Never print from tool functions.** Tools return data; formatter.py handles display.
- **Keep functions small and single-purpose.** One tool, one file, one job.
- **Use descriptive variable names.** Avoid single-letter variables except in
  list comprehensions.
- **Python version:** use f-strings (not .format()), use pathlib where relevant.

---

## API Keys and Environment Variables

Required variables in .env:

```
ANTHROPIC_API_KEY=your_key_here
NEWS_API_KEY=your_key_here
```

- .env is in .gitignore and must NEVER be committed to GitHub
- .env.example contains only the variable names with placeholder values — this
  file IS committed to GitHub so others know what keys are required
- Always load keys through config.py using python-dotenv, never os.getenv() directly
  in tool files

---

## Constants (defined in config.py)

```python
MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 10
NEWS_RESULTS_LIMIT = 4
REQUEST_TIMEOUT_SECONDS = 10
```

Do not hardcode these values anywhere else in the codebase. Always import
from config.py.

---

## What Is In Scope (V1)

- Single US-listed equity per run (NYSE, NASDAQ)
- CLI interface only — no web UI, no Telegram bot
- Five tools only: price, news, fundamentals, ratings, technicals
- Free API tiers only — no paid data subscriptions
- Text output to terminal — no PDF or email delivery

Do not add features outside this scope without being explicitly asked to.

---

## Current Build Phase

Update this line as each phase is completed:

**Current phase: [x] 1  [x] 2  [x] 3  [x] 4  [ ] 5  [ ] 6  [ ] 7  [ ] 8**

---

## Git Workflow Reminder

After every phase:
```bash
git status        # Confirm .env is NOT in the file list before proceeding
git add .
git commit -m "Phase N complete: description"
git push origin main
```

If .env appears in git status output — STOP. Fix .gitignore before committing.
