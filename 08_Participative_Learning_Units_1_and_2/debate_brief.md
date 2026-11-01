# Experiment 08 — Debate Brief: Agent Architectures & ReAct Reasoning

---

## Part 1: Agent Architecture Types

---

### 1. Simple Reflex Agent

**Definition:** An agent that selects actions purely based on the current percept, using condition-action rules ("if X then do Y"). It has no memory of past states.

**How it works:**
1. Perceives the current environment state
2. Matches the percept against a rule table
3. Executes the matched action
4. Repeats — no history or future planning involved

**Real-world example:** A room thermostat — if temperature < set-point → turn on heat; if temperature > set-point → turn off heat.

**Strengths:**
- Extremely fast (O(1) lookup)
- Deterministic and auditable
- Simple to build, test, and certify

**Weaknesses:**
- Completely blind to history — cannot distinguish "patient just arrived" from "patient has been waiting 4 hours"
- Fails in partially observable environments
- Cannot handle novel situations not covered by its rule set

**When to choose it:** Fixed, fully observable, time-critical environments where rules can be exhaustively enumerated (industrial safety cut-offs, hardware interlocks).

---

### 2. Model-Based Reflex Agent

**Definition:** Extends the simple reflex agent with an internal state — a model of how the world evolves — allowing it to handle partial observability.

**How it works:**
1. Maintains an internal state updated by: (a) the previous state, (b) the last action taken, (c) the new percept
2. Uses condition-action rules over the internal state + current percept
3. The internal model fills in "unseen" parts of the environment

**Real-world example:** A robot vacuum cleaner that maps rooms it has visited, so it doesn't re-clean areas already covered.

**Strengths:**
- Handles partial observability gracefully
- Can track evolving situations (patient condition changing over time)
- More robust than simple reflex in dynamic environments

**Weaknesses:**
- Model accuracy is critical — stale or wrong models lead to bad decisions
- More complex to maintain and debug
- Still no goal-directed planning

**When to choose it:** Environments that change over time and cannot be fully observed at once (inventory systems, patient monitoring with intermittent sensor data).

---

### 3. Goal-Based Agent

**Definition:** An agent that acts to achieve explicit goals, using search or planning to find action sequences that lead from the current state to the goal state.

**How it works:**
1. Maintains an internal model of the world (like model-based reflex)
2. Has one or more explicit goal conditions
3. Uses search (BFS, A*, MCTS) or planning (STRIPS, HTN) to find a path to the goal
4. Executes the plan, re-plans if environment changes

**Real-world example:** Google Maps navigation — given a destination (goal), plans a route through the road network, re-routes if conditions change.

**Strengths:**
- Flexible — same architecture can pursue different goals without redesign
- Can handle novel situations by searching for new plans
- Transparent about *why* it chose an action (traceability)

**Weaknesses:**
- Planning is computationally expensive (can be NP-hard)
- Goals must be precisely defined — ambiguous goals lead to wrong plans
- Brittle if the world model diverges from reality

**When to choose it:** Complex multi-step tasks with clear success criteria (logistics routing, automated scheduling, triage routing when criteria are well-defined).

---

### 4. Utility-Based Agent

**Definition:** Extends goal-based agents by replacing binary goal satisfaction with a continuous utility function, allowing the agent to trade off multiple competing objectives.

**How it works:**
1. Maintains world model + utility function over states
2. When choosing between actions, selects the action that maximises expected utility
3. Can handle uncertainty by computing expected utility across probability distributions of outcomes

**Real-world example:** An airline seat-assignment system balancing passenger preferences, revenue optimisation, fuel load distribution, and ground crew turnaround time simultaneously.

**Strengths:**
- Gracefully handles multiple competing objectives
- Natural handling of uncertainty (expected utility)
- Can encode domain expertise as utility weights

**Weaknesses:**
- Utility function design is extremely hard — wrong utility → misaligned behaviour
- Computationally expensive in large state spaces
- "Reward hacking" — agent exploits loopholes in the utility function

**When to choose it:** Multi-objective optimisation problems where outcomes have different degrees of desirability (resource allocation, personalised treatment recommendations).

---

### 5. Learning Agent

**Definition:** An agent that improves its own performance over time using feedback from the environment, without being explicitly reprogrammed.

**How it works:**
1. **Performance element:** Selects actions (can be any of the above architectures)
2. **Critic:** Evaluates the outcome against a performance standard
3. **Learning element:** Modifies the performance element based on critic feedback
4. **Problem generator:** Suggests exploratory actions to discover new knowledge

