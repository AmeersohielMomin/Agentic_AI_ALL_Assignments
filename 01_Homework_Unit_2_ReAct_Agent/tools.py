"""
tools.py — Mock tools for the ReAct Multi-Cloud Infrastructure Deployment Agent.
All responses are deterministic and require no external API keys.
"""

# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class ToolError(Exception):
    """Raised when a tool encounters a non-recoverable error."""
    pass


# ---------------------------------------------------------------------------
# Call counter (used to simulate first-call failure of deploy_database)
# ---------------------------------------------------------------------------
_db_call_count = 0


def reset_tool_state():
    """Reset global counters (useful for unit tests)."""
    global _db_call_count
    _db_call_count = 0


# ---------------------------------------------------------------------------
# Tool 1: inspect_environment
# ---------------------------------------------------------------------------

def inspect_environment(target: str) -> dict:
    """
    Returns configuration info about the target deployment environment.
    Deliberately surfaces a quota warning for the database tier so the
    ReAct agent can reason about it before the failure occurs.
    """
    environments = {
        "ap-south-1": {
            "region": "ap-south-1",
            "cloud_provider": "AWS",
            "compute_quota_status": "OK",
            "compute_available_types": ["t3.medium", "c5.xlarge", "r5.large"],
            "db_quota_status": "warning",          # <-- signals risk
            "db_available_types": ["db.r5.xlarge"],
            "db_quota_used_pct": 94,
            "networking": "VPC-enabled",
            "notes": "DB quota nearly exhausted — consider fallback region ap-south-2",
        },
        "ap-south-2": {
            "region": "ap-south-2",
            "cloud_provider": "AWS",
            "compute_quota_status": "OK",
            "compute_available_types": ["t3.medium", "c5.xlarge"],
            "db_quota_status": "OK",
            "db_available_types": ["db.r5.xlarge", "db.t3.medium"],
            "db_quota_used_pct": 42,
            "networking": "VPC-enabled",
            "notes": "Healthy spare capacity",
        },
    }
    return environments.get(
        target,
        {
            "region": target,
            "cloud_provider": "Unknown",
            "compute_quota_status": "OK",
            "db_quota_status": "OK",
            "notes": "Generic environment",
        },
    )


# ---------------------------------------------------------------------------
# Tool 2: provision_compute
# ---------------------------------------------------------------------------

def provision_compute(region: str, instance_type: str) -> dict:
    """
    Provisions a compute instance in the given region.
    Always succeeds (quota check already done in inspect_environment).
    """
    instance_id = f"i-{hash((region, instance_type)) & 0xFFFFFFFF:08x}"
    return {
        "status": "success",
        "instance_id": instance_id,
        "region": region,
        "instance_type": instance_type,
        "public_ip": "13.233.45.67",
        "private_ip": "10.0.1.42",
        "launch_time": "2026-11-01T18:00:00Z",
        "message": f"Instance {instance_id} launched successfully in {region}.",
    }


# ---------------------------------------------------------------------------
# Tool 3: deploy_database
# ---------------------------------------------------------------------------

def deploy_database(region: str, db_type: str, serverless: bool = False) -> dict:
    """
    Deploys a managed database cluster.

    FIRST CALL:  Always raises ToolError (ERR_DB_QUOTA_EXCEEDED) for
                 the primary region ap-south-1 — simulating a hard quota breach.
    SECOND CALL: Succeeds when alternate region ap-south-2 or serverless=True
                 is specified.
    """
    global _db_call_count
    _db_call_count += 1

    if _db_call_count == 1:
        raise ToolError(
            "ERR_DB_QUOTA_EXCEEDED: Primary region ap-south-1 quota limit reached "
            "for db.r5.xlarge. No additional DB instances can be launched in this region."
        )

    # Subsequent calls succeed
    endpoint = f"db-cluster-{region}.internal.aws.com:5432"
    return {
        "status": "success",
        "db_endpoint": endpoint,
        "region": region,
        "db_type": db_type,
        "serverless": serverless,
        "engine": "PostgreSQL 15.3",
        "multi_az": True,
        "created_at": "2026-11-01T18:05:00Z",
        "message": f"Database cluster deployed in fallback region {region}.",
    }


# ---------------------------------------------------------------------------
# Tool 4: run_health_checks
# ---------------------------------------------------------------------------

def run_health_checks(instance_id: str, db_endpoint: str) -> dict:
    """
    Runs a suite of health checks against the provisioned compute and database.
    Always returns HEALTHY in this simulation.
    """
    return {
        "overall_status": "HEALTHY",
        "checks": {
            "compute_reachability": {"status": "PASS", "latency_ms": 12},
            "db_connectivity": {"status": "PASS", "latency_ms": 8},
            "db_read_write": {"status": "PASS", "ops_per_sec": 1500},
            "ssl_certificate": {"status": "PASS", "expiry_days": 364},
            "cpu_utilization": {"status": "PASS", "value_pct": 3.2},
            "memory_utilization": {"status": "PASS", "value_pct": 18.7},
        },
        "checked_at": "2026-11-01T18:10:00Z",
        "instance_id": instance_id,
        "db_endpoint": db_endpoint,
    }


# ---------------------------------------------------------------------------
# Tool 5: validate_deployment
# ---------------------------------------------------------------------------

def validate_deployment(instance_id: str, db_endpoint: str) -> dict:
    """
    Final sign-off validation.  Confirms the full deployment is production-ready.
    """
    return {
        "status": "VALIDATED",
        "instance_id": instance_id,
        "db_endpoint": db_endpoint,
        "compliance_check": "PASS",
        "security_scan": "PASS",
        "performance_baseline": "PASS",
        "cost_estimate_usd_month": 312.50,
        "deployment_id": f"deploy-{hash(instance_id) & 0xFFFF:04x}",
        "signed_off_at": "2026-11-01T18:15:00Z",
        "message": "Deployment validated and approved for production traffic.",
    }
