# Problem Solving - Unit 5 (Applications, Safety and Guardrails)

## Course Outcome: CO-5 (Applications, Ethics and Future Trends)

### Submission Overview
This document and directory contain the complete, rigorous analytical solutions to all **six assigned problems** for Unit 5, accompanied by an executable Python test harness demonstrating each guardrail, grounding verifier, and action read-back check.

---

## Content Index

1. `problem_solutions.md`: Full step-by-step written answers to Problems 1 through 6, fully developed in student's own words with architectural justifications.
   - **Problem 1**: Autonomy by cost of mistake analysis for five real-world enterprise operations.
   - **Problem 2**: The Three Ingredients analysis, indirect prompt injection vectors, three defense layers, and non-neural failure boundaries.
   - **Problem 3**: Guarded pipeline architectural diagram and end-to-end attack propagation trace through each inspection box.
   - **Problem 4**: Policy grounding check on four customer claims with formal justifications and policy corrections.
   - **Problem 5**: Dual read-back verification design (storage verification and SMTP MTA confirmation) with failure recovery protocols.
   - **Problem 6**: Analysis matching real-world failure cases to controls (`Ground`, `Verify`, `Gate`, `Restrict`).

2. `guardrail_verification.py`: Executable Python test script modeling the guarded pipeline, demonstrating indirect injection blocking, automated claim grounding evaluation, and action read-back checks.

---

## How to Run the Verification Script

```bash
python3 guardrail_verification.py
```
