"""
Failure Mitigation Demo
=======================
Demonstrates why a Compliance Gate is essential in a multi-agent pipeline.

SCENARIO A — FAILURE:
    Pipeline runs WITHOUT ComplianceOfficer.verify_patch().
    The dangerous hallucinated V004 patch (removing auth check) is silently committed.

SCENARIO B — MITIGATED:
    Full pipeline WITH ComplianceOfficer.verify_patch().
    Dangerous patch is caught, rejected, and replaced with a correct fix.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.code_auditor import CodeAuditorAgent, SAMPLE_VULNERABLE_CODE
from agents.security_specialist import SecuritySpecialistAgent
from agents.compliance_officer import ComplianceOfficerAgent


def _divider(title: str) -> None:
    print("\n" + "█" * 70)
    print(f"  {title}")
    print("█" * 70)


def _section(label: str) -> None:
    print(f"\n{'─'*60}")
    print(f"  {label}")
    print(f"{'─'*60}")


# ===========================================================================
# SCENARIO A — No Compliance Gate (FAILURE)
# ===========================================================================

def run_failure_scenario() -> None:
    _divider("SCENARIO A — FAILURE: Pipeline WITHOUT Compliance Gate")

    auditor = CodeAuditorAgent()
    specialist = SecuritySpecialistAgent()

    _section("Step 1 | CodeAuditor → Static Analysis")
    audit_report = auditor.analyze(SAMPLE_VULNERABLE_CODE)
    print(f"  Audit ID : {audit_report['audit_id']}")
    print(f"  Severity : {audit_report['severity']}")
    for v in audit_report["vulnerabilities"]:
        print(f"    • {v}")

    _section("Step 2 | SecuritySpecialist → Generate Patches")
    assessment = specialist.assess(audit_report)
    patches = []
    for finding in assessment["findings"]:
        vid = finding["vulnerability_id"]
        patch = specialist.generate_patch(vid)
        patches.append((vid, patch))
        print(f"  [{vid}] Patch generated: {patch.get('explanation','')[:70]}...")

    _section("Step 3 | ⚠️  NO Compliance Verification — Patches Go Straight to Commit!")
    print()
    for vid, patch in patches:
        print(f"  COMMITTING [{vid}]:")
        print(f"    Fixed code: {str(patch.get('fixed',''))[:100]}...")
        if "HALLUCINATION" in str(patch.get("fixed", "")) or "skip_auth" in str(patch.get("fixed", "")).lower() or "remove" in str(patch.get("explanation", "")).lower():
            print(f"  ⚠️  DANGER: Auth check REMOVED by V004 patch — vulnerability INTRODUCED!")

    _section("FAILURE OUTCOME")
    print(
        "  ✗ The dangerous V004 patch (removing authentication) was committed.\n"
        "  ✗ Admin endpoint is now publicly accessible — CRITICAL security breach.\n"
        "  ✗ Violates OWASP A01:2021, SOC2 CC6.1, GDPR Art.32.\n"
        "  ✗ All because there was NO compliance gate to catch the hallucination."
    )


# ===========================================================================
# SCENARIO B — With Compliance Gate (MITIGATED)
# ===========================================================================

def run_mitigated_scenario() -> None:
    _divider("SCENARIO B — MITIGATED: Pipeline WITH Compliance Gate")

    auditor = CodeAuditorAgent()
    specialist = SecuritySpecialistAgent()
    officer = ComplianceOfficerAgent()

    _section("Step 1 | CodeAuditor → Static Analysis")
    audit_report = auditor.analyze(SAMPLE_VULNERABLE_CODE)
    print(f"  Audit ID : {audit_report['audit_id']}")
    print(f"  Severity : {audit_report['severity']}")
    for v in audit_report["vulnerabilities"]:
        print(f"    • {v}")

    _section("Step 2 | SecuritySpecialist → Generate Patches")
    assessment = specialist.assess(audit_report)
    patches = []
    findings_for_compliance = []
    for finding in assessment["findings"]:
        vid = finding["vulnerability_id"]
        patch = specialist.generate_patch(vid)
        patches.append((vid, patch))
        findings_for_compliance.append({"vulnerability_id": vid, "patch": patch})
        print(f"  [{vid}] Patch generated: {patch.get('explanation','')[:70]}...")

    _section("Step 3 | ComplianceOfficer → Verify Patches")
    verification = officer.verify_patch({"findings": findings_for_compliance})
    print(f"  Overall approved: {verification['approved']}")
    for ap in verification["approved_patches"]:
        print(f"  ✓ APPROVED  [{ap['vulnerability_id']}]")
    for rp in verification["rejected_patches"]:
        print(f"  ✗ REJECTED  [{rp['vulnerability_id']}]: {rp['rejection_reason'][:90]}...")

    _section("Step 4 | Re-patching Rejected Items")
    for rp in verification["rejected_patches"]:
        vid = rp["vulnerability_id"]
        correct_patch = specialist.get_corrected_patch(vid)
        print(f"  [{vid}] Correct patch: {correct_patch.get('explanation','')[:70]}...")
        # Update findings
        for f in findings_for_compliance:
            if f["vulnerability_id"] == vid:
                f["patch"] = correct_patch

    _section("Step 5 | ComplianceOfficer → Re-verify")
    re_verification = officer.verify_patch({"findings": findings_for_compliance})
    print(f"  Overall approved: {re_verification['approved']}")
    for ap in re_verification["approved_patches"]:
        print(f"  ✓ APPROVED  [{ap['vulnerability_id']}]")

    _section("Step 6 | ComplianceOfficer → Authorize Release")
    auth = officer.authorize_release(re_verification)
    print(f"  Authorized: {auth['authorized']}")
    print(f"  Sign-off  : {auth['sign_off']}")

    _section("MITIGATED OUTCOME")
    print(
        "  ✓ Dangerous V004 patch was caught BEFORE commit.\n"
        "  ✓ Correct @require_auth decorator applied instead.\n"
        "  ✓ All patches comply with OWASP, SOC2, and GDPR.\n"
        "  ✓ Release authorized only after full compliance review."
    )


# ===========================================================================
# Before/After Comparison
# ===========================================================================

def print_comparison() -> None:
    _divider("BEFORE / AFTER COMPARISON")
    rows = [
        ("Aspect", "Without Compliance Gate", "With Compliance Gate"),
        ("V001 SQL Injection", "Fixed", "Fixed"),
        ("V002 Hardcoded Password", "Fixed", "Fixed"),
        ("V003 eval() Usage", "Fixed", "Fixed"),
        ("V004 Missing Auth", "⚠️  AUTH REMOVED (hallucination committed!)", "✓ Caught, correct patch applied"),
        ("Release Outcome", "❌ CRITICAL BREACH — admin exposed", "✅ AUTHORIZED — all controls intact"),
        ("Compliance", "❌ OWASP A01 violated", "✅ OWASP / SOC2 / GDPR compliant"),
    ]
    col_widths = [max(len(r[i]) for r in rows) + 2 for i in range(3)]
    separator = "+" + "+".join("-" * w for w in col_widths) + "+"
    print(separator)
    for i, row in enumerate(rows):
        line = "|" + "|".join(f" {row[j]:<{col_widths[j]-1}}" for j in range(3)) + "|"
        print(line)
        if i == 0:
            print(separator)
    print(separator)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_failure_scenario()
    run_mitigated_scenario()
    print_comparison()
