# Makes tools/ a package and exports a dispatch map used by the agent
# to route tool_use requests to the correct implementation function.

# When Claude decides to call a tool, it sends back the tool's name as a plain
# string (e.g. "get_stock_price"). The agent needs a way to turn that string
# into an actual Python function call. TOOL_FUNCTIONS is a dict that maps each
# tool name string to its corresponding Python function. The agent looks up the
# name, gets the function, and calls it — no if/elif chain needed.

from tools.fundamentals import get_fundamentals
from tools.news import get_company_news
from tools.price import get_stock_price
from tools.ratings import get_analyst_ratings
from tools.technicals import calculate_technicals

# The keys must exactly match the "name" field in each tool definition in
# tool_definitions.py. If they don't match, Claude will ask for a tool that
# the agent cannot find, and the loop will return an "unknown tool" error.
TOOL_FUNCTIONS = {
    "get_stock_price": get_stock_price,
    "get_company_news": get_company_news,
    "get_fundamentals": get_fundamentals,
    "get_analyst_ratings": get_analyst_ratings,
    "calculate_technicals": calculate_technicals,
}
