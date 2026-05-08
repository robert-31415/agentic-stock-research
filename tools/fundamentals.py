# Pulls fundamental financial data: revenue, earnings, P/E ratio, market cap, etc.
# Used by the agent to evaluate company health and valuation.

# yfinance is an open-source Python library that wraps Yahoo Finance's unofficial
# API. It lets you download market data (quotes, history, fundamentals, options)
# for any ticker Yahoo Finance supports without an API key. Under the hood it
# makes HTTP requests to Yahoo's endpoints and parses the JSON/HTML responses.
# We use the Ticker object's `.info` dict, which contains a snapshot of the
# instrument's fundamental data fetched in a single network call.

import yfinance as yf


def get_fundamentals(ticker: str) -> dict:
    """Return key fundamental financial data for the given ticker symbol.

    Returns a dict with status='ok' and fundamental fields on success, or
    status='error' and a message field if the ticker is invalid or
    data is unavailable.
    """
    # Normalise the ticker so "aapl" and "AAPL" both work.
    ticker = ticker.strip().upper()

    try:
        # yf.Ticker() is lazy — it does not make a network call here.
        # The actual HTTP request happens when we access .info below.
        stock = yf.Ticker(ticker)

        # .info returns a dict with ~100+ fields. The call raises no exception
        # for an invalid ticker; instead it returns a minimal dict (often just
        # {"trailingPegRatio": None}), so we validate by checking a field that
        # every real equity has.
        info = stock.info

        # Yahoo Finance returns this key for every valid instrument.
        # Its absence is the most reliable signal that the ticker doesn't exist.
        if "regularMarketPrice" not in info or info["regularMarketPrice"] is None:
            return {
                "status": "error",
                "ticker": ticker,
                "message": (
                    f"No fundamental data found for '{ticker}'. "
                    "The ticker may be invalid or delisted."
                ),
            }

        return {
            "status": "ok",
            "ticker": ticker,
            # Human-readable company name, e.g. "Apple Inc."
            "company_name": info.get("longName"),
            # Broad economic sector, e.g. "Technology".
            "sector": info.get("sector"),
            # Narrower industry classification, e.g. "Consumer Electronics".
            "industry": info.get("industry"),
            # Total market value of outstanding shares in USD.
            "market_cap": info.get("marketCap"),
            # Trailing twelve-month price-to-earnings ratio; None for
            # companies with negative earnings.
            "pe_ratio": info.get("trailingPE"),
            # Forward P/E based on next twelve months' estimated earnings.
            "forward_pe": info.get("forwardPE"),
            # Trailing twelve-month earnings per share in USD.
            "eps": info.get("trailingEps"),
            # Total revenue over the trailing twelve months in USD.
            "revenue": info.get("totalRevenue"),
            # Net income divided by revenue; expressed as a decimal (0.25 = 25%).
            "profit_margin": info.get("profitMargins"),
            # Annual dividend yield as a decimal (0.02 = 2%); None if no
            # dividend is paid.
            "dividend_yield": info.get("dividendYield"),
            # Beta measures volatility relative to the market (1.0 = market).
            # Values above 1 indicate higher volatility than the broad index.
            "beta": info.get("beta"),
        }

    except Exception as exc:
        # Catches network errors, unexpected API changes, or yfinance bugs.
        return {
            "status": "error",
            "ticker": ticker,
            "message": f"Failed to fetch fundamental data: {exc}",
        }
