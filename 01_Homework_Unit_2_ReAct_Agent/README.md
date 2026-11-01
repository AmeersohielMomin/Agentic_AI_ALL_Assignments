# Homework – Unit 2: ReAct Reasoning Agent

## 1. Goal & Sub-Task Decomposition

**Goal:** Automate end-to-end Multi-Cloud Infrastructure Deployment and Health Verification using the **ReAct (Reason + Act)** framework.

The agent decomposes the goal into 5 ordered sub-tasks:

| # | Sub-Task | Tool |
|---|----------|------|
| 1 | Inspect environment (quotas, config) | `inspect_environment` |
| 2 | Provision compute instance | `provision_compute` |
| 3 | Deploy managed database | `deploy_database` |
| 4 | Run health checks | `run_health_checks` |
| 5 | Validate deployment | `validate_deployment` |

---

## 2. Thought / Action / Observation Trace (Summary)

> Full trace is saved in `traces/full_run_trace.txt`.

**Step 1 – Inspect Environment**
- 🧠 *Thought:* "I need to inspect ap-south-1 to understand quota status before provisioning."
- ⚡ *Action:* `inspect_environment(target='ap-south-1')`
- 👁 *Observation:* `db_quota_status: "warning"`, 94% used — risk flag raised.

**Step 2 – Provision Compute**
- 🧠 *Thought:* "Compute quota is fine; DB quota is at 94% — I should note the risk."
- ⚡ *Action:* `provision_compute(region='ap-south-1', instance_type='c5.xlarge')`
- 👁 *Observation:* `instance_id: "i-xxxxxxxx"` — success.

**Step 3 – Deploy Database (FAILS → REPLANNING)**
- 🧠 *Thought:* "Attempt primary region; be ready to fallback if quota fails."
- ⚡ *Action:* `deploy_database(region='ap-south-1', db_type='db.r5.xlarge')`
- 👁 *Observation:* `ToolError: ERR_DB_QUOTA_EXCEEDED` — triggers replanning event.

**Step 3b – Deploy Database (Replanned – Fallback Region)**
- ⚠️ *Replan:* Swap primary step for fallback region ap-south-2.
- 🧠 *Thought:* "Primary region quota exhausted; retrying in ap-south-2 (42% quota used)."
- ⚡ *Action:* `deploy_database(region='ap-south-2', db_type='db.r5.xlarge')`
- 👁 *Observation:* `db_endpoint: "db-cluster-ap-south-2.internal.aws.com:5432"` — success.

**Step 4 – Health Checks**
- ⚡ *Action:* `run_health_checks(instance_id=..., db_endpoint=...)`
- 👁 *Observation:* `overall_status: "HEALTHY"` — all 6 sub-checks PASS.

**Step 5 – Validate Deployment**
- ⚡ *Action:* `validate_deployment(instance_id=..., db_endpoint=...)`
- 👁 *Observation:* `status: "VALIDATED"` — compliance, security, performance all PASS.

---

## 3. The Replanning Case

### What Went Wrong
`deploy_database` on `ap-south-1` with `db.r5.xlarge` raised a hard `ToolError`:
```
ERR_DB_QUOTA_EXCEEDED: Primary region ap-south-1 quota limit reached for db.r5.xlarge.
```

### How the Agent Noticed
The `act()` method wraps tool calls in a `try/except ToolError` block inside `run()`.
When the exception fires, the agent does **not** crash — it captures the error as an `observation`, records it in `history`, and calls `replan()`.

### What It Changed
`replan()` performs an **in-place plan surgery**:
1. Pops the failed step from `self.plan` at the current index.
2. Inserts a new step: *"Deploy database in FALLBACK region ap-south-2"*.
3. Does **not** advance `self.step_index`, so the loop retries the (now-different) current step automatically.
4. Increments `self.replan_count` for telemetry.

The fallback call to `deploy_database(region='ap-south-2', ...)` succeeds on the second global invocation, and execution continues normally.

---

## 4. Where ReAct Helped vs. Struggled

| Aspect | Assessment |
|--------|-----------|
| **Helped: Explicit Reasoning** | The *Thought* step gave the agent a chance to flag the 94% DB quota warning *before* the failure, making the replan decision transparent and justifiable. |
| **Helped: Mid-Loop Adaptability** | Because the plan is a mutable list, inserting a fallback step mid-execution required no framework changes — the loop naturally picked up the new step. |
| **Struggled: State Management** | Accumulated state (`instance_id`, `db_endpoint`) must be manually threaded through the `act()` and `replan()` methods; with more steps this becomes fragile and error-prone without a proper state machine. |

---

## 5. File Structure

```
01_Homework_Unit_2_ReAct_Agent/
├── tools.py                  # 5 mock tools + ToolError
├── main.py                   # ReActAgent class + entry point
├── tests/
│   └── test_replanning.py    # 6 unittest assertions
├── traces/
│   └── full_run_trace.txt    # Complete Thought/Action/Observation log
└── README.md
```

---

## 6. How to Run

```bash
# Run the agent
python 01_Homework_Unit_2_ReAct_Agent/main.py

# Run tests
python -m unittest 01_Homework_Unit_2_ReAct_Agent/tests/test_replanning.py -v
```
