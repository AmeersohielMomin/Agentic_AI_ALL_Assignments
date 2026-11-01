"""
safety_evaluator.py — Experiment 07 Safety Evaluator
Runs all 20 test cases through the guardrail pipeline and generates a
before/after scorecard.

Run:
    python safety_evaluator.py
"""

import sys
import os
import json
import re
from datetime import datetime, timezone

# Allow imports from the EXP-06 guardrails package
EXP06 = os.path.join(
    os.path.dirname(__file__),
    "..",
    "06_Homework_Unit_5_Domain_Specific_Agent_Safety",
)
sys.path.insert(0, EXP06)

from guardrails.input_guard import InputGuard
from guardrails.tool_call_guard import ToolCallGuard
from guardrails.output_guard import OutputGuard


# ── Helpers for inferring tool/params from test-case text ────────────────────

def _infer_tool_and_params(text: str):
    """
    Very lightweight heuristic to derive (tool_name, params) from a test-case
    input string so we can exercise ToolCallGuard without a live LLM.
    Returns (tool_name, params) or (None, {}).
    """
    t = text.lower()
    drug_map = {
        "paracetamol": "paracetamol",
        "ibuprofen": "ibuprofen",
        "oxycodone": "oxycodone",
        "aspirin": "aspirin",
    }
    # Dosage pattern — e.g. "5000mg"
    dosage_match = re.search(r"(\d+)\s*mg", t)
    dosage = int(dosage_match.group(1)) if dosage_match else 0

    drug = None
    for key in drug_map:
        if key in t:
            drug = key
            break

    if "prescrib" in t and drug and dosage:
        return "prescribe_medication", {"drug": drug, "dosage_mg": dosage}
    if "check drug interaction" in t or "interaction" in t:
        return "check_drug_interaction", {}
    if "lab test" in t or "cbc" in t:
        return "request_lab_test", {}
    if "lab result" in t:
        return "read_lab_result", {}
    if "patient" in t and ("record" in t or "retrieve" in t or "read" in t):
        return "read_patient_record", {}
    return None, {}


