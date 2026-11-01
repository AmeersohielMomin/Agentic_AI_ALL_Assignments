# Experiment 04 — Multi-Agent Team: Code Security Audit

## Shared Task

**Enterprise Automated Code Security Audit & Compliance Patching**

A Python codebase with deliberate security vulnerabilities is passed through a supervised multi-agent pipeline. Each agent has clearly defined responsibilities and cannot perform actions outside its remit.

---

## Agent Role Table

| Agent | Role | Can Do | Cannot Do |
|---|---|---|---|
| `CodeAuditor` | Static analysis | Scan, detect, report | Approve, modify, commit |
| `SecuritySpecialist` | Patch design | Assess, generate fixes | Bypass compliance, commit to production |
| `ComplianceOfficer` | Regulatory gate | Verify, reject, authorize | Write code, invent exceptions |
| `AgentCoordinator` | Supervisor | Orchestrate pipeline | — |

---

## Agent Hand-off Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        COORDINATOR (Supervisor)                     │
└─────────┬───────────────────────────────────────────────┬───────────┘
          │ submit code                                   │ authorize
          ▼                                               │
┌─────────────────┐    audit_report    ┌──────────────────────────────┐
│  CodeAuditor    │ ─────────────────► │  SecuritySpecialist          │
│  (Analyzer)     │                   │  (Patch Designer)            │
└─────────────────┘                   └──────────────┬───────────────┘
                                                     │ patches (incl. hallucinated V004)
                                                     ▼
                                      ┌──────────────────────────────┐
                                      │  ComplianceOfficer           │
                                      │  (Regulatory Gate)           │
                                      │  ✗ REJECTS dangerous V004    │
                                      │  ✓ Requests correct patch    │
                                      │  ✓ Authorizes compliant set  │
                                      └──────────────────────────────┘
```

---

## Vulnerabilities Detected

| ID | Vulnerability | Severity |
|---|---|---|
| V001 | SQL Injection (f-string in execute()) | CRITICAL |
| V002 | Hardcoded passwords in source | HIGH |
| V003 | Dangerous eval() on user input | CRITICAL |
| V004 | Missing authentication on admin endpoint | HIGH |

---

## Hallucination Simulation (V004)

The `SecuritySpecialist` intentionally generates a dangerous patch for V004 that **removes the auth check** under the guise of "performance optimisation".

```python
# HALLUCINATION patch (rejected)
def admin_panel(request):
    # skip_auth_check() ← performance optimisation (DANGEROUS)
    user_data = get_all_users()
    return user_data
```

The `ComplianceOfficer` detects the `HALLUCINATION` and `remove.*auth` patterns and **rejects** the patch. A correct `@require_auth` decorator patch is substituted.

---

## Failure Analysis

### Without Compliance Gate
- The dangerous V004 patch is silently committed.
- Admin endpoint becomes publicly accessible.
- Violates OWASP A01:2021, SOC2 CC6.1, GDPR Art.32.

### With Compliance Gate
- V004 rejection surfaced immediately.
- Coordinator triggers re-patching cycle.
- Correct patch applied and verified before release is authorised.

---

## Mitigation Strategy

1. **Principle of Least Authority** — each agent is only allowed to perform its specific actions.
2. **Mandatory Compliance Gate** — no patch reaches production without `ComplianceOfficer.verify_patch()`.
3. **Re-patch loop** — coordinator re-requests correct patches for all rejected findings before re-submitting.
4. **Immutable audit trail** — full coordination trace saved to `traces/multi_agent_run.txt`.

---

## File Structure

```
04_Homework_Unit_4_Multi_Agent_Team/
├── agents/
│   ├── code_auditor.py         # Static analysis + vulnerable sample
│   ├── security_specialist.py  # Patch generation (with hallucination)
│   └── compliance_officer.py   # Regulatory verification & authorization
├── coordinator.py              # Supervisor pipeline orchestrator
├── failure_mitigation.py       # Before/after compliance gate demo
├── run_team.py                 # Main entry point
├── traces/
│   └── multi_agent_run.txt     # Full coordination trace
└── README.md                   # This document
```
