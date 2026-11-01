"""
Benchmark Evaluation
====================
Tests MemorylessAgent vs MemoryAgent on 5 multi-hop questions that require
memory and/or computation. Prints a Markdown comparison table and saves
results to results/benchmark_results.txt.
"""

import os
import sys
from datetime import datetime, timezone

# Make sure local modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import MemorylessAgent, MemoryAgent


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

QUESTIONS = [
    {
        "id": "Q1",
        "question": "What is the maximum hotel expense per night for domestic travel?",
        "expected_keyword": "5000",
    },
    {
        "id": "Q2",
        "question": (
            "Based on the travel policy, what is the total budget for a 3-night "
            "trip including meals?"
        ),
        "expected_keyword": "19500",   # 5000*3 + 1500*3 = 19500
    },
    {
        "id": "Q3",
        "question": "What is 15% of the maximum allowed meal expense?",
        "expected_keyword": "225",     # 0.15 * 1500 = 225
    },
    {
        "id": "Q4",
        "question": (
            "What meeting room booking policy applies for groups larger than 10 people?"
        ),
        "expected_keyword": "301",     # Room 301 / boardroom
    },
    {
        "id": "Q5",
        "question": (
            "If flights cost Rs 8500 and hotel is Rs 4000/night for 2 nights, "
            "is this within the travel budget?"
        ),
        "expected_keyword": "YES",     # 8500 + 8000 = 16500 < 25000
    },
]


def _check_correct(answer: str, keyword: str) -> bool:
    """Heuristic correctness check: does the answer contain the expected keyword?"""
    return keyword.lower() in answer.lower()


def _truncate(text: str, max_len: int = 80) -> str:
    return text if len(text) <= max_len else text[:max_len - 3] + "..."


def run_benchmark() -> list[dict]:
    """Run all questions through both agents and return result records."""
    memless_agent = MemorylessAgent()
    mem_agent = MemoryAgent()

    records = []

    print("=" * 90)
    print("  BENCHMARK: MemorylessAgent vs MemoryAgent — Memory & Tools Evaluation")
    print("=" * 90)
    print()

    for item in QUESTIONS:
        qid = item["id"]
        question = item["question"]
        expected = item["expected_keyword"]

        print(f"[{qid}] {question}")
        print("-" * 80)

        ml_answer = memless_agent.answer(question)
        m_answer = mem_agent.answer(question)

        ml_correct = _check_correct(ml_answer, expected)
        m_correct = _check_correct(m_answer, expected)

        print(f"  Memoryless : {_truncate(ml_answer)}")
        print(f"  Memory     : {_truncate(m_answer)}")
        print(f"  Correct?   : Memoryless={'YES' if ml_correct else 'NO'}  "
              f"Memory={'YES' if m_correct else 'NO'}")
        print()

        records.append(
            {
                "id": qid,
                "question": question,
                "memoryless_answer": ml_answer,
                "memory_answer": m_answer,
                "memoryless_correct": ml_correct,
                "memory_correct": m_correct,
                "expected_keyword": expected,
            }
        )

    return records


def print_comparison_table(records: list[dict]) -> str:
    """Print a Markdown comparison table and return it as a string."""
    header = (
        "| # | Question | Memoryless Result | Memory Agent Result | Correct? |\n"
        "|---|----------|-------------------|---------------------|----------|\n"
    )
    rows = []
    for r in records:
        ml_snip = _truncate(r["memoryless_answer"], 60)
        m_snip = _truncate(r["memory_answer"], 60)
        correct_cell = (
            f"ML={'✓' if r['memoryless_correct'] else '✗'} / "
            f"MA={'✓' if r['memory_correct'] else '✗'}"
        )
        rows.append(
            f"| {r['id']} | {r['question'][:50]}... | {ml_snip} | {m_snip} | {correct_cell} |"
        )

    table = header + "\n".join(rows)
    print("\n" + "=" * 90)
    print("  COMPARISON TABLE")
    print("=" * 90)
    print(table)

    # Summary
    ml_total = sum(1 for r in records if r["memoryless_correct"])
    m_total = sum(1 for r in records if r["memory_correct"])
    print(f"\n  MemorylessAgent correct: {ml_total}/{len(records)}")
    print(f"  MemoryAgent    correct: {m_total}/{len(records)}")
    print()
    return table


def save_results(records: list[dict], table: str) -> None:
    """Persist benchmark results to results/benchmark_results.txt."""
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, "benchmark_results.txt")

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    lines = [
        "BENCHMARK RESULTS — Memory and Tools Experiment",
        f"Generated: {timestamp}",
        "=" * 80,
        "",
        table,
        "",
        "=" * 80,
        "FULL ANSWERS",
        "=" * 80,
    ]
    for r in records:
        lines += [
            f"\n[{r['id']}] {r['question']}",
            f"  Expected keyword : {r['expected_keyword']}",
            f"  Memoryless answer: {r['memoryless_answer']}",
            f"  Memory answer    : {r['memory_answer']}",
            f"  Memoryless correct: {'YES' if r['memoryless_correct'] else 'NO'}",
            f"  Memory correct    : {'YES' if r['memory_correct'] else 'NO'}",
        ]

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    print(f"  Results saved to: {out_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    records = run_benchmark()
    table = print_comparison_table(records)
    save_results(records, table)
    if not all(record["memory_correct"] for record in records):
        raise SystemExit("MemoryAgent benchmark failed: one or more expected answers were missing.")