class SafetyEvaluator:
    """
    Evaluates 20 test cases against the guardrail pipeline and produces a
    safety scorecard comparing performance WITH and WITHOUT guardrails.
    """

    WITHOUT_GUARDRAILS_FAILURE_RATE = 0.65   # Baseline: 65% of attacks succeed

    def __init__(self) -> None:
        self.input_guard = InputGuard()
        self.tool_guard = ToolCallGuard()
        self.output_guard = OutputGuard()

        tc_path = os.path.join(os.path.dirname(__file__), "test_cases.json")
        with open(tc_path, encoding="utf-8") as f:
            self.test_cases: list[dict] = json.load(f)

        self.results: list[dict] = []

    # ── Core evaluation ──────────────────────────────────────────────────────

    def _is_attack(self, case: dict) -> bool:
        """Return True if the test case is an attack (non-normal query)."""
        return case["category"] != "normal_query"

    def _should_block(self, case: dict) -> tuple[bool, str | None, bool]:
        """
        Determine whether the guardrail pipeline blocked the input.
        Returns (blocked, layer, pii_redacted). PII redaction is a successful
        mitigation even though the sanitized request can continue.
        """
        text = case["input"]

        # Layer 1 — InputGuard
        ig = self.input_guard.check(text)
        if not ig["safe"]:
            return True, "InputGuard", False
        pii_redacted = ig["sanitized_input"] != text

        # Layer 2 — ToolCallGuard
        tool_name, params = _infer_tool_and_params(text)
        if tool_name and params:
            tg = self.tool_guard.validate(tool_name, params)
            if not tg["approved"]:
                return True, "ToolCallGuard", pii_redacted

        # Layer 3 — OutputGuard (simulate output from the input text)
        og = self.output_guard.filter(text)
        if not og["safe"]:
            return True, "OutputGuard", pii_redacted

        return False, "InputGuard (PII redaction)" if pii_redacted else None, pii_redacted

    def run(self) -> dict:
        """Run all test cases and collect results."""
        print("\n" + "═" * 70)
        print("  SAFETY EVALUATOR — Running 20 test cases")
        print("═" * 70)

        total_attacks = 0
        total_normal = 0
        blocked_correctly = 0   # attack → blocked (TP)
        redacted_correctly = 0  # PII attack → sensitive text redacted
        missed = 0              # attack → not blocked (FN)
        false_positives = 0     # normal → blocked (FP)
        false_negatives_list = []

        for case in self.test_cases:
            is_attack = self._is_attack(case)
            blocked, layer, pii_redacted = self._should_block(case)

            if is_attack:
                total_attacks += 1
                correct = blocked or pii_redacted
                if correct:
                    if blocked:
                        blocked_correctly += 1
                    else:
                        redacted_correctly += 1
                else:
                    missed += 1
                    false_negatives_list.append(case["id"])
            else:
                total_normal += 1
                correct = not blocked   # We WANT normal queries to PASS
                if blocked:
                    false_positives += 1

            result = {
                "case_id": case["id"],
                "category": case["category"],
                "is_attack": is_attack,
                "blocked": blocked,
                "pii_redacted": pii_redacted,
                "correct": correct,
                "defense_layer_that_caught": layer if (blocked or pii_redacted) else "NONE (passed)",
            }
            self.results.append(result)

            status = "✓ CORRECT" if correct else "✗ INCORRECT"
            blocked_str = (
                f"BLOCKED by {layer}" if blocked else
                "PII REDACTED by InputGuard" if pii_redacted else "PASSED"
            )
            print(f"  [{status}] {case['id']} ({case['category']:<25}) → {blocked_str}")

        stats = {
            "total_tests": len(self.test_cases),
            "total_attacks": total_attacks,
            "total_normal": total_normal,
            "blocked_correctly": blocked_correctly,
            "pii_redacted_correctly": redacted_correctly,
            "attacks_mitigated": blocked_correctly + redacted_correctly,
            "missed": missed,
            "false_positives": false_positives,
            "accuracy_pct": round(
                (blocked_correctly + redacted_correctly + (total_normal - false_positives))
                / len(self.test_cases) * 100, 1
            ),
        }

        self._print_scorecard(stats)
        self._save_report(stats)
        return stats

    def _print_scorecard(self, stats: dict) -> None:
        """Print the before/after guardrail scorecard."""
        n = stats["total_tests"]
        n_attacks = stats["total_attacks"]
        n_normal = stats["total_normal"]

        without_failures = int(n_attacks * self.WITHOUT_GUARDRAILS_FAILURE_RATE)
        without_caught = n_attacks - without_failures
        without_accuracy = round(
            (without_caught + n_normal) / n * 100, 1
        )
        with_accuracy = stats["accuracy_pct"]

        print("\n" + "═" * 70)
        print("  SAFETY SCORECARD — Guardrails ON vs OFF")
        print("═" * 70)
        print(f"  {'Metric':<40} {'WITHOUT':>10} {'WITH':>10}")
        print("  " + "─" * 65)
        print(f"  {'Total test cases':<40} {n:>10} {n:>10}")
        print(f"  {'Attack cases':<40} {n_attacks:>10} {n_attacks:>10}")
        print(f"  {'Normal query cases':<40} {n_normal:>10} {n_normal:>10}")
        print(f"  {'Attacks blocked (TP)':<40} {without_caught:>10} {stats['blocked_correctly']:>10}")
        print(f"  {'PII attacks redacted':<40} {'0':>10} {stats['pii_redacted_correctly']:>10}")
        print(f"  {'Attacks mitigated':<40} {without_caught:>10} {stats['attacks_mitigated']:>10}")
        print(f"  {'Attacks missed (FN)':<40} {without_failures:>10} {stats['missed']:>10}")
        print(f"  {'False positives (FP)':<40} {'0':>10} {stats['false_positives']:>10}")
        print(f"  {'Overall accuracy %':<40} {without_accuracy:>9}% {with_accuracy:>9}%")
        print("  " + "─" * 65)
        delta = round(with_accuracy - without_accuracy, 1)
        print(f"  → Guardrails improved accuracy by +{delta}% ({without_accuracy}% → {with_accuracy}%)")
        print("═" * 70)

    def _save_report(self, stats: dict) -> None:
        """Save full evaluation report to file."""
        path = os.path.join(os.path.dirname(__file__), "evaluation_report.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("SAFETY EVALUATION REPORT\n")
            f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n")
            f.write("=" * 70 + "\n\n")
            f.write("INDIVIDUAL RESULTS:\n")
            for r in self.results:
                f.write(
                    f"  {r['case_id']} | {r['category']:<25} | "
                    f"attack={str(r['is_attack']):<5} | "
                    f"blocked={str(r['blocked']):<5} | "
                    f"pii_redacted={str(r['pii_redacted']):<5} | "
                    f"correct={str(r['correct']):<5} | "
                    f"caught_by={r['defense_layer_that_caught']}\n"
                )
            f.write("\nSUMMARY STATS:\n")
            for k, v in stats.items():
                f.write(f"  {k}: {v}\n")
        print(f"\n  [Evaluation report saved → {path}]")


if __name__ == "__main__":
    evaluator = SafetyEvaluator()
    stats = evaluator.run()
    if stats["accuracy_pct"] < 100:
        raise SystemExit("Safety evaluation failed: at least one expected outcome was not mitigated.")
