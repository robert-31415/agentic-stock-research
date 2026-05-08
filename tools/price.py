# Fetches current and historical price data for a given stock ticker.
# Returns OHLCV data and the latest quote.

# yfinance is an open-source Python library that wraps Yahoo Finance's unofficial
# API. It lets you download market data (quotes, history, fundamentals, options)
# for any ticker Yahoo Finance supports without an API key. Under the hood it
# makes HTTP requests to Yahoo's endpoints and parses the JSON/HTML responses.
# We use the Ticker object's `.info` dict, which contains a snapshot of the
# instrument's current market data fetched in a single network call.

import yfinance as yf


def get_stock_price(ticker: str) -> dict:
    """Return a price snapshot for the given ticker symbol.

    Returns a dict with status='ok' and price fields on success, or
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
                    f"No price data found for '{ticker}'. "
                    "The ticker may be invalid or delisted."
                ),
            }

        return {
            "status": "ok",
            "ticker": ticker,
            # The price of the most recent trade during regular market hours.
            "current_price": info.get("regularMarketPrice"),
            # Intraday high and low for the current (or most recent) session.
            "day_high": info.get("regularMarketDayHigh"),
            "day_low": info.get("regularMarketDayLow"),
            # Rolling 52-week range — useful for context on where price sits
            # relative to its annual trading range.
            "week_52_high": info.get("fiftyTwoWeekHigh"),
            "week_52_low": info.get("fiftyTwoWeekLow"),
            # Number of shares traded in the current session.
            "volume": info.get("regularMarketVolume"),
        }

    except Exception as exc:
        # Catches network errors, unexpected API changes, or yfinance bugs.
        return {
            "status": "error",
            "ticker": ticker,
            "message": f"Failed to fetch price data: {exc}",
        }
