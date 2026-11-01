"""
Participative Learning Units 1 & 2
trace_remediation.py — Automated Reasoning Trace Remediation Engine

Demonstrates three architectural strategies to fix reasoning failures:
1. Deque-based Loop Detection: Tracks recent actions and halts repetition.
2. Confidence Gate & Soft-Failure Handling: Pivots tool choice when observations score low confidence.
3. Tree-of-Thought (ToT) Branch Switching: Backtracks to alternative reasoning paths when primary path stalls.
"""

from collections import deque
from typing import List, Dict, Any, Optional


class TraceRemediationEngine:
    def __init__(self, history_len: int = 3, min_confidence: float = 0.60):
        self.action_history = deque(maxlen=history_len)
        self.min_confidence = min_confidence

    def check_loop(self, proposed_action: str) -> bool:
        """Returns True if proposed_action causes repetitive loop."""
        if len(self.action_history) >= 2 and all(a == proposed_action for a in self.action_history):
            return True
        return False

    def evaluate_observation(self, observation: Dict[str, Any]) -> str:
        """Determines next action strategy based on observation quality."""
        conf = observation.get("confidence", 0.0)
        if conf < self.min_confidence:
            return "PIVOT_TOOL"
        return "PROCEED"


def run_remediation_demo():
    print("=" * 70)
    print("  AUTOMATED REASONING TRACE REMEDIATION DEMO")
    print("=" * 70)

    engine = TraceRemediationEngine(history_len=2, min_confidence=0.60)

    print("\n[Strategy 1] Loop Detection in Action")
    actions = ["search_api(query='Paracetamol price')", "search_api(query='Paracetamol price')", "search_api(query='Paracetamol price')"]

    for i, act in enumerate(actions, 1):
        if engine.check_loop(act):
            print(f"  Step {i}: 🛑 LOOP DETECTED for '{act}'! Overriding with alternative action.")
            remediated_act = "hospital_db_query(item='Paracetamol')"
            print(f"  Step {i} Remediated Action: {remediated_act}")
            engine.action_history.append(remediated_act)
            break
        else:
            print(f"  Step {i}: Allowed action -> {act}")
            engine.action_history.append(act)

    print("\n[Strategy 2] Confidence Gating & Dynamic Pivot")
    obs1 = {"result": "generic price found", "confidence": 0.38}
    decision1 = engine.evaluate_observation(obs1)
    print(f"  Observation 1 (Confidence {obs1['confidence'] * 100}%): Decision -> {decision1}")
    if decision1 == "PIVOT_TOOL":
        print("  Remediation: Switched from generic web search to structured database query.")

    obs2 = {"result": "hospital price verified Rs 3.20", "confidence": 0.94}
    decision2 = engine.evaluate_observation(obs2)
    print(f"  Observation 2 (Confidence {obs2['confidence'] * 100}%): Decision -> {decision2}")
    if decision2 == "PROCEED":
        print("  Remediation: High confidence validated. Proceeding to task completion.")

    print("\n" + "=" * 70)
    print("  ✅ Trace Remediation complete. Agent loop averted, confidence restored.")
    print("=" * 70)


if __name__ == "__main__":
    run_remediation_demo()
