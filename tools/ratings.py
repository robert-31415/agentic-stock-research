# Fetches analyst ratings, price targets, and consensus recommendations.
# Aggregates buy/hold/sell counts and average target price.

# yfinance is an open-source Python library that wraps Yahoo Finance's unofficial
# API. It lets you download market data (quotes, history, fundamentals, options)
# for any ticker Yahoo Finance supports without an API key. Under the hood it
# makes HTTP requests to Yahoo's endpoints and parses the JSON/HTML responses.
# We use the Ticker object's `.info` dict, which contains a snapshot of the
# instrument's analyst consensus data fetched in a single network call.

import yfinance as yf


def get_analyst_ratings(ticker: str) -> dict:
    """Return analyst consensus ratings and price targets for the given ticker.

    Returns a dict with status='ok' and ratings fields on success, or
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
                    f"No data found for '{ticker}'. "
                    "The ticker may be invalid or delisted."
                ),
            }

        # Not every valid ticker has analyst coverage — ETFs, small-caps, and
        # recently listed companies often have no Wall Street coverage at all.
        # numberOfAnalystOpinions being absent or zero signals this cleanly.
        num_analysts = info.get("numberOfAnalystOpinions")
        if not num_analysts:
            return {
                "status": "error",
                "ticker": ticker,
                "message": (
                    f"No analyst coverage found for '{ticker}'. "
                    "The stock may be an ETF, too small, or too recently listed."
                ),
            }

        return {
            "status": "ok",
            "ticker": ticker,
            # Number of analysts contributing to the consensus figures below.
            "number_of_analysts": num_analysts,
            # Plain-English consensus label: "buy", "hold", "sell",
            # "strong_buy", or "strong_sell". Sourced directly from Yahoo.
            "recommendation": info.get("recommendationKey"),
            # Numeric mean of all analyst ratings on Yahoo's 1–5 scale where
            # 1 = strong buy and 5 = strong sell. Useful for trend tracking.
            "recommendation_mean": info.get("recommendationMean"),
            # Consensus 12-month price target — the average across all analysts.
            "target_price_mean": info.get("targetMeanPrice"),
            # Median target; less sensitive to outlier high/low estimates
            # than the mean, so often a more stable central tendency.
            "target_price_median": info.get("targetMedianPrice"),
            # Most bullish and bearish individual analyst targets on record.
            "target_price_high": info.get("targetHighPrice"),
            "target_price_low": info.get("targetLowPrice"),
        }

    except Exception as exc:
        # Catches network errors, unexpected API changes, or yfinance bugs.
        return {
            "status": "error",
            "ticker": ticker,
            "message": f"Failed to fetch analyst ratings: {exc}",
        }
