# Experiential Learning – Unit 2: Task-Planning Workflows (CoT, ToT, ReAct)

## 1. Goal & Decomposition

**Goal:** *Plan a 3-day business trip to Mumbai within a budget of Rs 25,000 with client meetings.*

All three planners share the same goal but decompose and execute it differently:

| Approach | Decomposition Strategy |
|----------|----------------------|
| **CoT** | Linear 8-step sequence: flights → check meetings → budget → hotel → cab → restaurant → confirm |
| **ToT** | 3-branch tree (Business Hotels / Budget Hotels / Airbnb) with 3 leaf options each; heuristic scoring |
| **ReAct** | 6-step plan with iterative Thought → Action → Observation loops; replans when hotel is sold out |

---

## 2. Planning Errors Each Approach Made

| Approach | Error Encountered | How It Was Handled |
|----------|------------------|-------------------|
| **CoT** | Step 4 – Hotel Trident BKC sold out | ❌ Could not recover; execution halted after step 4 |
| **ToT** | Top-ranked option (Hotel Trident BKC) sold out | ✅ Backtracked to next-best node in the sorted list |
| **ReAct** | Hotel Trident BKC sold out (TravelToolError mid-loop) | ✅ `replan()` inserted fallback step; retried with Ibis Mumbai Airport |

---

## 3. How Replanning Was Triggered and Justified

### Chain-of-Thought (CoT)
CoT **cannot replan**. It executes steps in a fixed order with no error-recovery mechanism.
When Step 4 (`book_hotel`) fails, `execute_plan()` logs the error and returns early.
The remaining 4 steps are never reached.

### Tree-of-Thought (ToT)
ToT's replanning is **proactive**: it evaluates *all* options before committing.
When `inject_failure=True`, the best node is flagged `sold_out` during the search phase.
`search()` simply skips it and picks the next highest-scoring available node.
No mid-execution surprise — the failure is anticipated by the tree structure.

### ReAct
ReAct's replanning is **reactive and mid-execution**:
1. `check_hotel_availability("Hotel Trident BKC", ...)` raises `TravelToolError`.
2. The `run()` loop catches it, records the failed observation in history.
3. `replan()` is called: it **replaces** the failed step in `self.plan` with a new step targeting *"Ibis Mumbai Airport"*.
4. `self.step_index` is not advanced, so the loop re-executes the (now-different) current step.
5. Second call to `check_hotel_availability("Ibis Mumbai Airport", ...)` succeeds.

**Justification:** The fallback hotel (Ibis Mumbai Airport, Rs 2,800/night) keeps total trip cost within the Rs 25,000 budget, satisfying the primary constraint. The agent verified this in Step 5 (`calculate_budget`).

---

## 4. Which Approach Is Most Adaptive?

**ReAct is the most adaptive**, for three reasons:

1. **Real-time feedback loop:** Every action updates `self.state` and influences the next `Thought`. The agent reasons with live observations, not stale pre-computed trees.

2. **Mid-execution replanning:** CoT aborts; ToT pre-computes alternatives but can't reason about new information discovered mid-run. ReAct can insert entirely new steps based on unexpected observations.

3. **Transparency:** Each `===THOUGHT===` block explains *why* the agent is making a decision, making failures and recoveries auditable — critical for enterprise use cases like travel compliance or infrastructure deployments.

**ToT is best for structured exploration** when the option space is known upfront.
**CoT is best for deterministic workflows** where no step can fail (batch data pipelines, etc.).

---

## 5. Comparison Table (inject_failure=True)

| Metric                  | CoT | ToT | ReAct |
|-------------------------|-----|-----|-------|
| Completed successfully  | No  | Yes | Yes   |
| Handled dynamic failure | No  | Yes | Yes   |
| Steps taken             | 4   | 9   | 8     |
| Replanning events       | 0   | 1   | 1     |
| Trace saved             | Yes | Yes | Yes   |

---

## 6. File Structure

```
02_Experiential_Learning_Unit_2_Planning_ReAct/
├── cot_planner.py        # ChainOfThoughtPlanner (linear, no recovery)
├── tot_planner.py        # TreeOfThoughtPlanner (heuristic tree + backtrack)
├── react_workflow.py     # ReActTravelPlanner (Thought/Action/Observation loop)
├── compare_planners.py   # Runs all three; prints comparison table
├── traces/
│   ├── cot_trace.txt
│   ├── tot_trace.txt
│   └── react_trace.txt
└── README.md
```

---

## 7. How to Run

```bash
# Run individual planners
python 02_Experiential_Learning_Unit_2_Planning_ReAct/cot_planner.py
python 02_Experiential_Learning_Unit_2_Planning_ReAct/tot_planner.py
python 02_Experiential_Learning_Unit_2_Planning_ReAct/react_workflow.py

# Run comparison (all three with inject_failure=True)
python 02_Experiential_Learning_Unit_2_Planning_ReAct/compare_planners.py
```
