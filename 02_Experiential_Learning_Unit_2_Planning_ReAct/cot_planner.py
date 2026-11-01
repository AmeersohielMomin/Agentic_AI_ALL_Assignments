"""
cot_planner.py — Chain-of-Thought (CoT) Travel Itinerary Planner.

Approach: Linear, ordered step-by-step decomposition.
Limitation: Cannot replan when a step fails — execution halts.
"""

import os
import json
from typing import Optional


class ChainOfThoughtPlanner:
    """
    Chain-of-Thought planner for a 3-day business trip to Mumbai.

    CoT strength : Transparent, ordered reasoning.
    CoT weakness : No backtracking — a single failure aborts the whole plan.
    """

    goal = "Plan 3-day business trip to Mumbai within budget Rs 25,000 with client meetings"

    def decompose(self) -> list[str]:
        """Return an ordered list of 8 sub-tasks derived from the goal."""
        return [
            "1. Search available flights to Mumbai (BOM) within budget",
            "2. Check client meeting availability and confirm slots",
            "3. Calculate total budget allocation (flights + hotel + transport + meals)",
            "4. Book hotel near client offices (budget: Rs 4,000/night × 3 nights)",
            "5. Book airport-to-hotel cab/transfer on arrival day",
            "6. Book cab for each client meeting day",
            "7. Reserve meals/restaurant for client dinner",
            "8. Confirm full itinerary and send calendar invites",
        ]

    # ------------------------------------------------------------------
    # Mock execution of each step
    # ------------------------------------------------------------------

    def _run_step(self, step_num: int, step_label: str, inject_failure: bool) -> dict:
        """Simulate executing one step.  Step 4 fails when inject_failure=True."""

        # Simulated step outputs
        outputs = {
            1: {"flight": "AI-665 DEL→BOM", "price_rs": 6800, "duration": "2h 15m"},
            2: {"meetings": ["Mon 10am – Tata Client", "Tue 3pm – HDFC Review"], "status": "confirmed"},
            3: {"flights": 6800, "hotel": 12000, "transport": 2400, "meals": 3600, "total": 24800, "within_budget": True},
            4: {"hotel": "Hotel Trident BKC", "price_per_night_rs": 4000, "status": "booked"},
            5: {"cab": "Ola rental – airport pickup", "fare_rs": 850, "status": "booked"},
            6: {"cab": "Ola daily pass", "fare_rs": 1550, "status": "booked"},
            7: {"restaurant": "Ziya at The Oberoi", "reservation": "Tue 7:30pm", "status": "confirmed"},
            8: {"calendar_invites_sent": 2, "itinerary_pdf": "itinerary_mumbai.pdf", "status": "complete"},
        }

        # Inject failure at step 4 (hotel sold out)
        if inject_failure and step_num == 4:
            return {
                "step": step_num,
                "label": step_label,
                "status": "FAILED",
                "error": "Hotel Trident BKC is fully booked for requested dates.",
                "output": None,
            }

        return {
            "step": step_num,
            "label": step_label,
            "status": "SUCCESS",
            "error": None,
            "output": outputs.get(step_num, {}),
        }

    # ------------------------------------------------------------------
    # Main execution
    # ------------------------------------------------------------------

    def execute_plan(self, inject_failure: bool = False) -> list[dict]:
        """
        Execute steps sequentially.  On failure, stop — CoT has no fallback.
        Returns list of step result dicts.
        """
        steps = self.decompose()
        results: list[dict] = []

        print("=" * 70)
        print("  Chain-of-Thought Planner — Mumbai Business Trip")
        print(f"  Goal : {self.goal}")
        print("=" * 70)

        for i, label in enumerate(steps, start=1):
            result = self._run_step(i, label, inject_failure)
            results.append(result)

            status_icon = "✅" if result["status"] == "SUCCESS" else "❌"
            print(f"\n  {status_icon} Step {i}: {label}")
            if result["status"] == "SUCCESS":
                print(f"      Output: {json.dumps(result['output'], ensure_ascii=False)}")
            else:
                print(f"      ERROR : {result['error']}")
                print("      ⛔  CoT cannot replan — halting execution.")
                break  # CoT stops on first failure

        completed = sum(1 for r in results if r["status"] == "SUCCESS")
        print(f"\n  Steps completed: {completed}/{len(steps)}")
        print(f"  Plan outcome: {'PARTIAL (failed at step 4)' if inject_failure else 'COMPLETE'}\n")

        # Save trace
        traces_dir = os.path.join(os.path.dirname(__file__), "traces")
        os.makedirs(traces_dir, exist_ok=True)
        with open(os.path.join(traces_dir, "cot_trace.txt"), "w", encoding="utf-8") as f:
            f.write(f"Goal: {self.goal}\n\n")
            for r in results:
                f.write(f"Step {r['step']}: {r['label']}\n")
                f.write(f"  Status: {r['status']}\n")
                if r["error"]:
                    f.write(f"  Error : {r['error']}\n")
                if r["output"]:
                    f.write(f"  Output: {json.dumps(r['output'], ensure_ascii=False)}\n")
                f.write("\n")

        return results


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    planner = ChainOfThoughtPlanner()
    planner.execute_plan(inject_failure=True)
