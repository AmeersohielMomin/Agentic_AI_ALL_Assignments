# Experiential Learning UNIT-4: Designing a Team of Agents for a Task

## Course Outcome: CO-4 (Multi-Agent Systems and Collaboration)

### Activity Name
Designing a Team of Agents for a Task

---

## 1. System Architecture & Role Separation

Our multi-agent system models an autonomous collaborative research and reporting pipeline with three specialized role-based agents:

| Agent Name | Primary Responsibility | Input Contract | Output Contract |
| :--- | :--- | :--- | :--- |
| **ResearcherAgent** | Domain data gathering from mock research sources | Topic string | List of curated research snippets + sources |
| **WriterAgent** | Synthesizes research into structured markdown sections | Research findings payload | Complete 3-section draft report |
| **EditorAgent** | Quality control, factual consistency, and tone auditing | Draft report | Editorial approval status + critique |

---

## 2. Coordination and Hand-off Protocols

Coordination is implemented via two distinct paradigms:
1. **Direct Sequential Handoff (`crew_architecture.py`)**: High-throughput pipeline where Agent $A$ passes typed state dictionaries to Agent $B$.
2. **Explicit Message-Passing Protocol (`handoff_protocol.py`)**: Formalized asynchronous messaging with immutable message logs, sequence numbering, and delivery acknowledgments.

---

## 3. Failure Modes and Mitigations

### Failure Mode 1: Error Propagation Cascade
- **Problem**: When `DataIngestionAgent` generates an invalid or malformed data payload (e.g., negative revenue string or null user count), downstream agents performing numeric calculations experience unhandled type exceptions, causing total pipeline collapse.
- **Mitigation (`error_propagation_demo.py`)**: Implemented strict input schema validation at every agent boundary. If incoming data fails type or range constraints, the receiving agent flags the issue, applies a defensive fallback baseline, and logs an alert without crashing the downstream pipeline.

### Failure Mode 2: Circular Dependency Deadlock
- **Problem**: In peer-to-peer collaboration, Agent A may halt awaiting an authorization token from Agent B, while Agent B is simultaneously halted awaiting data schemas from Agent A.
- **Mitigation (`deadlock_breaker.py`)**: A supervisory dependency tracker maintains a wait-for directed graph. When DFS detects a cycle ($A \to B \to A$), the `SupervisorArbitrator` breaks the cycle by severing the blocked edge and injecting a pre-approved default payload.

---

## 4. How to Run the Experiments

```bash
# 1. Run main Crew architecture
python3 crew_architecture.py

# 2. Run explicit message-passing handoff protocol
python3 handoff_protocol.py

# 3. Run deadlock detection and resolution simulation
python3 deadlock_breaker.py

# 4. Run error propagation vs mitigation demonstration
python3 error_propagation_demo.py
```