**Real-world example:** AlphaFold — learned protein structure prediction from evolutionary sequence data, outperforming decades of hand-crafted bioinformatics rules.

**Strengths:**
- Adapts to novel situations without manual reprogramming
- Can discover non-obvious patterns in high-dimensional data
- Improves continuously with more data/experience

**Weaknesses:**
- Unpredictable in out-of-distribution situations
- Requires large amounts of training data
- Hard to audit or certify for safety-critical domains
- Can learn and amplify biases present in training data

**When to choose it:** Large-scale pattern recognition problems where rules cannot be hand-crafted (medical image diagnosis, NLP, fraud detection) — subject to rigorous evaluation before deployment.

---

## Part 2: Debate — "Which Architecture is Best for a Hospital Triage System?"

### Candidate Architectures: Goal-Based vs Utility-Based vs Learning Agent

---

#### Architecture A: Goal-Based Agent

**PRO:** Triage has explicit, auditable goals — "identify life-threatening conditions in <5 minutes, route to correct ward." A goal-based agent's decision trace can be shown to regulators and reviewed by clinicians. In a safety-critical environment, explainability is non-negotiable.

**CON:** Real triage involves competing priorities (severity vs bed availability vs patient risk tolerance). Binary goal satisfaction cannot capture these trade-offs — a goal-based agent may optimise one goal while ignoring others.

---

#### Architecture B: Utility-Based Agent

**PRO:** Triage is inherently a multi-objective problem. A utility function can encode: (a) severity urgency (highest weight), (b) expected treatment time, (c) patient preference, (d) resource availability. The agent makes principled trade-offs rather than rigid rule-following.

**CON:** Designing the utility function is dangerously difficult. A wrong weight on "bed utilisation efficiency" vs "patient mortality risk" could lead to systematic under-triaging of lower-acuity patients who deteriorate. Utility function errors in healthcare = patient harm.

---

#### Architecture C: Learning Agent (LLM-based ReAct)

**PRO:** A learning agent can recognise complex, non-standard presentations (e.g., atypical MI in women, silent stroke) that rule-based systems miss. It can generalise from millions of case histories.

**CON:** In a domain where errors are life-threatening, the unpredictability of a learning agent is an unacceptable regulatory risk. It cannot be reliably audited, and its outputs can be manipulated (prompt injection, adversarial inputs). Medical certification bodies (FDA, CDSCO) require explainability that LLMs cannot currently provide for autonomous clinical decisions.

---

**Group Consensus:** A **hybrid** architecture is most appropriate — a utility-based agent for structured triage scoring (ESI/MTS scale) with goal-based routing, enhanced by a learning agent in an **advisory-only** role (surfacing differential diagnoses for clinician review, flagged with confidence scores). No fully autonomous learning agent should make final triage decisions.

---

## Part 3: Group Critique — Common ReAct Reasoning Errors

### Error 1: Tool-Call Loop Without Progress Detection

**Description:** The agent calls the same search/retrieval tool repeatedly with nearly identical queries, receiving similar results each time, without recognising it is stuck.

**Root cause:** No mechanism to compare current action with previous actions; no diminishing-returns check; no loop counter.

**Proposed improvement:** Maintain a `recent_actions` deque of the last N tool calls. Before executing a tool, compute a similarity score between the proposed call and the last 2 calls. If similarity > 0.85, trigger "alternative action selection" — choose a different tool or reformulate the query.

---

### Error 2: Acting on Low-Confidence Intermediate Results

**Description:** The agent proceeds to the next reasoning step despite the current step returning a low-confidence or ambiguous result (e.g., a search returning "0 results" or a tool returning an error code), treating the absence of information as if it were a confirmed negative.

**Root cause:** No confidence-score gate between the Observation step and the next Thought step.

**Proposed improvement:** After each tool call, require the agent to explicitly score its confidence (0–100) in the observation. If confidence < threshold (e.g., 40%), branch to a "fallback strategy" — try an alternative tool, ask a clarifying question, or escalate to a human.

---

### Error 3: Premature Goal Declaration Without Verification

**Description:** The agent declares "Task complete" after taking an action (e.g., "file saved", "email sent") without verifying the action actually succeeded — relying on the tool's success status code without independently confirming the real-world effect.

**Root cause:** No "read-back verification" step after write operations; tool success is assumed rather than confirmed.

**Proposed improvement:** For all write/side-effect operations, add a mandatory post-action verification step: query the affected system to confirm the change (check file exists + size > 0, check email delivery log, check DB record updated). Only declare success after positive verification. If verification fails, set task status to `FAILED_VERIFICATION` and notify the user.
