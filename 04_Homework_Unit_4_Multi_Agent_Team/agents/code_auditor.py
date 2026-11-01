"""
CodeAuditorAgent
================
Performs static pattern-matching analysis on Python code to detect
common security vulnerabilities.  NEVER modifies files or approves code.
"""

import re
import uuid
import datetime


# ---------------------------------------------------------------------------
# Sample vulnerable code that the agent is asked to analyse
# ---------------------------------------------------------------------------

SAMPLE_VULNERABLE_CODE = '''
import sqlite3
import os

# Hardcoded password — security violation
password = "admin123"
db_password = "supersecret"

def get_user(username):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    # SQL Injection vulnerability
    cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
    return cursor.fetchone()

def run_user_input(user_code):
    # Dangerous eval usage
    result = eval(user_code)
    return result

def admin_panel(request):
    # Missing authentication check
    user_data = get_all_users()
    return user_data

def get_all_users():
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()
'''


# ---------------------------------------------------------------------------
# Detection rules
# ---------------------------------------------------------------------------

_VULNERABILITY_PATTERNS = [
    {
        "id": "V001",
        "name": "SQL Injection",
        "pattern": re.compile(r"execute\s*\(\s*f['\"].*\{", re.IGNORECASE),
        "severity": "CRITICAL",
        "recommendation": "Use parameterised queries: cursor.execute('SELECT * FROM users WHERE username = ?', (username,))",
    },
    {
        "id": "V002",
        "name": "Hardcoded Password",
        "pattern": re.compile(r'(?:password|passwd|pwd|secret)\s*=\s*["\'][^"\']{3,}["\']', re.IGNORECASE),
        "severity": "HIGH",
        "recommendation": "Store credentials in environment variables or a secrets manager (e.g., os.environ['DB_PASSWORD']).",
    },
    {
        "id": "V003",
        "name": "Dangerous eval() Usage",
        "pattern": re.compile(r'\beval\s*\(', re.IGNORECASE),
        "severity": "CRITICAL",
        "recommendation": "Remove eval(). Use ast.literal_eval() for data parsing or redesign the feature.",
    },
    {
        "id": "V004",
        "name": "Missing Authentication Check",
        "pattern": re.compile(r'def\s+admin\w*\s*\([^)]*\)\s*:\s*\n(?!\s*(if|auth|token|login|session|verify|check|require))', re.IGNORECASE),
        "severity": "HIGH",
        "recommendation": "Add @require_auth decorator or explicit session/token verification before exposing admin endpoints.",
    },
]


class CodeAuditorAgent:
    """
    Static code analysis agent.

    Responsibilities:
        - Scan code for known vulnerability patterns.
        - Report findings with severity ratings.
        - NEVER approve, modify, or commit code.
    """

    name: str = "CodeAuditor"
    role: str = "Static code analysis and vulnerability detection"

    FORBIDDEN_ACTIONS: list[str] = [
        "approve code",
        "modify files",
        "commit changes",
    ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, code_snippet: str) -> dict:
        """
        Scan *code_snippet* for vulnerabilities.

        Returns
        -------
        dict
            {audit_id, vulnerabilities, severity, recommendations, timestamp}
        """
        vulnerabilities = []
        recommendations = []
        max_severity = "NONE"
        severity_rank = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

        for rule in _VULNERABILITY_PATTERNS:
            if rule["pattern"].search(code_snippet):
                vuln_entry = f"[{rule['id']}] {rule['name']} (Severity: {rule['severity']})"
                vulnerabilities.append(vuln_entry)
                recommendations.append(f"[{rule['id']}] {rule['recommendation']}")
                if severity_rank[rule["severity"]] > severity_rank[max_severity]:
                    max_severity = rule["severity"]

        audit_id = f"AUDIT-{uuid.uuid4().hex[:8].upper()}"
        return {
            "audit_id": audit_id,
            "vulnerabilities": vulnerabilities,
            "severity": max_severity,
            "recommendations": recommendations,
            "timestamp": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "lines_scanned": len(code_snippet.splitlines()),
        }

    def can_do(self, action: str) -> bool:
        """Return False if *action* is in FORBIDDEN_ACTIONS."""
        return action.lower().strip() not in [a.lower() for a in self.FORBIDDEN_ACTIONS]

    def __repr__(self) -> str:
        return f"CodeAuditorAgent(name={self.name!r})"


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = CodeAuditorAgent()
    report = agent.analyze(SAMPLE_VULNERABLE_CODE)
    print(f"Audit ID : {report['audit_id']}")
    print(f"Severity : {report['severity']}")
    print(f"Findings :")
    for v in report["vulnerabilities"]:
        print(f"  {v}")
    print(f"\nRecommendations:")
    for r in report["recommendations"]:
        print(f"  {r}")
    print(f"\nCan approve code? {agent.can_do('approve code')}")
    print(f"Can analyze?      {agent.can_do('analyze')}")
