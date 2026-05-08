# Retrieves recent news headlines and summaries for a given stock ticker.
# Results are used by the agent to assess sentiment and material events.

# NewsAPI is a REST API (newsapi.org) that aggregates articles from thousands
# of news sources and blogs worldwide. It requires a free API key (set as
# NEWSAPI_API_KEY in .env). We use the /v2/everything endpoint, which searches
# the full article index by keyword and returns a ranked list of articles with
# headline, source, published date, description, and URL. Requests are made
# with the `requests` library directly — no NewsAPI SDK is needed.

import requests

from config import NEWS_API_KEY

NEWSAPI_EVERYTHING_URL = "https://newsapi.org/v2/everything"

# Number of articles to return per call. Kept low to stay within the agent's
# context window and avoid overwhelming the model with raw text.
MAX_ARTICLES = 5


def get_company_news(ticker: str) -> dict:
    """Return recent news articles for the given ticker symbol.

    Returns a dict with status='ok' and an articles list on success, or
    status='error' and a message field if the ticker is invalid or
    data is unavailable.
    """
    # Normalise the ticker so "aapl" and "AAPL" both work.
    ticker = ticker.strip().upper()

    try:
        # Build the query params. Using the ticker as the search term works well
        # for most US equities; for better precision callers can combine the
        # ticker with a company name (e.g. "AAPL Apple").
        params = {
            "q": ticker,
            "language": "en",
            # Sort by publication date so we always get the freshest articles.
            "sortBy": "publishedAt",
            "pageSize": MAX_ARTICLES,
            # NewsAPI requires the key as a query param or Authorization header.
            "apiKey": NEWS_API_KEY,
        }

        response = requests.get(NEWSAPI_EVERYTHING_URL, params=params, timeout=10)

        # NewsAPI returns non-2xx status codes for auth failures (401) and
        # rate limit breaches (429), so we raise here to surface those clearly.
        response.raise_for_status()

        data = response.json()

        # NewsAPI signals application-level errors via status='error' in the
        # body even when the HTTP status is 200, so we check for both.
        if data.get("status") != "ok":
            return {
                "status": "error",
                "ticker": ticker,
                "message": data.get("message", "NewsAPI returned an unknown error."),
            }

        articles = data.get("articles", [])

        # An empty article list means no coverage was found, not an API error.
        if not articles:
            return {
                "status": "error",
                "ticker": ticker,
                "message": f"No news articles found for '{ticker}'.",
            }

        return {
            "status": "ok",
            "ticker": ticker,
            # Total matches in the NewsAPI index — may be far larger than
            # MAX_ARTICLES; this gives the agent a sense of coverage volume.
            "total_results": data.get("totalResults", 0),
            # Each article is trimmed to the fields most useful for the agent.
            "articles": [
                {
                    # Name of the outlet that published the article.
                    "source": article.get("source", {}).get("name"),
                    # Short headline; used by the agent as the primary signal.
                    "title": article.get("title"),
                    # One-sentence summary provided by the source.
                    "description": article.get("description"),
                    # ISO 8601 publication timestamp for recency judgement.
                    "published_at": article.get("publishedAt"),
                    # Direct link so the agent or user can read the full piece.
                    "url": article.get("url"),
                }
                for article in articles
            ],
        }

    except requests.HTTPError as exc:
        # Raised by raise_for_status() for 4xx/5xx responses.
        return {
            "status": "error",
            "ticker": ticker,
            "message": f"NewsAPI request failed: {exc}",
        }

    except Exception as exc:
        # Catches network errors, timeouts, JSON parse failures, or unexpected
        # NewsAPI changes — mirrors the broad guard in price.py.
        return {
            "status": "error",
            "ticker": ticker,
            "message": f"Failed to fetch news data: {exc}",
        }
