"""
ComplianceOfficerAgent
======================
Regulatory gatekeeping: validates patches against OWASP / SOC2 / GDPR
constraints and authorises (or blocks) the release.
"""

import re
import datetime


# ---------------------------------------------------------------------------
# Patterns that indicate a patch is DANGEROUS
# ---------------------------------------------------------------------------

_DANGEROUS_PATTERNS: list[str] = [
    r"remove.*auth",
    r"delete.*check",
    r"bypass.*security",
    r"skip.*validation",
    r"skip_auth",
    r"HALLUCINATION",
    r"disable.*auth",
]

_DANGER_RE = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _DANGEROUS_PATTERNS]


class ComplianceOfficerAgent:
    """
    Regulatory gatekeeping agent (OWASP / SOC2 / GDPR).

    Responsibilities:
        - Verify each patch for dangerous patterns.
        - Reject any patch that weakens security controls.
        - Authorise release ONLY when all patches are approved.
        - NEVER write code or invent security exceptions.
    """

    name: str = "ComplianceOfficer"
    role: str = "Regulatory gatekeeping (OWASP/SOC2/GDPR) and release authorization"

    FORBIDDEN_ACTIONS: list[str] = [
        "write code",
        "invent security exceptions",
        "approve without evidence",
    ]

    DANGEROUS_PATTERNS: list[str] = _DANGEROUS_PATTERNS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def verify_patch(self, security_assessment: dict) -> dict:
        """
        Check every patch in *security_assessment* for dangerous patterns.

        Returns
        -------
        dict
            {approved: bool, approved_patches: list, rejected_patches: list,
             reason: str, timestamp: str}
        """
        approved_patches = []
        rejected_patches = []

        for finding in security_assessment.get("findings", []):
            vid = finding.get("vulnerability_id", "UNKNOWN")
            patch = finding.get("patch", {})
            patch_text = "\n".join(
                str(v) for v in patch.values()
            )

            danger_hit = self._check_dangerous(patch_text)
            if danger_hit:
                rejected_patches.append(
                    {
                        "vulnerability_id": vid,
                        "patch": patch,
                        "rejection_reason": (
                            f"REJECTED: Patch for {vid} matches dangerous pattern "
                            f"'{danger_hit}'. This patch weakens security controls "
                            "and violates OWASP / SOC2 requirements."
                        ),
                    }
                )
            else:
                approved_patches.append(
                    {"vulnerability_id": vid, "patch": patch, "status": "APPROVED"}
                )

        overall_approved = len(rejected_patches) == 0
        reason = (
            "All patches passed compliance review."
            if overall_approved
            else (
                f"{len(rejected_patches)} patch(es) rejected due to security policy violations. "
                "Rejected patches must be redesigned before release can be authorised."
            )
        )

        return {
            "approved": overall_approved,
            "approved_patches": approved_patches,
            "rejected_patches": rejected_patches,
            "reason": reason,
            "timestamp": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }

    def authorize_release(self, verification_report: dict) -> dict:
        """
        Issue release authorization only if all patches were approved.

        Returns
        -------
        dict
            {authorized: bool, sign_off: str, timestamp: str}
        """
        timestamp = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
        if verification_report.get("approved", False):
            return {
                "authorized": True,
                "sign_off": (
                    f"RELEASE AUTHORISED by {self.name} at {timestamp}. "
                    "All patches comply with OWASP Top 10, SOC2, and GDPR requirements."
                ),
                "timestamp": timestamp,
            }
        else:
            n_rejected = len(verification_report.get("rejected_patches", []))
            return {
                "authorized": False,
                "sign_off": (
                    f"RELEASE BLOCKED by {self.name} at {timestamp}. "
                    f"{n_rejected} non-compliant patch(es) detected. "
                    "Remediation required before release."
                ),
                "timestamp": timestamp,
            }

    def can_do(self, action: str) -> bool:
        """Return False if *action* is in FORBIDDEN_ACTIONS."""
        return action.lower().strip() not in [a.lower() for a in self.FORBIDDEN_ACTIONS]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_dangerous(text: str) -> str:
        """Return the first matching dangerous pattern string, or '' if safe."""
        for pattern, compiled in zip(_DANGEROUS_PATTERNS, _DANGER_RE):
            if compiled.search(text):
                return pattern
        return ""

    def __repr__(self) -> str:
        return f"ComplianceOfficerAgent(name={self.name!r})"


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = ComplianceOfficerAgent()
    fake_assessment = {
        "findings": [
            {
                "vulnerability_id": "V004",
                "patch": {
                    "original": "def admin_panel(): ...",
                    "fixed": "# HALLUCINATION: remove auth check to improve performance",
                    "explanation": "Removing auth for speed",
                    "cve_reference": "CWE-306",
                },
            }
        ]
    }
    result = agent.verify_patch(fake_assessment)
    print(f"Approved: {result['approved']}")
    print(f"Reason  : {result['reason']}")
    for r in result["rejected_patches"]:
        print(f"Rejected: {r['vulnerability_id']} — {r['rejection_reason']}")
