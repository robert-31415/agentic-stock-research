# 📈 Agentic Stock Researcher

A Python CLI that uses Claude's tool-use API to autonomously research any US stock ticker. Type a symbol and an AI agent automatically calls five data tools — fetching live prices, recent news, fundamental financials, analyst ratings, and technical indicators — then synthesises everything into a plain-English research brief printed directly to your terminal. No manual data gathering, no copy-pasting between tabs. The agent decides which tools to call, in what order, and when it has enough information to write its conclusion, all without any human input between steps.

This project demonstrates **agentic AI**: instead of a single prompt-and-reply, Claude operates in a loop — calling tools, reading their results, reasoning about what to do next, and only stopping when it has produced a complete answer. That loop pattern is the foundation of every serious AI assistant built today.

---

## 🔄 How It Works

```
┌─────────────┐     ticker      ┌─────────────────────────────────────┐
│    User     │ ─────────────▶  │            Agent Loop               │
│ python      │                 │                                     │
│ main.py     │                 │  1. Send message + tool definitions  │
│ AAPL        │                 │  2. Claude picks a tool to call      │
└─────────────┘                 │  3. Python runs the tool             │
                                │  4. Result is added to conversation  │
                                │  5. Repeat until all tools are done  │
                                └──────────────┬──────────────────────┘
                                               │ calls
                          ┌────────────────────▼────────────────────┐
                          │                 Tools                    │
                          │                                         │
                          │  get_stock_price      (yfinance)        │
                          │  get_company_news     (NewsAPI)         │
                          │  get_fundamentals     (yfinance)        │
                          │  get_analyst_ratings  (yfinance)        │
                          │  calculate_technicals (yfinance)        │
                          └────────────────────┬────────────────────┘
                                               │ results
                          ┌────────────────────▼────────────────────┐
                          │            Research Brief                │
                          │   Rendered to terminal with rich        │
                          └─────────────────────────────────────────┘
```

---

## ⚙️ Setup

**1. Clone the repository**
```bash
git clone https://github.com/your-username/agentic-stock-researcher.git
cd agentic-stock-researcher
```

**2. Create and activate a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Create your `.env` file**
```bash
cp .env.example .env
```

**5. Add your API keys to `.env`**
```
ANTHROPIC_API_KEY=your_anthropic_key_here
NEWS_API_KEY=your_newsapi_key_here
```

- **Anthropic API key** — get one at [console.anthropic.com](https://console.anthropic.com)
- **NewsAPI key** — get a free key at [newsapi.org](https://newsapi.org) (free tier supports development use)

---

## 🚀 Usage

```bash
python main.py AAPL
```

Replace `AAPL` with any US-listed ticker symbol (1–5 letters). Examples:

```bash
python main.py MSFT
python main.py TSLA
python main.py NVDA
```

The agent will print each tool call as it runs, then display the finished brief in a formatted terminal panel.

---

## 🛠️ Tools

| Tool | Data Source | What It Returns |
|---|---|---|
| `get_stock_price` | Yahoo Finance | Current price, day range, 52-week range, volume |
| `get_company_news` | NewsAPI | 5 most recent headlines with source and date |
| `get_fundamentals` | Yahoo Finance | Market cap, P/E ratio, EPS, revenue, profit margin, beta |
| `get_analyst_ratings` | Yahoo Finance | Buy/hold/sell consensus, price targets (mean, median, high, low) |
| `calculate_technicals` | Yahoo Finance | 50-day and 200-day moving averages, golden/death cross signal |

---

## 📄 Sample Output

See [`sample_output/AAPL_brief.txt`](sample_output/AAPL_brief.txt) for an example of the research brief this agent produces for Apple Inc.

---

## 🧠 What I Learned

Building this project taught me five core concepts in agentic AI:

1. **The agentic loop** — How an LLM can pause mid-reasoning, request external data via tools, absorb the results, and continue — repeating that cycle autonomously until it reaches a conclusion. This is fundamentally different from a single-shot prompt.

2. **Tool definitions and JSON Schema** — How to describe a Python function to an LLM using a structured schema so the model knows what the tool does, what arguments it expects, and what types those arguments must be.

3. **Conversation state management** — Why the full message history (user messages, assistant replies, and tool results) must be sent on every API call, and how that list acts as the model's working memory across turns.

4. **Structured error handling in agentic systems** — Why tool functions must never raise exceptions, and why returning a consistent `{"status": "error", ...}` dict lets the agent reason about failures gracefully rather than crashing the entire loop.

5. **Prompt design for autonomous agents** — How a system prompt shapes agent behaviour at scale: instructing the model to call every tool exactly once, handle errors without retrying, and write conclusions for non-expert readers — all without any human intervention mid-run.
