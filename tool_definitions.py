# Defines the tool schemas passed to the Claude API (name, description, input_schema).
# Each tool here corresponds to an implementation in the tools/ package.

# What is JSON Schema?
# JSON Schema is a standard format for describing the shape of a JSON object —
# what fields it has, what types those fields are, and which ones are required.
# It is the universal language APIs use to document data structures.
#
# Why does Claude need these definitions?
# Claude cannot see our Python source code. Before it can call a tool, it needs
# to know three things: (1) the tool's name so it can reference it, (2) a
# description written in plain English so it understands WHAT the tool does,
# WHEN to call it, and WHAT data it returns, and (3) the input_schema so it
# knows what arguments to pass and in what format.
#
# The description is the most important field. Claude reads it to decide which
# tool to call and in what order. A vague description ("gets stock info") leads
# to poor decisions; a specific description that lists the exact output fields
# lets Claude reason about what it will receive before it even calls the tool.
#
# The input_schema follows the JSON Schema draft-07 spec. "type": "object"
# means the input is a key-value map. "properties" lists each accepted key.
# "required" lists keys Claude must always provide (never leave optional).

TOOLS = [
    # --- get_stock_price ---
    # The description lists every field Claude will receive in the response.
    # This is deliberate: Claude reasons ahead. If it knows it will get
    # week_52_high and week_52_low, it can plan to use them in context
    # (e.g. "the stock is trading near its 52-week low"). Without that
    # foreknowledge, Claude might call a second tool to fetch data it already
    # has, wasting iterations of the agentic loop.
    {
        "name": "get_stock_price",
        "description": (
            "Fetches the current market price snapshot for a US-listed stock ticker. "
            "Returns: current_price (latest trade price in USD), day_high and day_low "
            "(intraday range for the current session), week_52_high and week_52_low "
            "(rolling one-year range to contextualise where price sits historically), "
            "and volume (shares traded in the current session). "
            "Call this first — it establishes the baseline price context that every "
            "other tool's output should be interpreted against."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": (
                        "The stock ticker symbol, e.g. 'AAPL', 'MSFT', 'TSLA'. "
                        "Upper or lower case is accepted."
                    ),
                }
            },
            "required": ["ticker"],
        },
    },

    # --- get_company_news ---
    # The description names the list key ("articles") and its sub-fields so
    # Claude knows it will receive a list of dicts, not a flat structure.
    # Naming the fields (title, description, source, published_at, url) tells
    # Claude what it can quote or summarise without having to guess field names
    # from a raw blob. The word "sentiment" cues Claude to use this tool for
    # qualitative signal rather than quantitative data.
    {
        "name": "get_company_news",
        "description": (
            "Fetches the most recent English-language news articles about a stock ticker "
            "from thousands of sources via NewsAPI. "
            "Returns: total_results (total articles found in the index) and articles "
            "(a list of up to 5 items, each containing title, description, source, "
            "published_at in ISO 8601 format, and url). "
            "Use this to assess recent sentiment, identify material events (earnings, "
            "lawsuits, product launches, leadership changes), and surface risks or "
            "catalysts not visible in price or fundamental data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": (
                        "The stock ticker symbol, e.g. 'AAPL', 'MSFT', 'TSLA'. "
                        "Upper or lower case is accepted."
                    ),
                }
            },
            "required": ["ticker"],
        },
    },

    # --- get_fundamentals ---
    # Fundamental data is the most field-rich tool. Listing all fields in the
    # description prevents Claude from calling another tool to look up something
    # (like market_cap or sector) that this tool already provides. The phrase
    # "company identity" groups the non-numeric fields so Claude understands
    # they serve a different purpose than the valuation ratios.
    {
        "name": "get_fundamentals",
        "description": (
            "Fetches key fundamental financial data for a stock ticker via Yahoo Finance. "
            "Returns company identity fields: company_name, sector, and industry. "
            "Returns valuation fields: market_cap (USD), pe_ratio (trailing twelve months), "
            "forward_pe (next twelve months estimate), and eps (trailing earnings per share in USD). "
            "Returns financial health fields: revenue (trailing twelve months in USD), "
            "profit_margin (net income / revenue as a decimal, e.g. 0.25 = 25%), "
            "dividend_yield (annual yield as a decimal; None if no dividend is paid), "
            "and beta (volatility relative to the market; 1.0 = market rate). "
            "Use this to evaluate whether the stock is cheap or expensive relative to "
            "earnings, how profitable the business is, and how risky it is compared to "
            "the broader market."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": (
                        "The stock ticker symbol, e.g. 'AAPL', 'MSFT', 'TSLA'. "
                        "Upper or lower case is accepted."
                    ),
                }
            },
            "required": ["ticker"],
        },
    },

    # --- get_analyst_ratings ---
    # The description explains the recommendation_mean scale (1–5) because
    # Claude cannot infer the direction of the scale from the name alone.
    # Without this, Claude might misread a score of 2.1 as "slightly bearish"
    # when it actually means "closer to strong buy than buy". The caveat about
    # ETFs and small-caps tells Claude what to do if the tool returns an error:
    # it is not a bug, just a data gap it should note in the brief.
    {
        "name": "get_analyst_ratings",
        "description": (
            "Fetches Wall Street analyst consensus ratings and 12-month price targets "
            "for a stock ticker via Yahoo Finance. "
            "Returns: number_of_analysts (count of analysts covering the stock), "
            "recommendation (consensus label: 'strong_buy', 'buy', 'hold', 'sell', or 'strong_sell'), "
            "recommendation_mean (numeric average on a 1–5 scale where 1 = strong buy "
            "and 5 = strong sell — a lower number is more bullish), "
            "target_price_mean (average 12-month price target in USD), "
            "target_price_median (median target, less skewed by outliers than the mean), "
            "target_price_high and target_price_low (most bullish and bearish individual targets). "
            "Note: ETFs, very small-cap stocks, and recently listed companies often have "
            "no analyst coverage — the tool returns an error in those cases."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": (
                        "The stock ticker symbol, e.g. 'AAPL', 'MSFT', 'TSLA'. "
                        "Upper or lower case is accepted."
                    ),
                }
            },
            "required": ["ticker"],
        },
    },

    # --- calculate_technicals ---
    # The description explains the signal values ("golden_cross", "death_cross",
    # "insufficient_data") explicitly, because these are domain-specific strings
    # Claude must interpret correctly to write a useful research brief. It also
    # explains what price_vs_ma_50_pct sign means (+ = above, - = below) so
    # Claude can translate the number into plain English without guessing.
    {
        "name": "calculate_technicals",
        "description": (
            "Computes 50-day and 200-day simple moving averages (SMA) from one year "
            "of daily closing prices fetched via Yahoo Finance. "
            "Returns: current_price (most recent closing price), trading_days_available "
            "(number of data points used — fewer than 200 means the 200-day SMA is None), "
            "ma_50 (average closing price over the last 50 trading days), "
            "ma_200 (average closing price over the last 200 trading days), "
            "price_vs_ma_50_pct and price_vs_ma_200_pct (how far current price sits above "
            "or below each MA as a percentage — positive means above, negative means below), "
            "and signal: 'golden_cross' if the 50-day MA is above the 200-day MA (bullish "
            "trend), 'death_cross' if below (bearish trend), or 'insufficient_data' if "
            "there is not enough history to compute both MAs. "
            "Use this to assess price trend direction and momentum."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": (
                        "The stock ticker symbol, e.g. 'AAPL', 'MSFT', 'TSLA'. "
                        "Upper or lower case is accepted."
                    ),
                }
            },
            "required": ["ticker"],
        },
    },
]
