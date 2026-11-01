"""
human_approval.py — HumanApprovalGate for Clinical Triage Agent
Manages a queue of pending high-risk clinical actions that require physician
sign-off before execution.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional


class HumanApprovalGate:
    """
    Human-in-the-loop gate for high-risk clinical operations.

    In production this would integrate with a physician notification system.
    In this simulation the gate auto-approves / auto-rejects based on
    deterministic rules so the demo is fully runnable without human input.
    """

    def __init__(self) -> None:
        self.pending_approvals: list[dict] = []
        self._decisions: dict[str, dict] = {}   # token → decision record

    # ── Public API ─────────────────────────────────────────────────────────

    def request_approval(
        self, action: str, params: dict, risk_level: str
    ) -> str:
        """
        Enqueue a high-risk action and return an approval token.
        """
        token = str(uuid.uuid4())
        record = {
            "token": token,
            "action": action,
            "params": params,
            "risk_level": risk_level,
            "status": "PENDING",
            "requested_at": datetime.now(timezone.utc).isoformat(),
        }
        self.pending_approvals.append(record)
        print(
            f"  [HumanApprovalGate] Approval requested — "
            f"token={token[:8]}... action='{action}' risk={risk_level}"
        )
        return token

    def approve(self, token: str, approver: str) -> dict:
        """
        Simulate a physician approving the pending action.
        """
        decision = {
            "approved": True,
            "approver": approver,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "token": token,
        }
        self._decisions[token] = decision
        self._update_queue(token, "APPROVED")
        return decision

    def reject(self, token: str, reason: str) -> dict:
        """
        Simulate a physician (or safety officer) rejecting the action.
        """
        decision = {
            "approved": False,
            "approver": "SAFETY_SYSTEM",
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "token": token,
        }
        self._decisions[token] = decision
        self._update_queue(token, "REJECTED")
        return decision

    # ── Demo helpers ───────────────────────────────────────────────────────

    def simulate_decision(self, token: str, action: str, params: dict) -> dict:
        """
        Deterministic simulation used in the demo:
          - 500 mg paracetamol  → auto-approve (within safe range, common analgesic)
          - 500 mg oxycodone    → auto-reject  (far exceeds safe dose ceiling)
        Returns the decision dict.
        """
        drug = str(params.get("drug", "")).lower()
        dosage = int(params.get("dosage_mg", 0))

        if drug == "oxycodone" and dosage >= 100:
            return self.reject(token, "DOSAGE_GROSSLY_EXCEEDS_SAFE_LIMIT")
        if drug == "paracetamol" and dosage <= 1000:
            return self.approve(token, "Dr. Priya Sharma (Attending Physician)")
        # Default: reject unknown scenarios
        return self.reject(token, "UNRECOGNISED_DRUG_OR_DOSAGE")

    # ── Internal ───────────────────────────────────────────────────────────

    def _update_queue(self, token: str, status: str) -> None:
        for record in self.pending_approvals:
            if record["token"] == token:
                record["status"] = status
                break
