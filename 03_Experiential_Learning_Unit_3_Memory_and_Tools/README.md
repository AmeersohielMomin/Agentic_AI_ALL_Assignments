# Experiment 03 — Memory and Tools: Activity Report

## Overview

This experiment explores how **short-term memory**, **vector-store retrieval**, and **sandboxed code execution** transform a stateless baseline agent into a context-aware, multi-hop reasoning system.

---

## Memory Architecture

### Short-Term Buffer (`memory/short_term_buffer.py`)

| Property | Value |
|---|---|
| Implementation | Sliding-window `list[dict]` |
| Capacity | 10 entries (MAX_SIZE) |
| Eviction policy | FIFO — oldest entry dropped on overflow |
| Entry schema | `{role, content, timestamp}` |

The buffer serves two roles:
1. **In-context injection** via `get_scratchpad()` — lets the agent "re-read" recent dialogue.
2. **Seeding the vector store** — each buffered entry is also indexed so it can be retrieved by semantic similarity later.

### Vector Store (`memory/vector_store.py`)

A pure-Python implementation using **TF bag-of-words + cosine similarity** — no NumPy or external libraries required.

```
_vectorize(text) → {term: frequency, ...}
_cosine_similarity(v1, v2) → float ∈ [0, 1]
```

Pre-loaded with **10 business knowledge-base articles** covering:
- Hotel / meal / flight expense limits
- Domestic vs international travel budgets
- Meeting room booking rules
- Expense reimbursement timelines
- Corporate credit card policy

---

## Tool Integration

### KnowledgeSearchTool (`tools/search_tool.py`)

Wraps the VectorStore and returns:
```python
{
  "results": [{"id", "content", "score"}, ...],
  "sources": ["KB001", ...],
  "confidence": 0.72
}
```

### SafeCodeExecTool (`tools/code_exec_tool.py`)

Uses `eval()` with a **stripped `__builtins__`** namespace containing only safe math functions. Before evaluation, a regex scan blocks:
- `import`, `__import__`, `exec`, `open`, `os`, `sys`, `subprocess`, `socket`, and all dunder attributes.

---

## Agent Designs

### MemorylessAgent
- Stateless; always returns a generic "I don't have context" response.
- Establishes the **baseline** for multi-hop question performance.

### MemoryAgent
Multi-step reasoning pipeline per question:
```
1. remember(question) → ShortTermBuffer + VectorStore
2. search_tool.search(question) → top-3 KB articles
3. code_tool.execute(derived_expr) → numeric result (if applicable)
4. synthesise(kb_snippets, computation, sources) → cited answer
5. remember(answer) → persisted for future recall
```

---

## Evaluation Methodology

5 multi-hop questions tested, each requiring at least one of:
- **Policy retrieval** (e.g., hotel rate per night)
- **Multi-step arithmetic** (e.g., 3-night total = hotel × 3 + meals × 3)
- **Conditional reasoning** (e.g., "is Rs 16,500 within the Rs 25,000 budget?")

Correctness is assessed with a simple expected-keyword check; it is a lightweight demonstration metric, not a semantic or factuality evaluation.

---

## Performance Comparison

| Agent | Score (/ 5) | Notes |
|---|---|---|
| MemorylessAgent | 0 / 5 | Cannot answer any policy or math question |
| MemoryAgent | 5 / 5 | Retrieves policy context, computes multi-step totals, and cites answers |

---

## Key Findings

1. **Memory is multiplicative** — even a simple sliding-window buffer plus a vector store turns a useless baseline into a capable assistant.
2. **Grounded policy retrieval** — policy rates are retrieved from cited KB entries, while derived totals are computed with the arithmetic tool.
3. **Sandboxed computation is essential** — arithmetic questions (Q2, Q3, Q5) require real calculation, not pattern matching.
4. **Memory persistence enables multi-hop** — answers added to the vector store can be retrieved to answer follow-up questions.

---

## File Structure

```
03_Experiential_Learning_Unit_3_Memory_and_Tools/
├── memory/
│   ├── short_term_buffer.py   # Sliding-window buffer
│   └── vector_store.py        # TF-IDF cosine vector store (pure Python)
├── tools/
│   ├── search_tool.py         # KnowledgeSearchTool
│   └── code_exec_tool.py      # SafeCodeExecTool (restricted eval)
├── agent.py                   # MemorylessAgent + MemoryAgent
├── benchmark_evaluation.py    # 5-question benchmark + comparison table
├── results/
│   └── benchmark_results.txt  # Saved evaluation output
└── README.md                  # This document
```
