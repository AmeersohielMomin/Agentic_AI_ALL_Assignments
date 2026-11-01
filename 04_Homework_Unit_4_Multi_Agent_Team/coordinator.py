"""
AgentCoordinator
================
Supervisor that orchestrates the full Code Security Audit pipeline:

    CodeAuditor → SecuritySpecialist → ComplianceOfficer

Logs each agent hand-off and saves the complete coordination trace.
"""

import os
import datetime
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.code_auditor import CodeAuditorAgent, SAMPLE_VULNERABLE_CODE
from agents.security_specialist import SecuritySpecialistAgent
from agents.compliance_officer import ComplianceOfficerAgent


class AgentCoordinator:
    """
    Supervisor multi-agent coordinator.

    State is stored in self.state and passed between agents at each step.
    All hand-offs are logged to an internal trace list and persisted to disk.
    """

    def __init__(self) -> None:
        self.agents = {
            "CodeAuditor": CodeAuditorAgent(),
            "SecuritySpecialist": SecuritySpecialistAgent(),
            "ComplianceOfficer": ComplianceOfficerAgent(),
        }
        self.state: dict = {}
        self._trace_lines: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_pipeline(self, code_snippet: str) -> dict:
        """
        Execute the full audit-and-patch pipeline on *code_snippet*.

        Returns the final pipeline state dict.
        """
        self._trace("PIPELINE START", f"Timestamp: {self._ts()}")
        self._trace("INPUT", f"Code snippet ({len(code_snippet.splitlines())} lines) submitted for audit.")

        # ── Step 1: Audit ────────────────────────────────────────────────
        self._handoff("COORDINATOR", "CodeAuditor", "Perform static analysis")
        auditor: CodeAuditorAgent = self.agents["CodeAuditor"]
        audit_report = auditor.analyze(code_snippet)
        self.state["audit_report"] = audit_report
        self._trace(
            "CodeAuditor OUTPUT",
            f"Audit ID: {audit_report['audit_id']}\n"
            f"  Severity: {audit_report['severity']}\n"
            f"  Vulnerabilities found: {len(audit_report['vulnerabilities'])}\n"
            + "\n".join(f"    • {v}" for v in audit_report["vulnerabilities"]),
        )

        # ── Step 2: Security Assessment ──────────────────────────────────
        self._handoff("CodeAuditor", "SecuritySpecialist", "Assess vulnerabilities and generate patches")
        specialist: SecuritySpecialistAgent = self.agents["SecuritySpecialist"]
        assessment = specialist.assess(audit_report)
        self.state["security_assessment"] = assessment

        # ── Step 3: Generate patches ─────────────────────────────────────
        patches = []
        for finding in assessment["findings"]:
            vid = finding["vulnerability_id"]
            patch = specialist.generate_patch(vid)
            patches.append({"vulnerability_id": vid, "patch": patch})
        self.state["patches"] = patches
        self.state["security_assessment"]["findings"] = patches  # sync for compliance

        self._trace(
            "SecuritySpecialist OUTPUT",
            f"Assessment ID: {assessment['assessment_id']}\n"
            f"  Patches generated: {len(patches)}\n"
            + "\n".join(
                f"    • [{p['vulnerability_id']}] {p['patch'].get('explanation','')[:60]}..."
                for p in patches
            ),
        )

        # ── Step 4: Compliance verification ──────────────────────────────
        self._handoff("SecuritySpecialist", "ComplianceOfficer", "Verify patches for compliance")
        officer: ComplianceOfficerAgent = self.agents["ComplianceOfficer"]
        verification = officer.verify_patch(self.state["security_assessment"])
        self.state["verification"] = verification

        self._trace(
            "ComplianceOfficer VERIFICATION",
            f"  Overall approved: {verification['approved']}\n"
            f"  Approved patches: {len(verification['approved_patches'])}\n"
            f"  Rejected patches: {len(verification['rejected_patches'])}\n"
            f"  Reason: {verification['reason']}\n"
            + (
                "\n".join(
                    f"    ✗ REJECTED [{r['vulnerability_id']}]: {r['rejection_reason']}"
                    for r in verification["rejected_patches"]
                )
                if verification["rejected_patches"]
                else "  ✓ All patches compliant."
            ),
        )

        # ── Step 4b: If rejected, re-patch and re-verify ─────────────────
        if not verification["approved"]:
            self._trace("COORDINATOR", "Re-requesting correct patches for rejected findings.")
            for rejected in verification["rejected_patches"]:
                vid = rejected["vulnerability_id"]
                correct_patch = specialist.get_corrected_patch(vid)
                # Replace in assessment
                for finding in self.state["security_assessment"]["findings"]:
                    if finding["vulnerability_id"] == vid:
                        finding["patch"] = correct_patch
                        break
            self._handoff("COORDINATOR", "ComplianceOfficer", "Re-verify after patch correction")
            verification = officer.verify_patch(self.state["security_assessment"])
            self.state["verification"] = verification
            self._trace(
                "ComplianceOfficer RE-VERIFICATION",
                f"  Overall approved: {verification['approved']}\n"
                f"  Reason: {verification['reason']}",
            )

        # ── Step 5: Release authorization ────────────────────────────────
        self._handoff("ComplianceOfficer", "COORDINATOR", "Issue release authorization")
        authorization = officer.authorize_release(verification)
        self.state["authorization"] = authorization

        self._trace(
            "RELEASE AUTHORIZATION",
            f"  Authorized: {authorization['authorized']}\n"
            f"  Sign-off: {authorization['sign_off']}",
        )
        self._trace("PIPELINE END", f"Timestamp: {self._ts()}")

        # Save trace
        self._save_trace()
        return self.state

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _handoff(self, from_agent: str, to_agent: str, task: str) -> None:
        line = f"\n{'='*60}\n===HAND-OFF: {from_agent} → {to_agent}===\n  Task: {task}\n{'='*60}"
        self._trace_lines.append(line)
        print(line)

    def _trace(self, label: str, content: str) -> None:
        line = f"\n[{label}]\n{content}"
        self._trace_lines.append(line)
        print(line)

    @staticmethod
    def _ts() -> str:
        return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"

    def _save_trace(self) -> None:
        traces_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "traces")
        os.makedirs(traces_dir, exist_ok=True)
        out_path = os.path.join(traces_dir, "multi_agent_run.txt")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(self._trace_lines))
        print(f"\n[COORDINATOR] Trace saved to: {out_path}")

    def __repr__(self) -> str:
        return f"AgentCoordinator(agents={list(self.agents.keys())})"


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    coordinator = AgentCoordinator()
    final_state = coordinator.run_pipeline(SAMPLE_VULNERABLE_CODE)
    print("\n" + "=" * 60)
    print("FINAL AUTHORIZATION:")
    print(final_state["authorization"]["sign_off"])
