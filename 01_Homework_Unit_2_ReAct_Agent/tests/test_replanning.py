"""
tests/test_replanning.py — Unit tests for the ReAct Infrastructure Agent.
Run with:  python -m unittest 01_Homework_Unit_2_ReAct_Agent/tests/test_replanning.py -v
"""

import sys
import os
import unittest

# Make the parent package importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools import reset_tool_state
from main import ReActAgent


class TestReActReplanning(unittest.TestCase):
    """Validate that the ReAct agent correctly handles the DB quota failure."""

    @classmethod
    def setUpClass(cls):
        """Run the agent once; all test methods share the same result."""
        reset_tool_state()
        cls.agent = ReActAgent()
        cls.agent.run()

    # ------------------------------------------------------------------
    # Core assertions
    # ------------------------------------------------------------------

    def test_replanning_occurred(self):
        """Agent must have triggered at least one replanning event."""
        self.assertGreaterEqual(
            self.agent.replan_count,
            1,
            msg=f"Expected replan_count >= 1, got {self.agent.replan_count}",
        )

    def test_db_endpoint_captured(self):
        """Agent must have saved a db_endpoint in its state after replanning."""
        endpoint = self.agent.state.get("db_endpoint")
        self.assertIsNotNone(
            endpoint,
            msg="db_endpoint should be set in agent.state after successful fallback deployment",
        )
        self.assertIn("ap-south-2", endpoint, msg="Endpoint should reference the fallback region")

    def test_instance_id_captured(self):
        """Agent must have saved an instance_id from the compute provisioning step."""
        instance_id = self.agent.state.get("instance_id")
        self.assertIsNotNone(
            instance_id,
            msg="instance_id should be set in agent.state after compute provisioning",
        )

    def test_history_structure(self):
        """Every history entry must have 'thought', 'action', and 'observation' keys."""
        self.assertGreater(len(self.agent.history), 0, msg="History should not be empty")
        for i, entry in enumerate(self.agent.history):
            for key in ("thought", "action", "observation"):
                self.assertIn(
                    key,
                    entry,
                    msg=f"History entry {i} is missing key '{key}'. Entry keys: {list(entry.keys())}",
                )

    def test_health_status_healthy(self):
        """Health checks must report HEALTHY after successful replanning."""
        self.assertEqual(
            self.agent.state.get("health_status"),
            "HEALTHY",
            msg="health_status should be 'HEALTHY'",
        )

    def test_validation_passed(self):
        """Final validation must succeed (status == VALIDATED)."""
        self.assertEqual(
            self.agent.state.get("validation_status"),
            "VALIDATED",
            msg="validation_status should be 'VALIDATED'",
        )

    def test_trace_file_created(self):
        """Trace file must exist after agent.run()."""
        trace_path = os.path.join(
            os.path.dirname(__file__), "..", "traces", "full_run_trace.txt"
        )
        self.assertTrue(
            os.path.isfile(trace_path),
            msg=f"Trace file not found at {trace_path}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
