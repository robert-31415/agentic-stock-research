# Computes technical indicators (RSI, MACD, moving averages, Bollinger Bands, etc.)
# from historical price data to support trend and momentum analysis.

# yfinance is an open-source Python library that wraps Yahoo Finance's unofficial
# API. It lets you download market data (quotes, history, fundamentals, options)
# for any ticker Yahoo Finance supports without an API key. Under the hood it
# makes HTTP requests to Yahoo's endpoints and parses the JSON/HTML responses.
# We use the Ticker object's `.info` dict to validate the ticker, then its
# `.history()` method to fetch a time series of daily closing prices. The moving
# averages are computed from that series using pandas' built-in rolling mean —
# yfinance returns a pandas DataFrame, so no extra libraries are needed.

import yfinance as yf


def calculate_technicals(ticker: str) -> dict:
    """Return 50-day and 200-day moving averages for the given ticker symbol.

    Returns a dict with status='ok' and technical fields on success, or
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

        # Fetch one year of daily OHLCV bars — 252 trading days, which is just
        # enough to compute a 200-day MA with a small buffer for non-trading
        # days (holidays, weekends already excluded by Yahoo).
        history = stock.history(period="1y")

        # An empty DataFrame here means Yahoo has no price history on record,
        # which can happen for very recently listed instruments.
        if history.empty:
            return {
                "status": "error",
                "ticker": ticker,
                "message": (
                    f"No price history found for '{ticker}'. "
                    "The stock may be too recently listed."
                ),
            }

        close = history["Close"]
        total_days = len(close)

        # A simple moving average (SMA) is the arithmetic mean of closing
        # prices over a rolling window. pandas rolling().mean() slides that
        # window forward one day at a time; we take the final value, which
        # represents the average of the most recent N closing prices.
        ma_50 = round(close.rolling(window=50).mean().iloc[-1], 4) if total_days >= 50 else None
        ma_200 = round(close.rolling(window=200).mean().iloc[-1], 4) if total_days >= 200 else None

        # The most recent closing price is our reference point for the
        # percentage-distance calculations below.
        current_price = round(float(close.iloc[-1]), 4)

        # Percentage distance from the current price to each moving average.
        # A positive value means price is trading above the MA (bullish bias);
        # negative means below (bearish bias). None when the MA cannot be
        # computed because there is insufficient history.
        price_vs_ma_50 = (
            round((current_price - ma_50) / ma_50 * 100, 2) if ma_50 else None
        )
        price_vs_ma_200 = (
            round((current_price - ma_200) / ma_200 * 100, 2) if ma_200 else None
        )

        # A "golden cross" (50-day crosses above 200-day) is a widely watched
        # bullish signal; a "death cross" (50-day crosses below 200-day) is the
        # bearish counterpart. We report the current state, not the crossover
        # event itself, since we only have a snapshot rather than a time series.
        if ma_50 is not None and ma_200 is not None:
            signal = "golden_cross" if ma_50 > ma_200 else "death_cross"
        else:
            signal = "insufficient_data"

        return {
            "status": "ok",
            "ticker": ticker,
            # Latest closing price used as the basis for MA comparisons.
            "current_price": current_price,
            # Number of trading days available — useful for the agent to know
            # when a MA could not be computed due to limited history.
            "trading_days_available": total_days,
            # 50-day simple moving average of closing prices; None if fewer
            # than 50 days of history are available.
            "ma_50": ma_50,
            # 200-day simple moving average of closing prices; None if fewer
            # than 200 days of history are available.
            "ma_200": ma_200,
            # Percentage above (+) or below (−) each moving average.
            "price_vs_ma_50_pct": price_vs_ma_50,
            "price_vs_ma_200_pct": price_vs_ma_200,
            # "golden_cross", "death_cross", or "insufficient_data".
            "signal": signal,
        }

    except Exception as exc:
        # Catches network errors, unexpected API changes, or yfinance bugs.
        return {
            "status": "error",
            "ticker": ticker,
            "message": f"Failed to compute technical indicators: {exc}",
        }
