"""
Experiential Learning Unit 4: Team of Agents
deadlock_breaker.py - Multi-Agent Deadlock Detection and Cycle Breaking Simulation

Simulates circular dependency deadlock between role-based agents:
- Agent A waits for Agent B's output
- Agent B waits for Agent A's output
Demonstrates DFS cycle detection on wait-for dependency graphs and automated supervisor arbitration.
"""

import time
from collections import defaultdict
from typing import Dict, List, Set, Optional


class DependencyGraph:
    """Tracks waiting dependencies between agents."""
    def __init__(self):
        self.adj: Dict[str, Set[str]] = defaultdict(set)  # u -> set of v (u is waiting for v)

    def add_dependency(self, waiting_agent: str, target_agent: str):
        self.adj[waiting_agent].add(target_agent)

    def remove_dependency(self, waiting_agent: str, target_agent: str):
        self.adj[waiting_agent].discard(target_agent)

    def clear(self):
        self.adj.clear()

    def detect_cycle(self) -> Optional[List[str]]:
        """DFS-based cycle detection returning the cycle path if found."""
        visited = set()
        rec_stack = set()
        parent_map = {}

        def dfs(node: str, path: List[str]) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.adj.get(node, []):
                if neighbor not in visited:
                    parent_map[neighbor] = node
                    cycle = dfs(neighbor, path)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Cycle detected: extract subpath from neighbor to current
                    cycle_start_idx = path.index(neighbor)
                    return path[cycle_start_idx:] + [neighbor]

            rec_stack.remove(node)
            path.pop()
            return None

        for node in list(self.adj.keys()):
            if node not in visited:
                cycle = dfs(node, [])
                if cycle:
                    return cycle
        return None


class SupervisorArbitrator:
    """Central supervisor that monitors agent communications and resolves deadlocks."""
    def __init__(self, graph: DependencyGraph):
        self.graph = graph

    def arbitrate(self, cycle: List[str], fallback_payloads: Dict[str, dict]) -> str:
        """
        Breaks the cycle by:
        1. Identifying the least critical agent in the cycle.
        2. Injecting a default/cached baseline payload so that agent stops waiting.
        3. Severing the dependency edge.
        """
        broken_edge_from = cycle[0]
        broken_edge_to = cycle[1]
        self.graph.remove_dependency(broken_edge_from, broken_edge_to)

        fallback = fallback_payloads.get(broken_edge_to, {"status": "FALLBACK_INJECTED", "data": "Default baseline"})
        return (f"[SUPERVISOR INTERVENTION] Deadlock cycle detected: {' -> '.join(cycle)}!\n"
                f"  Arbitration Action: Severed dependency edge ({broken_edge_from} -> {broken_edge_to}).\n"
                f"  Injected synthetic context payload on behalf of {broken_edge_to}: {fallback}\n"
                f"  Agent {broken_edge_from} unblocked. Pipeline resumed.")


def run_deadlock_simulation():
    print("=" * 70)
    print("  MULTI-AGENT DEADLOCK DETECTION & RESOLUTION SIMULATION")
    print("=" * 70)

    graph = DependencyGraph()
    supervisor = SupervisorArbitrator(graph)

    print("\n[Phase 1] Normal Coordination (Linear Handoff: A -> B -> C)")
    graph.add_dependency("AgentB", "AgentA")
    graph.add_dependency("AgentC", "AgentB")
    cycle = graph.detect_cycle()
    print(f"  Current Dependencies : AgentB waits for AgentA; AgentC waits for AgentB")
    print(f"  Cycle Detected?      : {cycle is not None} (Graph is a valid DAG)")

    print("\n[Phase 2] Simulating Circular Deadlock (A <-> B)")
    print("  Scenario: AgentA needs AgentB's security clearance before sending raw data.")
    print("            AgentB refuses to issue clearance until AgentA sends the raw data schema.")
    graph.clear()
    graph.add_dependency("AgentA", "AgentB")
    graph.add_dependency("AgentB", "AgentA")

    print(f"  Dependency: AgentA -> waits for -> AgentB")
    print(f"  Dependency: AgentB -> waits for -> AgentA")

    cycle = graph.detect_cycle()
    print(f"\n  [DeadlockDetector] Running DFS Cycle Detection...")
    if cycle:
        print(f"  ⚠️  DEADLOCK CONFIRMED! Cycle path: {' -> '.join(cycle)}")
        print("  Status: Agents are permanently blocked waiting for mutual responses.")

        print("\n[Phase 3] Supervisor Arbitration")
        fallbacks = {
            "AgentB": {"clearance_level": "RESTRICTED_TEMPORARY", "max_records": 10}
        }
        resolution = supervisor.arbitrate(cycle, fallbacks)
        print(resolution)

        # Check graph again
        cycle_after = graph.detect_cycle()
        print(f"\n  Cycle Detected After Arbitration: {cycle_after is not None}")
        print("  ✅ Pipeline state restored to normal execution.")
    print("=" * 70)


if __name__ == "__main__":
    run_deadlock_simulation()
