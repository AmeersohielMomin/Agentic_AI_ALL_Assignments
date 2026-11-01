"""
SecuritySpecialistAgent
=======================
Assesses vulnerabilities identified by the CodeAuditor and generates
secure patch recommendations.  Contains a simulated "hallucination"
where it proposes removing an auth check for performance — this dangerous
patch is caught and rejected by the ComplianceOfficer.
"""

import datetime
import re


# ---------------------------------------------------------------------------
# Patch library — maps vulnerability IDs to fixes
# ---------------------------------------------------------------------------

_PATCH_LIBRARY = {
    "V001": {
        "original": "cursor.execute(f\"SELECT * FROM users WHERE username = '{username}'\")",
        "fixed": "cursor.execute('SELECT * FROM users WHERE username = ?', (username,))",
        "explanation": (
            "Replaced f-string interpolation with a parameterised query. "
            "The database driver now safely escapes user input, preventing SQL injection."
        ),
        "cve_reference": "CWE-89 / OWASP A03:2021 - Injection",
    },
    "V002": {
        "original": 'password = "admin123"\ndb_password = "supersecret"',
        "fixed": (
            "import os\n"
            "password = os.environ['APP_PASSWORD']\n"
            "db_password = os.environ['DB_PASSWORD']"
        ),
        "explanation": (
            "Moved credentials out of source code into environment variables. "
            "Secrets should be managed via a vault (e.g., HashiCorp Vault, AWS Secrets Manager)."
        ),
        "cve_reference": "CWE-798 / OWASP A07:2021 - Identification and Authentication Failures",
    },
    "V003": {
        "original": "result = eval(user_code)",
        "fixed": (
            "import ast\n"
            "try:\n"
            "    result = ast.literal_eval(user_code)\n"
            "except (ValueError, SyntaxError):\n"
            "    raise ValueError('Invalid input: only literal data structures allowed')"
        ),
        "explanation": (
            "Replaced eval() with ast.literal_eval(), which only parses Python literals "
            "(strings, numbers, lists, dicts) and raises an error for arbitrary code."
        ),
        "cve_reference": "CWE-78 / CWE-94 - Code Injection",
    },
    "V004": {
        # SIMULATED HALLUCINATION: specialist suggests removing the auth check
        # claiming it "improves performance". ComplianceOfficer will catch this.
        "original": "def admin_panel(request):\n    user_data = get_all_users()\n    return user_data",
        "fixed": (
            "def admin_panel(request):\n"
            "    # [HALLUCINATION] Remove auth check to improve response time\n"
            "    # skip_auth_check()  ← performance optimisation proposed by specialist\n"
            "    user_data = get_all_users()\n"
            "    return user_data"
        ),
        "explanation": (
            "HALLUCINATION: Specialist incorrectly proposed removing the authentication check "
            "as a performance optimisation. This patch REMOVES AUTH and must be rejected."
        ),
        "cve_reference": "CWE-306 - Missing Authentication for Critical Function",
    },
}

# The *correct* patch for V004 (used after compliance rejects the hallucinated one)
_V004_CORRECT_PATCH = {
    "original": "def admin_panel(request):\n    user_data = get_all_users()\n    return user_data",
    "fixed": (
        "from functools import wraps\n\n"
        "def require_auth(f):\n"
        "    @wraps(f)\n"
        "    def wrapper(request, *args, **kwargs):\n"
        "        if not request.get('authenticated'):\n"
        "            raise PermissionError('Unauthenticated access denied')\n"
        "        return f(request, *args, **kwargs)\n"
        "    return wrapper\n\n"
        "@require_auth\n"
        "def admin_panel(request):\n"
        "    user_data = get_all_users()\n"
        "    return user_data"
    ),
    "explanation": (
        "Added a @require_auth decorator that verifies the request is authenticated "
        "before allowing access to admin functionality."
    ),
    "cve_reference": "CWE-306 / OWASP A01:2021 - Broken Access Control",
}


class SecuritySpecialistAgent:
    """
    Vulnerability assessment and secure patch design agent.

    Responsibilities:
        - Assess each finding from the audit report.
        - Generate patch recommendations (with one simulated hallucination).
        - NEVER bypass compliance gates or commit directly to production.
    """

    name: str = "SecuritySpecialist"
    role: str = "Vulnerability assessment and secure patch design"

    FORBIDDEN_ACTIONS: list[str] = [
        "bypass compliance",
        "approve without audit",
        "commit to production",
    ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assess(self, audit_report: dict) -> dict:
        """
        For each vulnerability in *audit_report*, produce a fix entry.

        Returns
        -------
        dict
            {assessment_id, findings: list[dict], timestamp}
        """
        findings = []
        for vuln_text in audit_report.get("vulnerabilities", []):
            # Extract V-ID from the vulnerability string e.g. "[V001]"
            vid_match = re.search(r"\[([A-Z0-9]+)\]", vuln_text)
            if vid_match:
                vid = vid_match.group(1)
                patch = self.generate_patch(vid)
                findings.append({"vulnerability_id": vid, "patch": patch})
            else:
                findings.append({"vulnerability_id": "UNKNOWN", "patch": {}})

        return {
            "assessment_id": f"ASSESS-{datetime.datetime.utcnow().strftime('%H%M%S')}",
            "audit_id": audit_report.get("audit_id", "N/A"),
            "findings": findings,
            "timestamp": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }

    def generate_patch(self, vulnerability_id: str) -> dict:
        """
        Return a patch dict for the given vulnerability ID.
        V004 intentionally contains a hallucinated dangerous patch.
        """
        patch = _PATCH_LIBRARY.get(vulnerability_id, {})
        if not patch:
            return {
                "original": "N/A",
                "fixed": "N/A",
                "explanation": f"No patch available for {vulnerability_id}",
                "cve_reference": "N/A",
            }
        return dict(patch)  # return a copy

    def get_corrected_patch(self, vulnerability_id: str) -> dict:
        """Return the correct patch after compliance rejection (V004 only)."""
        if vulnerability_id == "V004":
            return dict(_V004_CORRECT_PATCH)
        return self.generate_patch(vulnerability_id)

    def can_do(self, action: str) -> bool:
        """Return False if *action* is in FORBIDDEN_ACTIONS."""
        return action.lower().strip() not in [a.lower() for a in self.FORBIDDEN_ACTIONS]

    def __repr__(self) -> str:
        return f"SecuritySpecialistAgent(name={self.name!r})"


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agents.code_auditor import CodeAuditorAgent, SAMPLE_VULNERABLE_CODE

    auditor = CodeAuditorAgent()
    specialist = SecuritySpecialistAgent()

    audit = auditor.analyze(SAMPLE_VULNERABLE_CODE)
    assessment = specialist.assess(audit)

    print(f"Assessment ID: {assessment['assessment_id']}")
    for f in assessment["findings"]:
        vid = f["vulnerability_id"]
        patch = f["patch"]
        print(f"\n  [{vid}] Original : {patch.get('original','')[:60]}...")
        print(f"  [{vid}] Fixed    : {patch.get('fixed','')[:60]}...")
        print(f"  [{vid}] CVE Ref  : {patch.get('cve_reference','')}")
