# Experiment 07 — Domain Agent Safety Evaluator

## Activity Report

---

## 1. Evaluation Methodology

The Safety Evaluator runs all 20 test cases from `test_cases.json` through the same three-layer guardrail pipeline used in Experiment 06:

**Pipeline:** `InputGuard → ToolCallGuard → OutputGuard`

For each test case the evaluator:
1. Feeds the input text through **InputGuard** — checks for injection patterns and PII
2. Heuristically infers the implied tool call and feeds it to **ToolCallGuard** — checks dosage and operation risk
3. Feeds the text through **OutputGuard** — checks for unknown drugs and sensitive fields
4. Records whether the case was blocked, by which layer, and whether that outcome was correct

---

## 2. Test Case Categories

| Category | Count | Description |
|----------|-------|-------------|
| `normal_query` | 5 | Legitimate clinical queries that should PASS |
| `jailbreak` | 4 | Direct prompt-injection attempts targeting the LLM's persona |
| `indirect_injection` | 4 | Injections hidden in data payloads (patient notes, lab results) |
| `dosage_hallucination` | 4 | Requests for dangerous or non-existent drug doses |
| `pii_exfiltration` | 2 | Inputs containing Aadhaar-like or PAN-like PII |
| `social_engineering` | 1 | Authority impersonation to bypass controls |

---

## 3. Mitigation Pipeline Architecture

```
 Input String
      │
      ▼
┌─────────────┐
│  InputGuard │  ← Regex injection detection, PII redaction
└──────┬──────┘
       │ safe=True
       ▼
┌─────────────┐
│   Agent     │  ← Simulated LLM reasoning step (sanitized input only)
└──────┬──────┘
       │ proposed tool call
       ▼
┌──────────────────┐
│  ToolCallGuard   │  ← Dosage ceiling enforcement, operation allowlist
└──────┬───────────┘
       │ approved (HIGH RISK → gate)
       ▼
┌──────────────────────┐
│  HumanApprovalGate   │  ← Physician sign-off for HIGH RISK operations
└──────┬───────────────┘
       │ approved
       ▼
┌─────────────┐
│ OutputGuard │  ← Sensitive field redaction, hallucination detection
└──────┬──────┘
       │
       ▼
  Final Result + Audit Trail
```

### Source Grounding Check

The `MitigationPipeline.source_grounding_check(claim, source_docs)` method:
- Tokenises the claim into content keywords (removing stop words)
- Checks each source document for keyword containment
- Requires ≥40% keyword overlap to declare SUPPORTED
- Returns verdict, matched source excerpt, and matched keywords

---

## 4. Scorecard — Before vs After Guardrails

| Metric | Without Guardrails | With Guardrails |
|--------|-------------------|-----------------|
| Total test cases | 20 | 20 |
| Attack cases | 15 | 15 |
| Normal query cases | 5 | 5 |
| Attacks blocked (TP) | 6 (40%) | 13 (87%) |
| PII attacks redacted | 0 | 2 (13%) |
| Attacks mitigated | 6 (40%) | 15 (100%) |
| Attacks missed (FN) | 9 (60%) | 0 |
| False positives (FP) | 0 | 0 |
| Overall accuracy | 55% | **100%** |

> **Key finding:** On this synthetic benchmark, the pipeline blocked 13 attacks and redacted PII in 2 more, with zero false positives on the normal query set. The evaluator uses lightweight text heuristics, and the baseline without guardrails is a configured comparison estimate, not a measured run.

---

## 5. Key Findings

1. **InputGuard** is the most effective single layer — catches all direct jailbreaks and indirect injections at the text level before the LLM sees the payload.

2. **ToolCallGuard** is the safety net for attacks that survive InputGuard — dosage ceiling enforcement is deterministic and cannot be bypassed by prompt manipulation.

3. **OutputGuard** catches hallucinated drug names in agent responses — critical for clinical safety.

4. **Defense-in-depth** matters: no single layer catches all attacks. On this test suite, the layers block injection and unsafe tool calls, while the input guard redacts PII before it reaches the simulated agent.

---

## 6. Files

```
07_Experiential_Learning_Unit_5_Domain_Specific_Agent/
├── test_cases.json          # 20 labelled test cases across 6 categories
├── safety_evaluator.py      # Automated evaluation + scorecard generator
├── mitigation_pipeline.py   # Full chained pipeline with source grounding
├── evaluation_report.txt    # Generated evaluation report (after run)
└── README.md                # This document
```
