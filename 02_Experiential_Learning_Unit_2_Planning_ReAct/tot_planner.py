"""
tot_planner.py — Tree-of-Thought (ToT) Travel Itinerary Planner.

Approach: Build a tree of alternative options, score each node, prune low-value
branches, and backtrack on failure to find the next-best option.
"""

import os
import json
from typing import Optional


class TreeOfThoughtPlanner:
    """
    Tree-of-Thought planner for a 3-day business trip to Mumbai.

    ToT strength : Explores multiple options simultaneously; backtracks gracefully.
    ToT weakness : More complex to implement; can over-explore when tree is wide.
    """

    goal = "Plan 3-day business trip to Mumbai within budget Rs 25,000 with client meetings"

    # Weights for heuristic score (must sum to 1.0)
    WEIGHTS = {"cost": 0.50, "comfort": 0.30, "risk": 0.20}

    # ------------------------------------------------------------------
    # Tree construction
    # ------------------------------------------------------------------

    def build_tree(self) -> dict:
        """
        Build a planning tree with 3 root branches (accommodation strategy),
        each containing 3 child options (specific hotels / listings).

        Each leaf node has:
          cost_score    : 0–10 (10 = cheapest / best value)
          comfort_score : 0–10 (10 = most comfortable)
          risk_score    : 0–10 (10 = lowest risk of cancellation / issues)
          sold_out      : bool (set True to test backtracking)
        """
        return {
            "goal": self.goal,
            "branches": [
                {
                    "id": "A",
                    "name": "Business Hotels (near BKC)",
                    "options": [
                        {
                            "id": "A1",
                            "name": "Hotel Trident BKC",
                            "cost_score": 7.0,
                            "comfort_score": 9.0,
                            "risk_score": 8.0,
                            "price_per_night_rs": 4000,
                            "sold_out": False,  # will be set True on inject_failure
                        },
                        {
                            "id": "A2",
                            "name": "ITC Grand Central",
                            "cost_score": 5.5,
                            "comfort_score": 9.5,
                            "risk_score": 7.5,
                            "price_per_night_rs": 5500,
                            "sold_out": False,
                        },
                        {
                            "id": "A3",
                            "name": "The St. Regis Mumbai",
                            "cost_score": 3.0,
                            "comfort_score": 10.0,
                            "risk_score": 6.0,
                            "price_per_night_rs": 9000,
                            "sold_out": False,
                        },
                    ],
                },
                {
                    "id": "B",
                    "name": "Budget Hotels (Andheri / Powai)",
                    "options": [
                        {
                            "id": "B1",
                            "name": "Ibis Mumbai Airport",
                            "cost_score": 9.0,
                            "comfort_score": 7.0,
                            "risk_score": 9.0,
                            "price_per_night_rs": 2800,
                            "sold_out": False,
                        },
                        {
                            "id": "B2",
                            "name": "Treebo Trend Neelkanth",
                            "cost_score": 9.5,
                            "comfort_score": 6.5,
                            "risk_score": 8.5,
                            "price_per_night_rs": 2400,
                            "sold_out": False,
                        },
                        {
                            "id": "B3",
                            "name": "FabHotel Prime Comfort",
                            "cost_score": 10.0,
                            "comfort_score": 5.5,
                            "risk_score": 7.0,
                            "price_per_night_rs": 1900,
                            "sold_out": False,
                        },
                    ],
                },
                {
                    "id": "C",
                    "name": "Airbnb / Serviced Apartments",
                    "options": [
                        {
                            "id": "C1",
                            "name": "Luxury Apartment Worli Sea View",
                            "cost_score": 8.5,
                            "comfort_score": 8.5,
                            "risk_score": 6.0,
                            "price_per_night_rs": 3200,
                            "sold_out": False,
                        },
                        {
                            "id": "C2",
                            "name": "Cozy Studio BKC",
                            "cost_score": 9.0,
                            "comfort_score": 7.5,
                            "risk_score": 6.5,
                            "price_per_night_rs": 2700,
                            "sold_out": False,
                        },
                        {
                            "id": "C3",
                            "name": "Modern 1BHK Lower Parel",
                            "cost_score": 8.0,
                            "comfort_score": 8.0,
                            "risk_score": 7.0,
                            "price_per_night_rs": 3000,
                            "sold_out": False,
                        },
                    ],
                },
            ],
        }

    # ------------------------------------------------------------------
    # Heuristic evaluation
    # ------------------------------------------------------------------

    def evaluate_node(self, node: dict) -> float:
        """
        Compute a weighted heuristic score in [0, 10] for a leaf node.
        Higher is better.
        """
        score = (
            self.WEIGHTS["cost"] * node["cost_score"]
            + self.WEIGHTS["comfort"] * node["comfort_score"]
            + self.WEIGHTS["risk"] * node["risk_score"]
        )
        return round(score, 3)

    # ------------------------------------------------------------------
    # Best-first search with backtracking
    # ------------------------------------------------------------------

    def search(self, inject_failure: bool = False) -> dict:
        """
        Perform best-first search over the tree:
        1. Score every leaf node.
        2. Sort globally by score (descending).
        3. If inject_failure=True, mark the top-scoring option as sold_out.
        4. Iterate through sorted candidates; skip sold_out; return first available.

        Returns a result dict with the chosen path and all explored nodes.
        """
        tree = self.build_tree()

        print("=" * 70)
        print("  Tree-of-Thought Planner — Mumbai Business Trip")
        print(f"  Goal : {self.goal}")
        print("=" * 70)
        print("\n  🌳 Building and evaluating option tree...\n")

        all_nodes: list[dict] = []
        for branch in tree["branches"]:
            print(f"  Branch {branch['id']}: {branch['name']}")
            for opt in branch["options"]:
                score = self.evaluate_node(opt)
                opt["heuristic_score"] = score
                opt["branch_name"] = branch["name"]
                all_nodes.append(opt)
                print(
                    f"    [{opt['id']}] {opt['name']:35s}  score={score:.3f}"
                    f"  Rs {opt['price_per_night_rs']:,}/night"
                )

        # Inject failure: mark the globally best option as sold_out
        all_nodes_sorted = sorted(all_nodes, key=lambda n: n["heuristic_score"], reverse=True)
        if inject_failure:
            top = all_nodes_sorted[0]
            top["sold_out"] = True
            print(f"\n  ⚠  inject_failure=True → '{top['name']}' marked as SOLD OUT")

        print(f"\n  🔍 Best-first search (pruning sold_out nodes)...\n")

        chosen = None
        backtrack_count = 0
        explored: list[dict] = []

        for node in all_nodes_sorted:
            icon = "✅" if not node["sold_out"] else "❌"
            status = "selected" if not node["sold_out"] else "sold_out → backtrack"
            print(f"    {icon} [{node['id']}] {node['name']:35s}  score={node['heuristic_score']:.3f}  {status}")
            explored.append({"id": node["id"], "name": node["name"], "score": node["heuristic_score"], "sold_out": node["sold_out"]})

            if node["sold_out"]:
                backtrack_count += 1
                continue

            chosen = node
            break

        print(f"\n  ✅  Best available option: [{chosen['id']}] {chosen['name']}")
        print(f"      Price: Rs {chosen['price_per_night_rs']:,}/night")
        print(f"      Score: {chosen['heuristic_score']:.3f}")
        print(f"      Backtracks: {backtrack_count}\n")

        result = {
            "best_path": {
                "option_id": chosen["id"],
                "name": chosen["name"],
                "branch": chosen["branch_name"],
                "price_per_night_rs": chosen["price_per_night_rs"],
                "heuristic_score": chosen["heuristic_score"],
            },
            "backtrack_count": backtrack_count,
            "nodes_explored": explored,
            "completed_successfully": True,
        }

        # Save trace
        traces_dir = os.path.join(os.path.dirname(__file__), "traces")
        os.makedirs(traces_dir, exist_ok=True)
        with open(os.path.join(traces_dir, "tot_trace.txt"), "w", encoding="utf-8") as f:
            f.write(f"Goal: {self.goal}\n\n")
            f.write("Nodes explored (best-first):\n")
            for n in explored:
                f.write(f"  [{n['id']}] {n['name']} — score={n['score']} sold_out={n['sold_out']}\n")
            f.write(f"\nChosen: {json.dumps(result['best_path'], ensure_ascii=False)}\n")
            f.write(f"Backtracks: {backtrack_count}\n")

        return result


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    planner = TreeOfThoughtPlanner()
    result = planner.search(inject_failure=True)
    print("Final result:", json.dumps(result["best_path"], indent=2))
