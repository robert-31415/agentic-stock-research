# Entry point for the agentic-stock-researcher CLI.
# Parses user input, starts the research agent, and prints formatted results.
# This file does only two things: validate input and hand off to agent.py.
# All research logic lives in agent.py — keep it that way.

import argparse
import re
import sys

from agent import run_agent
from formatter import print_research_brief


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

    # Wrap the entire agent call so that unexpected crashes (network outage,
    # Anthropic API downtime, unhandled library bug) surface as a clean message
    # instead of a Python traceback. KeyboardInterrupt is separated so the user
    # can always Ctrl-C without seeing a confusing error.
    try:
        # Hand off to the agentic loop. run_agent() drives all the Claude API
        # calls and tool executions and returns Claude's final brief as a string.
        brief = run_agent(args.ticker)

        # Render the brief using the rich-formatted panel layout from formatter.py.
        # print_research_brief() handles the header, body panel, and footer rule.
        print_research_brief(args.ticker, brief)

    except KeyboardInterrupt:
        # The user pressed Ctrl-C mid-run. Exit gracefully with a clear message
        # rather than letting Python dump a KeyboardInterrupt traceback.
        print("\n\nResearch cancelled by user.")
        sys.exit(0)

    except Exception as exc:
        # Catches anything else: Anthropic API auth failures, total network loss,
        # or an unhandled bug in the agent loop. We print the error and exit with
        # code 1 (the Unix convention for a general runtime failure) so scripts
        # that call this CLI can detect the failure via the exit code.
        print(f"\nUnexpected error: {exc}")
        print("If this persists, check your API keys in .env and your network connection.")
        sys.exit(1)


if __name__ == "__main__":
    # This block only runs when the file is executed directly (python main.py).
    # It does NOT run when main.py is imported by another module, which prevents
    # side effects during testing or future imports.
    main()
