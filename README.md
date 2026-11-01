# Agentic AI Coursework

Coursework and practical demonstrations for **PE-IV SEM-VII: Agentic AI**. This repository brings together ten assignments covering agent architectures, planning, memory, tool use, multi-agent coordination, and safety.

The examples use local, deterministic Python programs and mock services. They are designed for classroom learning and do not connect to real cloud, healthcare, email, or booking systems.

## Assignments

| # | Unit / activity | Project | Main entry point |
|---|---|---|---|
| 01 | Homework · Unit 2 | ReAct deployment agent with recovery and replanning | `01_Homework_Unit_2_ReAct_Agent/main.py` |
| 02 | Experiential learning · Unit 2 | CoT, ToT, and ReAct planning comparison | `02_Experiential_Learning_Unit_2_Planning_ReAct/compare_planners.py` |
| 03 | Experiential learning · Unit 3 | Agent memory, policy retrieval, and safe computation | `03_Experiential_Learning_Unit_3_Memory_and_Tools/benchmark_evaluation.py` |
| 04 | Homework · Unit 4 | Coordinated multi-agent security audit | `04_Homework_Unit_4_Multi_Agent_Team/run_team.py` |
| 05 | Experiential learning · Unit 4 | Agent handoffs, deadlocks, and error propagation | `05_Experiential_Learning_Unit_4_Team_of_Agents/crew_architecture.py` |
| 06 | Homework · Unit 5 | Domain-specific agent safety guardrails | `06_Homework_Unit_5_Domain_Specific_Agent_Safety/domain_agent.py` |
| 07 | Experiential learning · Unit 5 | Safety and misuse evaluation on synthetic cases | `07_Experiential_Learning_Unit_5_Domain_Specific_Agent/safety_evaluator.py` |
| 08 | Participative learning · Units 1–2 | Agent architecture debate and ReAct trace critique | `08_Participative_Learning_Units_1_and_2/live_demo_critique.py` |
| 09 | Participative learning · Units 3–5 | Agent governance and incident-response simulation | `09_Participative_Learning_Units_3_4_5/incident_simulation.py` |
| 10 | Problem solving · Unit 5 | Analytical guardrail problems and verification | `10_Problem_Solving_Unit_5_Guardrails/guardrail_verification.py` |

Each assignment folder contains its own README with project-specific details and commands. It also includes a `Submission_Documentation.docx` with a workflow diagram, file guide, run instructions, and verification notes.

## Requirements

- Python 3.9 or newer
- No third-party Python packages or API keys are required

## Run the full coursework check

From the repository root, run:

```bash
python3 run_all.py
```

The runner executes the included unit test and the assignment demonstrations, then reports a pass/fail summary. To run one assignment, use the entry point shown in the table above; run commands from the repository root.

## Student

- **Name:** Ameersohiel N Momin
- **Class:** LYAIA4

---

Prepared for Agentic AI coursework, PE-IV SEM-VII.
