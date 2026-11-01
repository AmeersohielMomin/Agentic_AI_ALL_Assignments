# Participative Learning - Units III, IV & V

## Course Outcome: CO-3, CO-4 & CO-5

### Activity Name
Panel Discussion and Role-Play: Building, Coordinating, and Governing Real-World Agentic AI Systems

---

## 1. Overview & Objectives
This participative module addresses the multi-disciplinary governance challenges that emerge when deploying autonomous agents with persistent memory, external tool access, and collaborative multi-agent hand-offs in enterprise environments.

The activity evaluates:
- **Memory & Privacy Trade-offs**: Persistent vector memory vs. GDPR Right-to-be-Forgotten.
- **Autonomous Tool Risk**: Unilateral execution vs. human approval gates in financial and sensitive operations.
- **Multi-Agent Error Cascades & Prompt Injections**: Establishing zero-trust inter-agent boundaries.

---

## 2. Key Files & Artifacts

1. `roleplay_script.md`: Comprehensive 3-stakeholder script capturing technical arguments between the Lead AI Systems Architect, Head of Operations, and Chief AI Safety & Compliance Officer.
2. `governance_framework.md`: Exhaustive 8-dimension policy matrix providing consensus mandates across memory retention, tool privileges, prompt injection defense, audit trails, and kill switches.
3. `incident_simulation.py`: Executable Python simulation modeling an autonomous multi-agent incident response crew (ThreatDetector, ForensicAnalyst, IncidentCommander, NotificationAgent) isolating and neutralizing an indirect prompt injection attack.

---

## 3. How to Run the Simulation

```bash
python3 incident_simulation.py
```
