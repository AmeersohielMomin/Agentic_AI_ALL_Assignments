"""
compare_planners.py — Run all three planners with inject_failure=True and
print a comparison table.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from cot_planner import ChainOfThoughtPlanner
from tot_planner import TreeOfThoughtPlanner
from react_workflow import ReActTravelPlanner, reset_travel_tool_state


def run_cot() -> dict:
    planner = ChainOfThoughtPlanner()
    results = planner.execute_plan(inject_failure=True)
    completed = all(r["status"] == "SUCCESS" for r in results)
    steps = len(results)
    failed = any(r["status"] == "FAILED" for r in results)
    return {
        "completed_successfully": completed,
        "handled_dynamic_failure": False,   # CoT cannot replan
        "steps_taken": steps,
        "replanning_events": 0,
        "trace_saved": os.path.isfile(
            os.path.join(os.path.dirname(__file__), "traces", "cot_trace.txt")
        ),
    }


def run_tot() -> dict:
    planner = TreeOfThoughtPlanner()
    result = planner.search(inject_failure=True)
    return {
        "completed_successfully": result["completed_successfully"],
        "handled_dynamic_failure": result["backtrack_count"] > 0,
        "steps_taken": len(result["nodes_explored"]),
        "replanning_events": result["backtrack_count"],
        "trace_saved": os.path.isfile(
            os.path.join(os.path.dirname(__file__), "traces", "tot_trace.txt")
        ),
    }


def run_react() -> dict:
    reset_travel_tool_state()
    planner = ReActTravelPlanner()
    planner.run()
    return {
        "completed_successfully": planner.state.get("itinerary") is not None,
        "handled_dynamic_failure": planner.replan_count > 0,
        "steps_taken": len(planner.history),
        "replanning_events": planner.replan_count,
        "trace_saved": os.path.isfile(
            os.path.join(os.path.dirname(__file__), "traces", "react_trace.txt")
        ),
    }


# ---------------------------------------------------------------------------

def fmt_bool(b: bool) -> str:
    return "Yes" if b else "No"


def print_comparison(cot: dict, tot: dict, react: dict) -> None:
    metrics = [
        ("Completed successfully",   "completed_successfully",   fmt_bool),
        ("Handled dynamic failure",  "handled_dynamic_failure",  fmt_bool),
        ("Steps taken",              "steps_taken",              str),
        ("Replanning events",        "replanning_events",        str),
        ("Trace saved",              "trace_saved",              fmt_bool),
    ]

    col_w = 28
    val_w = 7

    border = "+" + "-" * col_w + "+" + ("-" * val_w + "+") * 3
    header = f"| {'Metric':<{col_w-1}}| {'CoT':^{val_w-1}} | {'ToT':^{val_w-1}} | {'ReAct':^{val_w-1}} |"

    print("\n\n" + "=" * 70)
    print("  PLANNER COMPARISON (inject_failure=True)")
    print("=" * 70)
    print(border)
    print(header)
    print(border)
    for label, key, fmt in metrics:
        cv = fmt(cot[key])
        tv = fmt(tot[key])
        rv = fmt(react[key])
        print(f"| {label:<{col_w-1}}| {cv:^{val_w-1}} | {tv:^{val_w-1}} | {rv:^{val_w-1}} |")
    print(border)

    print("\n📌 Key insight:")
    print("   CoT: linear; fails hard at step 4 (no fallback).")
    print("   ToT: explores alternatives upfront; backtracks elegantly.")
    print("   ReAct: adapts mid-execution via Thought+Action loop; most realistic.")
    print()


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "█" * 70)
    print("  RUNNING CoT PLANNER")
    print("█" * 70)
    cot_stats = run_cot()

    print("\n" + "█" * 70)
    print("  RUNNING ToT PLANNER")
    print("█" * 70)
    tot_stats = run_tot()

    print("\n" + "█" * 70)
    print("  RUNNING ReAct PLANNER")
    print("█" * 70)
    react_stats = run_react()

    print_comparison(cot_stats, tot_stats, react_stats)
