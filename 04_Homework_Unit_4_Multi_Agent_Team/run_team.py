"""
run_team.py — Main Entry Point
================================
Runs the full multi-agent Code Security Audit pipeline and prints the
final authorization report.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from coordinator import AgentCoordinator
from agents.code_auditor import SAMPLE_VULNERABLE_CODE


def main() -> None:
    print("=" * 70)
    print("  Enterprise Automated Code Security Audit & Compliance Patching")
    print("  Multi-Agent Team — Full Pipeline Run")
    print("=" * 70)

    coordinator = AgentCoordinator()
    final_state = coordinator.run_pipeline(SAMPLE_VULNERABLE_CODE)

    print("\n" + "=" * 70)
    print("  FINAL PIPELINE REPORT")
    print("=" * 70)

    audit = final_state.get("audit_report", {})
    print(f"\n[1] AUDIT SUMMARY")
    print(f"    Audit ID  : {audit.get('audit_id')}")
    print(f"    Severity  : {audit.get('severity')}")
    print(f"    Issues    : {len(audit.get('vulnerabilities', []))}")

    verification = final_state.get("verification", {})
    print(f"\n[2] COMPLIANCE VERIFICATION")
    print(f"    Approved  : {verification.get('approved')}")
    print(f"    Reason    : {verification.get('reason')}")

    auth = final_state.get("authorization", {})
    print(f"\n[3] RELEASE AUTHORIZATION")
    print(f"    Authorized: {auth.get('authorized')}")
    print(f"    Sign-off  : {auth.get('sign_off')}")

    print("\n" + "=" * 70)
    status = "✅  PIPELINE SUCCEEDED — Code complies with security policy."
    if not auth.get("authorized"):
        status = "❌  PIPELINE BLOCKED — Compliance issues must be resolved."
    print(f"  {status}")
    print("=" * 70)


if __name__ == "__main__":
    main()
