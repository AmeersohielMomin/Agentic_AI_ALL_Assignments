"""
live_demo_critique.py — Experiment 08
Interactive CLI showing a flawed ReAct trace vs an improved trace,
followed by group discussion points.

Run:
    python live_demo_critique.py
"""

import sys
import time


def _banner(title: str, char: str = "═") -> None:
    print("\n" + char * 70)
    print(f"  {title}")
    print(char * 70 + "\n")


def _step(label: str, content: str, delay: float = 0.0) -> None:
    print(f"  [{label}] {content}")
    if delay:
        time.sleep(delay)


def print_flawed_trace() -> None:
    _banner("FLAWED REACT TRACE — Agent Stuck in Tool Loop", "▓")

    trace = [
        ("Thought 1",
         "I need to find the current price of Paracetamol 500mg at City Hospital."),
        ("Action 1",
         "search_tool(query='Paracetamol 500mg price City Hospital')"),
        ("Observation 1",
         "Results: 'Paracetamol tablets, 500mg, Rs. 2.50 per strip (general)'. "
         "[Confidence: 42%] — generic result, hospital-specific price unclear."),
        ("Thought 2",
         "The result is generic. Let me search again with more detail."),
        ("Action 2",
         "search_tool(query='Paracetamol 500mg price City Hospital pharmacy 2024')"),
        ("Observation 2",
         "Results: 'Paracetamol tablets, 500mg, approximately Rs. 2.50'. "
         "[Confidence: 38%] — still generic, no hospital-specific data."),
        ("Thought 3",
         "Still not specific enough. Let me try a slightly different query."),
        ("Action 3",
         "search_tool(query='City Hospital pharmacy Paracetamol tablet cost 500mg')"),
        ("Observation 3",
         "Results: 'Common analgesic, widely available, Rs. 2-3 per strip'. "
         "[Confidence: 35%] — decreasing confidence. No hospital data found."),
        ("Thought 4",
         "I need the exact hospital price. Let me search again."),
        ("Action 4",
         "search_tool(query='Paracetamol 500mg City Hospital 2024 pharmacy price INR')"),
        ("Observation 4",
         "Results: Similar to previous — generic price range only. "
         "[Confidence: 32%]"),
        ("Thought 5",
         "One more search should get me the answer."),
        ("Action 5",
         "search_tool(query='500mg Paracetamol price hospital India')"),
        ("Observation 5",
         "Results: Generic pharmaceutical pricing data only. "
         "[Confidence: 29%] — Confidence declining each step."),
        ("Thought 6",
         "I still don't have the exact price. Let me search one more time..."),
        ("⚠ INFINITE LOOP DETECTED",
         "Agent has called search_tool 5 times with near-identical queries. "
         "NO progress. System terminated agent after loop timeout."),
    ]

    for label, content in trace:
        _step(label, content)

    print("\n  ─────────────────────────────────────────────────────────")
    print("  WHAT IS WRONG WITH THIS TRACE:")
    print("  ─────────────────────────────────────────────────────────")
    problems = [
        ("Problem 1 — No loop detection",
         "Agent called search_tool 5 times. No check that the last N actions\n"
         "    were identical. A simple deque of recent calls would catch this."),
        ("Problem 2 — No confidence gate",
         "Confidence fell from 42% → 29% across 5 calls. Agent never checked\n"
         "    whether results were improving. Should have branched to alternative\n"
         "    tool after confidence dropped below threshold (e.g. 40%)."),
        ("Problem 3 — No backoff / alternative tool selection",
         "Same tool, same type of query, every step. Agent should have switched\n"
         "    to: ask_database_tool, call_pharmacy_api, or escalate_to_human\n"
         "    after 2 failed search attempts."),
    ]
    for label, detail in problems:
        print(f"\n  [{label}]")
        print(f"    {detail}")


def print_improved_trace() -> None:
    _banner("IMPROVED REACT TRACE — With Loop Detection & Alternative Tools", "▒")

    trace = [
        ("Thought 1",
         "I need to find the current price of Paracetamol 500mg at City Hospital."),
        ("Action 1",
         "search_tool(query='Paracetamol 500mg price City Hospital')"),
        ("Observation 1",
         "Results: Generic — Rs. 2.50 per strip. [Confidence: 42%]"),
        ("Loop Check",
         "recent_actions = [search_tool]. Calls=1. OK to continue."),
        ("Confidence Check",
         "42% < threshold(60%). Confidence low. Trying alternative query."),
        ("Thought 2",
         "Generic result insufficient. Switching to pharmacy_database_tool for "
         "hospital-specific pricing."),
        ("Action 2",
         "pharmacy_database_tool(hospital='City Hospital', drug='Paracetamol', "
         "strength_mg=500)"),
        ("Observation 2",
         "DB Result: Rs. 3.20 per strip of 10 (City Hospital formulary price, "
         "updated 2024-09-01). [Confidence: 91%]"),
        ("Loop Check",
         "recent_actions = [search_tool, pharmacy_database_tool]. "
         "No repeat detected. OK."),
        ("Confidence Check",
         "91% ≥ threshold(60%). Confidence acceptable. Proceeding."),
        ("Thought 3",
         "I now have a reliable, hospital-specific price with high confidence. "
         "I can answer the question."),
        ("Final Answer",
         "The current price of Paracetamol 500mg at City Hospital is "
         "Rs. 3.20 per strip of 10 tablets (formulary price, Sept 2024). ✓"),
    ]

    for label, content in trace:
        _step(label, content)

    print("\n  ─────────────────────────────────────────────────────────")
    print("  WHAT IS BETTER IN THIS TRACE:")
    print("  ─────────────────────────────────────────────────────────")
    improvements = [
        "After 1 failed search (not 5), the agent pivots to an alternative tool.",
        "Confidence check gates the next step — low confidence → branch to better tool.",
        "Recent-actions deque prevents tool call repetition beyond 2 attempts.",
        "Total steps: 2 tool calls instead of 5. 60% more efficient.",
        "Final answer has 91% confidence vs 29% in the flawed trace.",
    ]
    for i, imp in enumerate(improvements, 1):
        print(f"\n    [{i}] {imp}")


def print_group_discussion() -> None:
    _banner("GROUP DISCUSSION POINTS", "░")
    points = [
        (
            "Critique 1 — Loop detection should be architectural, not an afterthought",
            "Every ReAct agent should have a built-in loop counter and similarity\n"
            "  checker as standard infrastructure. It should not be the developer's\n"
            "  responsibility to remember to add it to each agent implementation.",
        ),
        (
            "Critique 2 — Confidence scores need to be first-class citizens",
            "Observations should always return a confidence/reliability score.\n"
            "  The reasoning engine should treat low-confidence observations as\n"
            "  'soft failures' that trigger alternative strategy selection, not\n"
            "  as signals to try the same action again with minor variation.",
        ),
        (
            "Critique 3 — Alternative tool libraries should be pre-planned",
            "Before deployment, each agent should have a documented 'fallback ladder':\n"
            "  Primary tool → Alternative tool 1 → Alternative tool 2 → Human escalation.\n"
            "  Agents that can only do one thing when stuck will always get stuck.",
        ),
    ]
    for label, detail in points:
        print(f"\n  [{label}]")
        print(f"  {detail}")
    print()


if __name__ == "__main__":
    auto = "--auto" in sys.argv or not sys.stdin.isatty()
    print_flawed_trace()
    if not auto:
        input("\n  Press ENTER to see the improved trace...")
    print_improved_trace()
    if not auto:
        input("\n  Press ENTER to see group discussion points...")
    print_group_discussion()
    print("  Demo complete.\n")
