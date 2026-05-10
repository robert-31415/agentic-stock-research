# Formats the agent's research brief and status messages for terminal display.
# Uses the 'rich' library, which extends Python's built-in print() with colors,
# borders, styled text, and layout primitives that make CLI output look professional.
#
# How rich works at a high level:
#   - Console  : the main object. All styled output goes through console.print().
#   - Panel    : wraps content in a box with a border, title, and optional padding.
#   - Text     : a string with per-character style information attached.
#   - Rule     : a full-width horizontal divider line.
#   - Markup   : inline style tags inside strings — e.g. "[bold green]hello[/bold green]"

from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

# Console is the central object in rich. Creating one instance at module level
# is the recommended pattern — it lets rich measure the terminal width once and
# reuse that measurement for every print call in this session.
console = Console()


def print_research_brief(ticker: str, brief_text: str) -> None:
    """Render the completed research brief to the terminal using rich panels.

    Displays a green header panel with the ticker and timestamp, followed by
    the brief body in a white panel, and closes with a horizontal rule.

    Args:
        ticker:     The stock ticker symbol (e.g. 'AAPL').
        brief_text: The plain-text research brief returned by the agent loop.
    """
    # --- Header panel ---
    # We build the header as a Text object so we can apply different styles
    # to different segments of the same block of text.
    # Text(justify="center") means all segments will be center-aligned.
    timestamp = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    header_content = Text(justify="center")
    # .append() adds a segment of text with a specific style.
    # Styles are expressed as space-separated keywords: "bold white", "dim", etc.
    header_content.append(f"{ticker.upper()}  ", style="bold white")
    header_content.append("Research Brief", style="bold green")
    header_content.append(f"\n{timestamp}", style="dim white")

    # Panel() draws a box around any renderable object (Text, string, table, etc.).
    #   border_style — color/style of the box lines themselves.
    #   padding      — (top+bottom lines, left+right spaces) of space inside the box.
    console.print(
        Panel(
            header_content,
            border_style="green",
            padding=(1, 4),
        )
    )

    # --- Body panel ---
    # The research brief is long freeform text. We wrap it in a second panel
    # so it sits inside a visible boundary and is easy to scroll through.
    #   overflow="fold" — wraps lines that are too wide instead of truncating them.
    #   expand=True     — stretches the panel to the full terminal width.
    #   padding=(1, 2)  — one blank line top and bottom, two spaces left and right.
    body_text = Text(brief_text, style="white", overflow="fold")

    console.print(
        Panel(
            body_text,
            border_style="dim white",
            padding=(1, 2),
            expand=True,
        )
    )

    # --- Footer rule ---
    # Rule() prints a horizontal line that spans the full terminal width.
    # It provides visual closure after the brief so the shell prompt that
    # follows doesn't run directly into the output.
    console.print(Rule(style="dim green"))


def print_agent_step(tool_name: str) -> None:
    """Print a dim status line showing which tool the agent is about to call.

    Call this immediately before invoking each tool so the user can watch the
    agent work in real time rather than staring at a blank terminal while API
    calls complete.

    Args:
        tool_name: The function name of the tool being called
                   (e.g. 'get_stock_price').
    """
    # Rich markup tags work inline inside any string passed to console.print().
    # Tags are wrapped in square brackets: [dim italic]...[/dim italic]
    #   dim    — reduces brightness, making status lines visually secondary.
    #   italic — distinguishes these lines from regular output at a glance.
    console.print(f"  [dim italic]-> Calling {tool_name}...[/dim italic]")
