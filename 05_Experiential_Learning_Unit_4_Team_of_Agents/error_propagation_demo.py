"""
Experiential Learning Unit 4: Team of Agents
error_propagation_demo.py - Multi-Agent Error Propagation and Mitigation

Demonstrates:
1. Scenario A: Unmitigated pipeline where Agent 1 introduces corrupted schema or bad calculation,
   causing cascade failure in Agent 2 and Agent 3.
2. Scenario B: Mitigated pipeline with Input/Output validation contracts and fallback recovery
   at each boundary.
"""

from typing import Dict, Any, Optional


class CorruptedDataException(Exception):
    pass


# ----------------------------------------------------------------------
# Pipeline Agents
# ----------------------------------------------------------------------

class DataIngestionAgent:
    def fetch_metrics(self, corrupt: bool = False) -> Dict[str, Any]:
        if corrupt:
            # Corrupted payload: revenue is negative string, users is None
            return {
                "timestamp": "2026-11-01T12:00:00Z",
                "revenue": "-50000_INVALID",
                "active_users": None,
                "status": "RAW_EXTRACT"
            }
        return {
            "timestamp": "2026-11-01T12:00:00Z",
            "revenue": 150000,
            "active_users": 12500,
            "status": "RAW_EXTRACT"
        }


class AnalyticsAgent:
    def calculate_arpu(self, raw_data: Dict[str, Any], validate: bool = False) -> Dict[str, Any]:
        if validate:
            # Boundary validation
            rev = raw_data.get("revenue")
            users = raw_data.get("active_users")
            if not isinstance(rev, (int, float)) or rev < 0:
                print("  [AnalyticsAgent Validator] Flagged corrupt revenue! Applying default fallback.")
                rev = 0
            if not isinstance(users, int) or users <= 0:
                print("  [AnalyticsAgent Validator] Flagged corrupt users! Applying default fallback.")
                users = 1
            arpu = rev / users
            return {
                "arpu": round(arpu, 2),
                "total_revenue": rev,
                "users": users,
                "is_fallback": True
            }

        # Unvalidated execution: direct arithmetic causes TypeError / ValueError
        rev = raw_data["revenue"]
        users = raw_data["active_users"]
        # Will raise TypeError or ValueError
        arpu = float(rev) / users
        return {"arpu": arpu, "total_revenue": rev, "users": users}


class ExecutiveReportAgent:
    def generate_report(self, analytics_result: Optional[Dict[str, Any]]) -> str:
        if not analytics_result or "arpu" not in analytics_result:
            return "❌ EXECUTIVE REPORT FAILED: Empty or garbage analytics payload received."
        return (f"📊 EXECUTIVE SUMMARY:\n"
                f"   Total Revenue : Rs. {analytics_result.get('total_revenue')}\n"
                f"   Active Users  : {analytics_result.get('users')}\n"
                f"   Average ARPU  : Rs. {analytics_result.get('arpu')}\n"
                f"   Data Integrity: {'FALLBACK_ESTIMATE' if analytics_result.get('is_fallback') else 'VERIFIED'}")


def run_demonstration():
    print("=" * 70)
    print("  MULTI-AGENT ERROR PROPAGATION VS MITIGATION DEMO")
    print("=" * 70)

    ingest = DataIngestionAgent()
    analytics = AnalyticsAgent()
    executive = ExecutiveReportAgent()

    print("\n[SCENARIO A] Unmitigated Pipeline (Error Propagation Cascade)")
    print("  Trigger: DataIngestionAgent emits corrupted payload.")
    corrupt_data = ingest.fetch_metrics(corrupt=True)
    print(f"  Step 1: DataIngestionAgent emitted: {corrupt_data}")

    try:
        print("  Step 2: AnalyticsAgent attempting calculation without validation...")
        analytics_out = analytics.calculate_arpu(corrupt_data, validate=False)
        report = executive.generate_report(analytics_out)
        print(f"  Step 3: ExecutiveReportAgent output:\n{report}")
    except Exception as e:
        print(f"  💥 CASCADE CRASH at AnalyticsAgent: {type(e).__name__}: {e}")
        print("  Step 3: ExecutiveReportAgent never received data. Downstream pipeline dead.")
        print("  Result: Entire multi-agent coordination failed due to single unhandled error.")

    print("\n" + "-" * 70)
    print("\n[SCENARIO B] Mitigated Pipeline (Boundary Contracts & Fallback Recovery)")
    print("  Trigger: Same corrupted payload injected.")
    print(f"  Step 1: DataIngestionAgent emitted corrupt payload.")

    try:
        print("  Step 2: AnalyticsAgent running with Boundary Validation enabled...")
        analytics_out = analytics.calculate_arpu(corrupt_data, validate=True)
        print(f"  Step 2 Output: {analytics_out}")

        print("  Step 3: ExecutiveReportAgent receiving sanitized payload...")
        report = executive.generate_report(analytics_out)
        print(report)
        print("  ✅ SUCCESS: Error caught at boundary; pipeline completed safely with fallback.")
    except Exception as e:
        print(f"  Unexpected crash: {e}")

    print("=" * 70)


if __name__ == "__main__":
    run_demonstration()
