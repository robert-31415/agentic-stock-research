# Orchestrates the agentic research loop using the Anthropic SDK.
# Sends messages to Claude, handles tool calls, and manages conversation state.

# What is an "agentic loop"?
# A normal API call is a single round-trip: you send a message, Claude replies,
# done. An agentic loop is different — Claude can pause its reply mid-thought,
# ask for a tool to be run (e.g. "call get_stock_price('AAPL')"), wait for the
# result, then continue reasoning with that new information. This back-and-forth
# repeats until Claude has gathered everything it needs and writes a final answer.
# The loop in this file drives that cycle automatically without any human input.

import json

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from tool_definitions import TOOLS
from tools import TOOL_FUNCTIONS

# Maximum number of times the loop will call the Claude API in a single run.
# This is a safety guard against infinite loops — if Claude keeps requesting
# tools without ever reaching end_turn, the loop stops and returns a notice.
# 10 is generous for 5 tools; in practice Claude usually finishes in 6–7 turns.
MAX_ITERATIONS = 10

# The system prompt defines Claude's role and goals for the entire conversation.
# It is sent on every API call but does not appear in the messages list — the
# Anthropic API keeps it separate so it always anchors Claude's behaviour.
SYSTEM_PROMPT = """You are an expert stock research analyst. The user will give
you a ticker symbol. Your job is to call each of the available tools to gather
price data, recent news, fundamental financials, analyst ratings, and technical
indicators for that ticker. After you have called all the tools, synthesise the
results into a clear, structured research brief written in plain English.

Follow these rules:
- Call every tool exactly once before writing the brief.
- If a tool returns status='error', note the gap in your brief rather than
  retrying — the error is informative in itself.
- Do not ask the user for clarification. Work autonomously with the tools given.
- Write the final brief in a format suitable for a non-expert reader."""


def run_agent(ticker: str) -> str:
    """Run the agentic research loop for the given ticker and return the brief.

    Sends the ticker to Claude, drives the tool-call cycle until Claude reaches
    end_turn, then returns Claude's final text response.
    """
    # Create the Anthropic SDK client. This object manages authentication and
    # sends HTTP requests to the Claude API on our behalf.
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # The messages list is the conversation history. Every message we send and
    # every reply Claude gives must be appended here and sent back on the next
    # API call. Claude has no memory between calls — this list IS its memory.
    # We start with a single user message asking for a research brief.
    messages = [
        {
            "role": "user",
            "content": (
                f"Please research the stock ticker '{ticker.strip().upper()}' "
                "and produce a comprehensive research brief."
            ),
        }
    ]

    # --- The agentic loop ---
    # Each iteration is one round-trip to the Claude API. We keep looping
    # until Claude signals it is done (stop_reason == 'end_turn') or we hit
    # the safety cap.
    for iteration in range(MAX_ITERATIONS):

        # Send the full conversation history plus the tool definitions to Claude.
        # Claude uses the tool definitions to know what tools exist and what
        # arguments each one expects. We must send them on every call.
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # stop_reason tells us why Claude stopped generating:
        #   'end_turn'  — Claude finished its reply and has nothing more to say.
        #   'tool_use'  — Claude wants to call one or more tools before continuing.
        #   'max_tokens'— Claude ran out of token budget mid-reply (rare).

        # --- Branch 1: Claude is done ---
        if response.stop_reason == "end_turn":
            # response.content is a list of content blocks. When Claude writes
            # its final answer the block type is "text". We find it and return it.
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            # Fallback: Claude finished but produced no text (should not happen).
            return "Research complete, but no text was returned by the model."

        # --- Branch 2: Claude wants to call tools ---
        if response.stop_reason == "tool_use":

            # Step A: Append Claude's reply to the conversation history.
            # This reply contains "thinking" text (if any) and one or more
            # tool_use blocks describing which tools Claude wants to call and
            # with what arguments. We must echo it back on the next call so
            # Claude can see its own prior reasoning.
            messages.append({"role": "assistant", "content": response.content})

            # Step B: Execute every tool Claude requested in this turn.
            # Claude can ask for multiple tools in a single response — we run
            # all of them and collect the results before sending anything back.
            tool_results = []

            for block in response.content:
                # Skip text blocks — only act on tool_use blocks.
                if block.type != "tool_use":
                    continue

                tool_name = block.name    # e.g. "get_stock_price"
                tool_input = block.input  # e.g. {"ticker": "AAPL"}
                tool_use_id = block.id    # unique ID Claude gave this request

                # Look up the Python function that matches the tool name.
                # TOOL_FUNCTIONS is the dispatch map imported from tools/__init__.py.
                if tool_name in TOOL_FUNCTIONS:
                    tool_fn = TOOL_FUNCTIONS[tool_name]
                    # Call the function with the arguments Claude provided.
                    # ** unpacks the dict so {"ticker": "AAPL"} becomes
                    # get_stock_price(ticker="AAPL").
                    result = tool_fn(**tool_input)
                else:
                    # Claude asked for a tool that doesn't exist in our map.
                    # Return a clear error rather than crashing the whole loop.
                    result = {
                        "status": "error",
                        "message": f"Unknown tool '{tool_name}'. Check TOOL_FUNCTIONS.",
                    }

                # Convert the result dict to a JSON string. Claude reads tool
                # results as text, so json.dumps() is safer than str() because
                # it handles None → null, booleans, and nested dicts correctly.
                tool_results.append(
                    {
                        "type": "tool_result",
                        # tool_use_id links this result to the specific request
                        # Claude made — required so Claude can match results when
                        # multiple tools were called in the same turn.
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(result),
                    }
                )

            # Step C: Send all tool results back to Claude as a user message.
            # The role is "user" because in the Anthropic API, tool results are
            # always submitted from the user side of the conversation, not the
            # assistant side — even though the results came from our code, not
            # a human. Claude will read these results and continue its reasoning.
            messages.append({"role": "user", "content": tool_results})

            # The loop now repeats: we call the API again with the updated
            # messages list, Claude sees the tool results, and either calls
            # more tools or writes its final brief.
            continue

        # --- Branch 3: Unexpected stop_reason ---
        # Guard against future API changes or edge cases (e.g. 'max_tokens').
        return (
            f"Agent stopped unexpectedly with stop_reason='{response.stop_reason}'. "
            "The research brief could not be completed."
        )

    # --- Loop exhausted ---
    # We reached MAX_ITERATIONS without Claude reaching end_turn. This most
    # likely means Claude kept calling tools without ever writing a conclusion.
    return (
        f"Research incomplete: the agent reached the maximum of {MAX_ITERATIONS} "
        "iterations without finishing. Try running again or increasing MAX_ITERATIONS."
    )
