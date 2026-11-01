"""
main.py — ReAct (Reason + Act) Agent for Multi-Cloud Infrastructure Deployment.

Framework: ReAct  (Yao et al., 2022)
Task     : Automated Multi-Cloud Infrastructure Deployment & Health Verification
Scenario : Dynamic replanning when primary-region DB quota is exhausted.
"""

import os
import sys
import json
import textwrap
from typing import Any

# Make sure sibling directory is importable when run directly
sys.path.insert(0, os.path.dirname(__file__))

from tools import (
    ToolError,
    inspect_environment,
    provision_compute,
    deploy_database,
    run_health_checks,
    validate_deployment,
    reset_tool_state,
)

# ---------------------------------------------------------------------------
# Pretty-print helpers
# ---------------------------------------------------------------------------
DIVIDER = "=" * 72


def _box(label: str, content: str, width: int = 72) -> str:
    header = f"{'=' * width}\n  {label}\n{'=' * width}"
    body = textwrap.indent(content, "  ")
    return f"{header}\n{body}\n"


def _dict_pretty(d: dict) -> str:
    return json.dumps(d, indent=2, default=str)


# ---------------------------------------------------------------------------
# Plan step: each step is a named tuple (label, type_key)
# type_key tells act() exactly which tool to call — immune to label changes.
# ---------------------------------------------------------------------------

class PlanStep:
    def __init__(self, label: str, type_key: str):
        self.label = label
        self.type_key = type_key

    def __str__(self):
        return self.label


# ---------------------------------------------------------------------------
# ReAct Agent
# ---------------------------------------------------------------------------

