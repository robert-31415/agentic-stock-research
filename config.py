# Loads and exposes configuration values from environment variables and .env.
# Single source of truth for API keys, model name, and runtime settings.

# python-dotenv reads the .env file and injects its key-value pairs into
# os.environ before any other code runs. Calling load_dotenv() at import time
# means every module that imports from config.py gets populated env vars
# automatically, with no manual setup required in main.py or agent.py.

import os

from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    """Return the value of an env var, raising clearly if it is missing."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            "Copy .env.example to .env and fill in your values."
        )
    return value


# --- Required ---

# Anthropic API key — must be set or the agent cannot run at all.
ANTHROPIC_API_KEY: str = _require("ANTHROPIC_API_KEY")

# Claude model used for all agent calls. Pinning to a specific version keeps
# behaviour reproducible across updates to the Anthropic model lineup.
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# --- Optional (tools degrade gracefully when these are absent) ---

# Free key from newsapi.org — required only when get_company_news() is called.
NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")

# Alpha Vantage key — reserved for future fundamentals/technicals tools.
ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")

# Finnhub key — reserved for future ratings/analyst tools.
FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")
