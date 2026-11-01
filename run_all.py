"""
Agentic AI (PE-IV SEM-VII) - Master Experiment Verification Runner
Executes test suites and verification scripts across all 10 assignment directories.
"""

import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EXPERIMENTS = [
    ("01 - Homework Unit 2: ReAct Agent (Unit Tests)", [sys.executable, "-m", "unittest", "01_Homework_Unit_2_ReAct_Agent/tests/test_replanning.py"]),
    ("02 - Experiential Learning Unit 2: Planning Workflows (CoT / ToT / ReAct)", [sys.executable, "02_Experiential_Learning_Unit_2_Planning_ReAct/compare_planners.py"]),
    ("03 - Experiential Learning Unit 3: Memory & Tools Benchmark", [sys.executable, "03_Experiential_Learning_Unit_3_Memory_and_Tools/benchmark_evaluation.py"]),
    ("04 - Homework Unit 4: Multi-Agent Team Execution", [sys.executable, "04_Homework_Unit_4_Multi_Agent_Team/run_team.py"]),
    ("04 - Homework Unit 4: Failure Mitigation Demo", [sys.executable, "04_Homework_Unit_4_Multi_Agent_Team/failure_mitigation.py"]),
    ("05 - Experiential Learning Unit 4: Crew Architecture", [sys.executable, "05_Experiential_Learning_Unit_4_Team_of_Agents/crew_architecture.py"]),
    ("05 - Experiential Learning Unit 4: Deadlock Breaker", [sys.executable, "05_Experiential_Learning_Unit_4_Team_of_Agents/deadlock_breaker.py"]),
    ("05 - Experiential Learning Unit 4: Error Propagation", [sys.executable, "05_Experiential_Learning_Unit_4_Team_of_Agents/error_propagation_demo.py"]),
    ("06 - Homework Unit 5: Healthcare Safety Agent", [sys.executable, "06_Homework_Unit_5_Domain_Specific_Agent_Safety/domain_agent.py"]),
    ("06 - Homework Unit 5: Indirect Prompt Injection Attack", [sys.executable, "06_Homework_Unit_5_Domain_Specific_Agent_Safety/attacks/indirect_injection.py"]),
    ("07 - Experiential Learning Unit 5: Safety Evaluator", [sys.executable, "07_Experiential_Learning_Unit_5_Domain_Specific_Agent/safety_evaluator.py"]),
    ("08 - Participative Learning Units 1 & 2: Live Demo Critique", [sys.executable, "08_Participative_Learning_Units_1_and_2/live_demo_critique.py", "--auto"]),
    ("08 - Participative Learning Units 1 & 2: Trace Remediation", [sys.executable, "08_Participative_Learning_Units_1_and_2/trace_remediation.py"]),
    ("09 - Participative Learning Units 3, 4 & 5: Incident Simulation", [sys.executable, "09_Participative_Learning_Units_3_4_5/incident_simulation.py"]),
    ("10 - Problem Solving Unit 5: Guardrail Verification", [sys.executable, "10_Problem_Solving_Unit_5_Guardrails/guardrail_verification.py"]),
]

def main():
    print("=" * 80)
    print("  AGENTIC AI (PE-IV SEM-VII) — MASTER EXPERIMENT RUNNER")
    print("=" * 80)

    passed = 0
    failed = 0

    for name, cmd in EXPERIMENTS:
        print(f"\n▶ Running: {name} ...", flush=True)
        res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"  ✅ PASS: {name}")
            passed += 1
        else:
            print(f"  ❌ FAIL: {name}")
            print(res.stderr[:400])
            failed += 1

    print("\n" + "=" * 80)
    print(f"  EXECUTION SUMMARY: {passed}/{len(EXPERIMENTS)} Passed | {failed} Failed")
    print("=" * 80)

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