class ReActAgent:
    """
    A ReAct agent that deploys and verifies a multi-cloud infrastructure stack.

    The agent maintains an explicit plan (list of PlanStep), iterates through
    them with a Thought → Action → Observation loop, and can dynamically
    replan when a tool raises a ToolError.
    """

    def __init__(self):
        self.plan: list[PlanStep] = [
            PlanStep("Step 1: Inspect target environment ap-south-1 to understand quota and config", "inspect"),
            PlanStep("Step 2: Provision compute instance (c5.xlarge) in ap-south-1", "provision_compute"),
            PlanStep("Step 3: Deploy database (db.r5.xlarge) in primary region ap-south-1", "deploy_db_primary"),
            PlanStep("Step 4: Run health checks on provisioned compute and database", "health_checks"),
            PlanStep("Step 5: Validate final deployment", "validate"),
        ]
        self.step_index: int = 0
        self.history: list[dict] = []
        self.state: dict[str, Any] = {}
        self.replan_count: int = 0

    # ------------------------------------------------------------------
    # Core ReAct methods
    # ------------------------------------------------------------------

    def think(self, context: str) -> str:
        """
        Generate a Thought string based on the current step and known state.
        In a real LLM-powered agent this would call an LLM; here we produce
        deterministic reasoning strings that mirror what an LLM would say.
        """
        type_key = self.plan[self.step_index].type_key

        thoughts = {
            "inspect": (
                "I need to start by inspecting the target environment ap-south-1. "
                "This will tell me the quota status for both compute and database tiers "
                "before I commit any resources.  If the DB quota is tight I should note "
                "that as a risk and have a fallback region ready."
            ),
            "provision_compute": (
                "Environment inspection is done. "
                f"I can see compute quota is fine, but db_quota_status is "
                f"'{self.state.get('db_quota_status', 'unknown')}' with "
                f"{self.state.get('db_quota_used_pct', '?')}% used — that is a risk. "
                "I will now provision the compute instance as planned (c5.xlarge in ap-south-1). "
                "Even if the DB fails later I want the compute ready."
            ),
            "deploy_db_primary": (
                f"Compute is up: instance_id={self.state.get('instance_id', 'pending')}. "
                "Now I will attempt to deploy the database on the primary region ap-south-1 "
                "with instance type db.r5.xlarge.  I noted the quota warning earlier — "
                "if this fails with ERR_DB_QUOTA_EXCEEDED I must replan and try ap-south-2."
            ),
            "deploy_db_fallback": (
                f"After replanning, I am retrying database deployment in the fallback "
                f"region ap-south-2.  Primary region was quota-exhausted.  "
                f"ap-south-2 has {self.state.get('fallback_db_quota_used_pct', 42)}% quota "
                f"used which is healthy.  Proceeding with db.r5.xlarge in ap-south-2."
            ),
            "health_checks": (
                f"Database is up: db_endpoint={self.state.get('db_endpoint', 'pending')}. "
                "Now I will run the full health-check suite against the compute instance "
                "and the database to confirm everything is reachable and performant."
            ),
            "validate": (
                "Health checks passed — all systems HEALTHY. "
                "Final step is to call validate_deployment for compliance, security, "
                "and cost sign-off before handing over to the operations team."
            ),
        }

        return thoughts.get(
            type_key,
            f"Proceeding with: {self.plan[self.step_index].label}. "
            f"State keys: {list(self.state.keys())}.",
        )

    def act(self, thought: str) -> tuple[str, dict]:
        """
        Decide which tool to invoke based on the step type_key, call it, and
        return (action_description, observation_dict).
        Raises ToolError if the underlying tool does.
        """
        type_key = self.plan[self.step_index].type_key

        if type_key == "inspect":
            action_str = "inspect_environment(target='ap-south-1')"
            obs = inspect_environment("ap-south-1")
            self.state["environment"] = obs
            self.state["db_quota_status"] = obs["db_quota_status"]
            self.state["db_quota_used_pct"] = obs["db_quota_used_pct"]
            return action_str, obs

        elif type_key == "provision_compute":
            action_str = "provision_compute(region='ap-south-1', instance_type='c5.xlarge')"
            obs = provision_compute("ap-south-1", "c5.xlarge")
            self.state["instance_id"] = obs["instance_id"]
            self.state["compute_region"] = obs["region"]
            return action_str, obs

        elif type_key == "deploy_db_primary":
            # FIRST call always raises ToolError (quota exhausted)
            action_str = "deploy_database(region='ap-south-1', db_type='db.r5.xlarge')"
            obs = deploy_database("ap-south-1", "db.r5.xlarge")
            self.state["db_endpoint"] = obs["db_endpoint"]
            self.state["db_region"] = obs["region"]
            return action_str, obs

        elif type_key == "deploy_db_fallback":
            # Replanned fallback — succeeds
            action_str = "deploy_database(region='ap-south-2', db_type='db.r5.xlarge')"
            obs = deploy_database("ap-south-2", "db.r5.xlarge")
            self.state["db_endpoint"] = obs["db_endpoint"]
            self.state["db_region"] = obs["region"]
            return action_str, obs

        elif type_key == "health_checks":
            iid = self.state["instance_id"]
            dbe = self.state["db_endpoint"]
            action_str = f"run_health_checks(instance_id='{iid}', db_endpoint='{dbe}')"
            obs = run_health_checks(iid, dbe)
            self.state["health_status"] = obs["overall_status"]
            return action_str, obs

        elif type_key == "validate":
            iid = self.state["instance_id"]
            dbe = self.state["db_endpoint"]
            action_str = f"validate_deployment(instance_id='{iid}', db_endpoint='{dbe}')"
            obs = validate_deployment(iid, dbe)
            self.state["deployment_id"] = obs.get("deployment_id")
            self.state["validation_status"] = obs["status"]
            return action_str, obs

        else:
            raise RuntimeError(
                f"Unhandled step type_key='{type_key}' at index {self.step_index}"
            )

    def replan(self, error_observation: dict) -> None:
        """
        Called when a ToolError is caught.  Logs what went wrong and
        inserts alternative steps into self.plan at the current position.
        """
        self.replan_count += 1
        error_msg = error_observation.get("error", "Unknown error")
        failed_step = self.plan[self.step_index]

        print(f"\n{'!' * 72}")
        print(f"  ⚠  REPLANNING EVENT #{self.replan_count}")
        print(f"{'!' * 72}")
        print(f"  Failed step : {failed_step.label}")
        print(f"  Error       : {error_msg}")
        print(f"  Strategy    : Replace primary-region DB step with fallback-region step")
        print(f"{'!' * 72}\n")

        # Replace the failed step with the fallback step
        self.plan.pop(self.step_index)
        self.plan.insert(
            self.step_index,
            PlanStep(
                "Step 3b [REPLANNED]: Deploy database (db.r5.xlarge) in FALLBACK region ap-south-2",
                "deploy_db_fallback",
            ),
        )
        # Store fallback quota info for think()
        fallback_env = inspect_environment("ap-south-2")
        self.state["fallback_db_quota_used_pct"] = fallback_env["db_quota_used_pct"]

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Execute the ReAct loop: Thought → Action → Observation for each step.
        On ToolError, trigger replan() and retry the (now-modified) current step.
        """
        print(DIVIDER)
        print("  ReAct Agent: Multi-Cloud Infrastructure Deployment")
        print("  Goal: Deploy compute + database, verify health, validate")
        print(DIVIDER)
        print(f"\nInitial plan ({len(self.plan)} steps):")
        for i, s in enumerate(self.plan, 1):
            print(f"  {i}. {s.label}")
        print()

        trace_lines: list[str] = []

        def record(label: str, content: str):
            block = _box(label, content)
            print(block)
            trace_lines.append(block)

        while self.step_index < len(self.plan):
            current_step = self.plan[self.step_index]
            print(f"\n{'─' * 72}")
            print(f"  STEP {self.step_index + 1}/{len(self.plan)}: {current_step.label}")
            print(f"{'─' * 72}")

            # ── THOUGHT ──────────────────────────────────────────────────
            thought = self.think(current_step.label)
            record("===THOUGHT===", thought)

            # ── ACTION + OBSERVATION ──────────────────────────────────────
            try:
                action_str, observation = self.act(thought)
                record("===ACTION===", action_str)
                record("===OBSERVATION===", _dict_pretty(observation))

                self.history.append(
                    {"thought": thought, "action": action_str, "observation": observation}
                )
                self.step_index += 1

            except ToolError as e:
                failed_action = "deploy_database(region='ap-south-1', db_type='db.r5.xlarge')"
                error_obs = {"error": str(e), "status": "FAILED"}
                record("===ACTION===", failed_action)
                record("===OBSERVATION===", _dict_pretty(error_obs))

                self.history.append(
                    {"thought": thought, "action": failed_action, "observation": error_obs}
                )
                # Trigger replanning — step_index stays the same so loop retries new step
                self.replan(error_obs)

        # ── MISSION COMPLETE ──────────────────────────────────────────────
        summary = (
            "\n" + DIVIDER + "\n"
            "  ✅  MISSION COMPLETE\n"
            + DIVIDER + "\n"
            f"  Total steps executed  : {len(self.history)}\n"
            f"  Replanning events     : {self.replan_count}\n"
            f"  Instance ID           : {self.state.get('instance_id')}\n"
            f"  DB Endpoint           : {self.state.get('db_endpoint')}\n"
            f"  DB Region (final)     : {self.state.get('db_region')}\n"
            f"  Health Status         : {self.state.get('health_status')}\n"
            f"  Validation Status     : {self.state.get('validation_status')}\n"
            f"  Deployment ID         : {self.state.get('deployment_id')}\n"
            + DIVIDER
        )
        print(summary)
        trace_lines.append(summary)

        # ── SAVE TRACE ────────────────────────────────────────────────────
        traces_dir = os.path.join(os.path.dirname(__file__), "traces")
        os.makedirs(traces_dir, exist_ok=True)
        trace_path = os.path.join(traces_dir, "full_run_trace.txt")
        with open(trace_path, "w", encoding="utf-8") as f:
            f.write("\n".join(trace_lines))
        print(f"\n  Full trace saved → {trace_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    reset_tool_state()
    agent = ReActAgent()
    agent.run()
