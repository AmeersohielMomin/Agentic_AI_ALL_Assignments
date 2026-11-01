# Participative Learning - Units I & II

## Course Outcome: CO-1 & CO-2

### Activity Name
Group Debate and Live Demonstration: Agent Architectures and ReAct-Based Reasoning in Practice

---

## 1. Overview & Learning Objectives
This participative module establishes conceptual grounding and critical evaluation across autonomous agent paradigms:
1. **Agent Architecture Debate**: Analyzing trade-offs among Simple Reflex, Model-Based Reflex, Goal-Based, Utility-Based, and Learning Agents across real-world operational domains.
2. **Live Demonstration Critique**: Diagnosing pathology in live ReAct execution traces (e.g., infinite tool loops, declining observation confidence, failure to back off).
3. **Trace Remediation**: Implementing and defending structural fixes including history deques, confidence thresholds, and fallback tool ladders.

---

## 2. Key Files in this Experiment

- `debate_brief.md`: Formal debate briefing paper comparing agent architectures with industrial use cases and hospital triage scenario argumentation.
- `live_demo_critique.py`: Interactive and automated CLI displaying a flawed ReAct reasoning trace side-by-side with an improved, loop-guarded trace.
- `trace_remediation.py`: Automated remediation engine demonstrating loop detection algorithms and confidence-gated tool pivots.

---

## 3. How to Run the Demonstration

```bash
# Run interactive live demonstration (batch/automated mode supported)
python3 live_demo_critique.py --auto

# Run the automated remediation engine
python3 trace_remediation.py
```
