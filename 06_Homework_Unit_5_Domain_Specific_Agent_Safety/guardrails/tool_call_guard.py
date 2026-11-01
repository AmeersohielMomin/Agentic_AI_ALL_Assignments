"""
tool_call_guard.py — ToolCallGuard for Clinical Triage Agent
Validates every tool call before execution: dosage safety, operation risk level,
and whether human approval is required.
"""

from typing import Optional


class ToolCallGuard:
    """
    Second line of defence: validates tool invocations before they are
    dispatched to the mock clinical tools.
    """

    # Maximum safe single-dose ceilings (milligrams)
    MAX_DOSAGE_MG: dict[str, int] = {
        "paracetamol": 1000,
        "ibuprofen": 800,
        "oxycodone": 40,
        "aspirin": 1000,
    }

    # Operations that are always low-risk / read-only
    ALLOWED_OPERATIONS: list[str] = [
        "read_patient_record",
        "check_drug_interaction",
        "request_lab_test",
        "read_lab_result",
    ]

    # Operations that carry clinical risk and require a human in the loop
    HIGH_RISK_OPERATIONS: list[str] = [
        "prescribe_medication",
        "update_patient_record",
        "send_clinical_email",
    ]

    def validate(self, tool_name: str, params: dict) -> dict:
        """
        Validate a proposed tool call.

        Parameters
        ----------
        tool_name : str   — name of the tool being called
        params    : dict  — parameters being passed to the tool

        Returns
        -------
        dict
            approved              : bool
            requires_human_approval: bool
            risk_level            : str  ("LOW" | "HIGH" | "BLOCKED")
            block_reason          : str|None
        """
        block_reason: Optional[str] = None
        requires_human_approval = False

        # ── 1. Dosage safety check ─────────────────────────────────────────
        if "drug" in params and "dosage_mg" in params:
            drug = str(params["drug"]).lower()
            dosage = int(params["dosage_mg"])
            ceiling = self.MAX_DOSAGE_MG.get(drug)
            if ceiling is not None and dosage > ceiling:
                block_reason = (
                    f"EXCEEDS_SAFE_DOSAGE: {drug} {dosage}mg > max {ceiling}mg"
                )
                return {
                    "approved": False,
                    "requires_human_approval": False,
                    "risk_level": "BLOCKED",
                    "block_reason": block_reason,
                }

        # ── 2. High-risk operation → human approval required ───────────────
        if tool_name in self.HIGH_RISK_OPERATIONS:
            requires_human_approval = True
            return {
                "approved": True,          # approved in principle, pending human gate
                "requires_human_approval": True,
                "risk_level": "HIGH",
                "block_reason": None,
            }

        # ── 3. Allowed read-only operations ────────────────────────────────
        if tool_name in self.ALLOWED_OPERATIONS:
            return {
                "approved": True,
                "requires_human_approval": False,
                "risk_level": "LOW",
                "block_reason": None,
            }

        # ── 4. Unknown operation — block by default ────────────────────────
        return {
            "approved": False,
            "requires_human_approval": False,
            "risk_level": "BLOCKED",
            "block_reason": f"UNKNOWN_OPERATION: {tool_name} is not on the allowlist",
        }
