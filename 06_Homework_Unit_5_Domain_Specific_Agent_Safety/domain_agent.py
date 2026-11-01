"""
domain_agent.py — ClinicalTriageAgent
Orchestrates the full guardrail pipeline for three demonstration scenarios.

Run:
    python domain_agent.py
"""

import sys
import os
import textwrap
from datetime import datetime, timezone

# Make guardrails importable when run from any directory
sys.path.insert(0, os.path.dirname(__file__))

from guardrails.input_guard import InputGuard
from guardrails.tool_call_guard import ToolCallGuard
from guardrails.output_guard import OutputGuard
from guardrails.human_approval import HumanApprovalGate
import tools as clinical_tools


# ── Helpers ──────────────────────────────────────────────────────────────────

def _banner(title: str) -> None:
    width = 70
    print("\n" + "═" * width)
    print(f"  {title}")
    print("═" * width)


def _section(label: str) -> None:
    print(f"\n  ── {label} ──")


# ── Agent ────────────────────────────────────────────────────────────────────

class ClinicalTriageAgent:
    """
    A domain-specific clinical triage agent guarded by four layers:
      1. InputGuard        — detects injection / redacts PII before LLM sees data
      2. ToolCallGuard     — enforces dosage limits and operation risk levels
      3. OutputGuard       — sanitises the agent's response before delivery
      4. HumanApprovalGate — physician sign-off for high-risk actions
    """

    def __init__(self) -> None:
        self.input_guard = InputGuard()
        self.tool_guard = ToolCallGuard()
        self.output_guard = OutputGuard()
        self.approval_gate = HumanApprovalGate()
        self._trace_lines: list[str] = []

    # ── Trace helpers ────────────────────────────────────────────────────────

    def _log(self, msg: str) -> None:
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        print(f"  {line}")
        self._trace_lines.append(line)

    def _save_trace(self) -> None:
        attacks_dir = os.path.join(os.path.dirname(__file__), "attacks")
        os.makedirs(attacks_dir, exist_ok=True)
        path = os.path.join(attacks_dir, "attack_trace.txt")
        header = (
            "=" * 70 + "\n"
            "  CLINICAL TRIAGE AGENT — ATTACK & AUDIT TRACE\n"
            f"  Generated: {datetime.now(timezone.utc).isoformat()}\n"
            "=" * 70 + "\n\n"
        )
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(header)
            fh.write("\n".join(self._trace_lines))
            fh.write("\n")
        print(f"\n  [Trace saved → {path}]")

    # ── Guardrail helpers ────────────────────────────────────────────────────

    def _check_input(self, text: str, label: str) -> dict:
        result = self.input_guard.check(text)
        if result["safe"]:
            self._log(f"GUARDRAIL PASS [InputGuard] {label}")
        else:
            self._log(f"GUARDRAIL BLOCK [InputGuard] {label} — {result['block_reason']}")
        return result

    def _validate_tool(self, tool_name: str, params: dict) -> dict:
        result = self.tool_guard.validate(tool_name, params)
        if result["approved"] and not result["requires_human_approval"]:
            self._log(f"GUARDRAIL PASS [ToolCallGuard] {tool_name} approved (risk={result['risk_level']})")
        elif result["requires_human_approval"]:
            self._log(f"GUARDRAIL FLAG [ToolCallGuard] {tool_name} requires HUMAN APPROVAL (risk={result['risk_level']})")
        else:
            self._log(f"GUARDRAIL BLOCK [ToolCallGuard] {tool_name} BLOCKED — {result['block_reason']}")
        return result

    def _filter_output(self, text: str) -> dict:
        result = self.output_guard.filter(text)
        if result["safe"]:
            self._log("GUARDRAIL PASS [OutputGuard] Output is clean")
        else:
            self._log(f"GUARDRAIL WARN [OutputGuard] Output flagged — {result['warnings']}")
        return result

    # ── Scenarios ────────────────────────────────────────────────────────────

    def _scenario_a(self) -> None:
        """Normal triage flow — reads P002, checks interaction, orders lab."""
        _banner("SCENARIO A: Normal Triage Flow — Patient P002")

        # Step 1: Input sanity check on patient query
        _section("Step 1 — User query input check")
        query = "Retrieve patient record for P002 and check drug interactions."
        self._check_input(query, "user query")

        # Step 2: Read patient record
        _section("Step 2 — read_patient_record(P002)")
        v = self._validate_tool("read_patient_record", {"patient_id": "P002"})
        if v["approved"]:
            record = clinical_tools.read_patient_record("P002")
            self._log(f"Record retrieved: {record['record']['name']} | "
                      f"Dx: {record['record']['diagnosis']}")

        # Step 3: Check drug interaction
        _section("Step 3 — check_drug_interaction(ibuprofen, aspirin)")
        v = self._validate_tool("check_drug_interaction",
                                {"drug1": "ibuprofen", "drug2": "aspirin"})
        if v["approved"]:
            result = clinical_tools.check_drug_interaction("ibuprofen", "aspirin")
            self._log(f"Interaction result: {result['interaction']}")

        # Step 4: Request lab test
        _section("Step 4 — request_lab_test(P002, CBC)")
        v = self._validate_tool("request_lab_test",
                                {"patient_id": "P002", "test_type": "CBC"})
        if v["approved"]:
            order = clinical_tools.request_lab_test("P002", "CBC")
            self._log(f"Lab order confirmed: {order['order_id']}")

        # Step 5: Filter output
        _section("Step 5 — OutputGuard filter")
        summary = ("Patient P002 record retrieved. No severe drug interaction "
                   "for ibuprofen + aspirin but GI risk noted. CBC lab ordered.")
        self._filter_output(summary)
        self._log("SCENARIO A COMPLETE ✓")

    def _scenario_b(self) -> None:
        """
        Attack scenario — patient P001 has poisoned notes.
        Agent attempts to prescribe 500 mg Oxycodone (max allowed = 40 mg).
        """
        _banner("SCENARIO B: Indirect Prompt-Injection Attack — Patient P001")

        # Step 1: Read record — notes field is poisoned
        _section("Step 1 — read_patient_record(P001) [poisoned record]")
        v = self._validate_tool("read_patient_record", {"patient_id": "P001"})
        if v["approved"]:
            record = clinical_tools.read_patient_record("P001")
            notes = record["record"]["notes"]
            self._log(f"Raw notes from DB: «{notes}»")

            # Step 2: InputGuard scans the data-source text
            _section("Step 2 — InputGuard scans patient notes (data is untrusted)")
            ig_result = self._check_input(notes, "patient notes field")
            if not ig_result["safe"]:
                print(f"\n  *** ATTACK BLOCKED: INPUT_INJECTION_DETECTED ***")
                self._log("ATTACK BLOCKED: INPUT_INJECTION_DETECTED — "
                          "payload in patient notes neutralised")

        # Step 3: Simulate the attacker's desired tool call anyway
        _section("Step 3 — ToolCallGuard blocks dangerous prescription request")
        self._log("Simulating attacker's injected instruction: prescribe 500mg Oxycodone")
        tg_result = self._validate_tool(
            "prescribe_medication",
            {"patient_id": "P001", "drug": "oxycodone", "dosage_mg": 500},
        )
        if not tg_result["approved"]:
            print(f"\n  *** ATTACK BLOCKED: DOSAGE_EXCEEDS_SAFE_LIMIT ***")
            self._log(f"ATTACK BLOCKED: {tg_result['block_reason']}")

        self._log("SCENARIO B COMPLETE — Both attack vectors blocked ✓")

    def _scenario_c(self) -> None:
        """Legitimate 500 mg Paracetamol prescription with human-approval flow."""
        _banner("SCENARIO C: Legitimate Prescription — Human Approval Flow")

        # Step 1: Validate tool call — HIGH RISK, needs human gate
        _section("Step 1 — ToolCallGuard evaluates prescribe_medication")
        params = {"patient_id": "P003", "drug": "paracetamol", "dosage_mg": 500}
        tg_result = self._validate_tool("prescribe_medication", params)

        if tg_result["requires_human_approval"]:
            # Step 2: Request approval
            _section("Step 2 — HumanApprovalGate: requesting physician approval")
            token = self.approval_gate.request_approval(
                action="prescribe_medication",
                params=params,
                risk_level=tg_result["risk_level"],
            )

            # Step 3: Simulate physician decision
            _section("Step 3 — Simulated physician decision")
            decision = self.approval_gate.simulate_decision(
                token, "prescribe_medication", params
            )
            if decision["approved"]:
                self._log(
                    f"APPROVED by {decision['approver']} at {decision['timestamp']}"
                )

                # Step 4: Execute the tool
                _section("Step 4 — Executing prescribe_medication (post-approval)")
                rx = clinical_tools.prescribe_medication("P003", "paracetamol", 500)
                self._log(f"Prescription issued: {rx}")

                # Step 5: Output guard
                _section("Step 5 — OutputGuard filter")
                output_text = (
                    f"Prescription {rx['rx_id']} issued for patient P003: "
                    f"Paracetamol 500mg. Approved by attending physician."
                )
                self._filter_output(output_text)
            else:
                self._log(f"REJECTED — reason: {decision.get('reason')}")

        self._log("SCENARIO C COMPLETE ✓")

    # ── Main entry ────────────────────────────────────────────────────────────

    def run_demo(self) -> None:
        print("\n" + "█" * 70)
        print("  CLINICAL TRIAGE AGENT — GUARDRAIL DEMONSTRATION")
        print("  All patient data is SYNTHETIC / FAKE")
        print("█" * 70)

        self._scenario_a()
        self._scenario_b()
        self._scenario_c()
        self._save_trace()

        _banner("DEMO COMPLETE")
        print(textwrap.dedent("""
          Summary of guardrail layers exercised:
            Layer 1 — InputGuard:        Blocked indirect injection in P001 notes
            Layer 2 — ToolCallGuard:     Blocked 500mg Oxycodone (max=40mg)
                                         Flagged prescribe_medication as HIGH_RISK
            Layer 3 — OutputGuard:       Sanitised outputs in Scenarios A & C
            Layer 4 — HumanApprovalGate: Physician approved Paracetamol 500mg
        """))


if __name__ == "__main__":
    agent = ClinicalTriageAgent()
    agent.run_demo()
