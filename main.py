# Entry point for the agentic-stock-researcher CLI.
# Parses user input, starts the research agent, and prints formatted results.
# This file does only two things: validate input and hand off to agent.py.
# All research logic lives in agent.py — keep it that way.

import argparse
import re

from agent import run_agent


def validate_ticker(ticker: str) -> str:
    """Return the ticker uppercased if it looks valid, otherwise raise argparse error.

    Valid tickers are 1–5 letters (A–Z). Numbers, dots, and hyphens used by
    some exchanges (e.g. BRK.B) are intentionally excluded for now — this app
    targets standard US exchange tickers only.
    """
    # Convert to uppercase so the user can type 'aapl' or 'AAPL' interchangeably.
    ticker = ticker.strip().upper()

    # re.fullmatch checks that the ENTIRE string matches the pattern, not just
    # a substring. [A-Z]{1,5} means "one to five letters A through Z, nothing
    # else". This rejects empty strings, numbers, spaces, and symbols.
    if not re.fullmatch(r"[A-Z]{1,5}", ticker):
        # argparse.ArgumentTypeError causes argparse to print a clean "error:"
        # message and exit with code 2, which is the standard Unix convention
        # for a command-line usage error.
        raise argparse.ArgumentTypeError(
            f"'{ticker}' is not a valid ticker symbol. "
            "Please use 1–5 letters only (e.g. AAPL, MSFT, TSLA)."
        )

    return ticker


def main():
    # argparse is Python's standard library for parsing command-line arguments.
    # It automatically generates --help output and handles missing arguments.
    parser = argparse.ArgumentParser(
        prog="stock-researcher",
        description="Autonomously research a US stock ticker using AI.",
    )

    # Add a positional argument called 'ticker'. Positional means the user
    # does not need to type a flag — they just run: python main.py AAPL
    # The 'type' parameter points to our validator, so argparse calls
    # validate_ticker() on the raw string before we ever see it in main().
    parser.add_argument(
        "ticker",
        type=validate_ticker,
        help="Stock ticker symbol to research (e.g. AAPL, MSFT, TSLA).",
    )

    # Parse the arguments the user typed. If 'ticker' is missing or invalid,
    # argparse prints an error and exits automatically — we never reach the
    # code below in that case.
    args = parser.parse_args()

    print(f"Researching {args.ticker} — this may take a few seconds...\n")

    # Hand off to the agentic loop. run_agent() drives all the Claude API calls
    # and tool executions and returns Claude's final research brief as a string.
    brief = run_agent(args.ticker)

    # Print the finished brief. A trailing newline keeps the terminal prompt
    # on its own line after the output.
    print(brief)


if __name__ == "__main__":
    # This block only runs when the file is executed directly (python main.py).
    # It does NOT run when main.py is imported by another module, which prevents
    # side effects during testing or future imports.
    main()
