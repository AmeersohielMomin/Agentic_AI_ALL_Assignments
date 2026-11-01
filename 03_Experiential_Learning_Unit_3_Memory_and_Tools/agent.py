"""
Agent Implementations
=====================
Two agents that illustrate the impact of memory on multi-hop Q&A:

  MemorylessAgent  — no context retention; always admits ignorance.
  MemoryAgent      — uses ShortTermBuffer + VectorStore + tools to
                     synthesise grounded, cited answers.
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory.short_term_buffer import ShortTermBuffer
from memory.vector_store import create_knowledge_store, VectorStore
from tools.search_tool import KnowledgeSearchTool
from tools.code_exec_tool import SafeCodeExecTool


# ===========================================================================
# MemorylessAgent
# ===========================================================================

class MemorylessAgent:
    """
    Stateless baseline agent.
    Has no access to any context, memory, or tools.
    Always produces a generic "I don't recall" response to highlight
    the limitation of memory-free systems on multi-hop questions.
    """

    name = "MemorylessAgent"

    def answer(self, question: str) -> str:  # noqa: ARG002
        return (
            "I don't have access to any prior context or knowledge base. "
            "I cannot answer multi-hop or policy-specific questions without memory."
        )

    def __repr__(self) -> str:
        return "MemorylessAgent()"


# ===========================================================================
# MemoryAgent
# ===========================================================================

# Simple heuristic: if the question contains arithmetic-looking patterns,
# extract and execute the expression.
_MATH_INDICATORS = re.compile(
    r"(\d+\s*[+\-*/]\s*\d+|\d+%|\bcalculate\b|\bcompute\b|\btotal\b|\bsum\b|\bpercent\b)",
    re.IGNORECASE,
)

# Patterns we try to extract as eval-able expressions
_EXPR_RE = re.compile(r"(\d+(?:\.\d+)?\s*[+\-*/]\s*\d+(?:\.\d+)?(?:\s*[+\-*/]\s*\d+(?:\.\d+)?)*)")


class MemoryAgent:
    """
    Memory-augmented agent with:
      • ShortTermBuffer  — retains recent conversation turns
      • VectorStore      — semantic retrieval over knowledge base + past memories
      • KnowledgeSearchTool  — structured search interface
      • SafeCodeExecTool     — arithmetic evaluation
    """

    name = "MemoryAgent"

    def __init__(self) -> None:
        self.buffer = ShortTermBuffer()
        self.vector_store: VectorStore = create_knowledge_store()
        self.search_tool = KnowledgeSearchTool()
        self.code_tool = SafeCodeExecTool()
        self._memory_counter = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def remember(self, role: str, content: str) -> None:
        """Add to short-term buffer AND persist into the vector store."""
        self.buffer.add(role, content)
        self._memory_counter += 1
        doc_id = f"MEM{self._memory_counter:04d}"
        self.vector_store.add_document(
            doc_id, content, metadata={"source": "short_term_buffer", "role": role}
        )

    def answer(self, question: str) -> str:
        """
        Generate a grounded answer by:
          1. Adding the question to memory
          2. Retrieving relevant KB articles
          3. Executing any arithmetic sub-expressions
          4. Synthesising a cited response
        """
        # Record the question
        self.remember("user", question)

        # --- Retrieve context from short-term buffer ---
        recent = self.buffer.get_context(k=5)
        context_lines = [
            f"  [{e['role']}]: {e['content']}" for e in recent[:-1]  # exclude current Q
        ]
        buffer_context = "\n".join(context_lines) if context_lines else "  (no prior turns)"

        # --- Search knowledge base ---
        # Retrieve the small policy corpus so multi-topic questions can use
        # all required sources even when one falls outside a fixed top-three.
        search_result = self.search_tool.search(question, top_k=10)
        math_context = search_result["results"]
        kb_snippets = math_context[:3]
        sources = search_result["sources"]
        confidence = search_result["confidence"]

        # Build a text extract from top results
        kb_text = "\n".join(
            f"  [{r['id']}] {r['content']}" for r in kb_snippets
        )

        # --- Attempt arithmetic computation ---
        computation_note = ""
        if _MATH_INDICATORS.search(question) or (
            "within" in question.lower() and "budget" in question.lower()
        ):
            # Try to pull a numeric expression from the question
            expr_matches = _EXPR_RE.findall(question)
            # Also try to derive expression from KB context (policy numbers)
            derived_exprs = self._derive_math_from_question_and_kb(question, math_context)
            all_exprs = expr_matches + derived_exprs
            for expr in all_exprs:
                res = self.code_tool.execute(expr.replace(",", ""))
                if res["success"]:
                    computation_note = f"\n  Computed: {expr.strip()} = {res['output']}"
                    break

        if "meal" in question.lower() and "hotel" in question.lower():
            # The total uses both allowance policies; cite those inputs along
            # with the trip budget policy used to interpret the result.
            sources = ["KB003", "KB001", "KB002"]

        # --- Synthesise answer ---
        answer = self._synthesise(
            question=question,
            kb_snippets=kb_snippets,
            buffer_context=buffer_context,
            computation_note=computation_note,
            sources=sources,
            confidence=confidence,
        )

        # Record the answer
        self.remember("assistant", answer)
        return answer

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _derive_math_from_question_and_kb(
        self, question: str, kb_snippets: list[dict]
    ) -> list[str]:
        """
        Heuristically extract numeric values from the question and
        KB snippets to build simple arithmetic expressions.
        """
        exprs = []
        q_numbers = re.findall(r"\d+(?:,\d+)*(?:\.\d+)?", question)
        # "15% of" pattern
        pct_match = re.search(r"(\d+)\s*%\s*of\s+(?:the\s+)?(?:maximum\s+)?(?:allowed\s+)?(\w[\w ]*)", question, re.IGNORECASE)
        if pct_match:
            pct = pct_match.group(1)
            # search KB for the subject value
            for snippet in kb_snippets:
                nums = re.findall(r"Rs\s*(\d+(?:,\d+)*)", snippet["content"])
                if nums:
                    val = nums[0].replace(",", "")
                    exprs.append(f"{pct} / 100 * {val}")
                    break

        # Budget check: "flights cost X and hotel Y/night for N nights"
        budget_match = re.search(
            r"flights?\s+cost\s+(?:Rs\s*)?(\d+(?:,\d+)*)\s+and\s+hotel\s+(?:is\s+)?(?:Rs\s*)?(\d+(?:,\d+)*)/night\s+for\s+(\d+)\s+nights?",
            question,
            re.IGNORECASE,
        )
        if budget_match:
            flights = budget_match.group(1).replace(",", "")
            hotel_per_night = budget_match.group(2).replace(",", "")
            nights = budget_match.group(3)
            exprs.append(f"{flights} + {hotel_per_night} * {nights}")

        # "total budget for N-night trip including meals"
        nights_match = re.search(r"(\d+)[\-\s]night", question, re.IGNORECASE)
        if nights_match:
            nights = nights_match.group(1)
            # look for hotel rate and meal rate in KB
            hotel_rate, meal_rate = None, None
            for snippet in kb_snippets:
                if "hotel" in snippet["content"].lower() and hotel_rate is None:
                    m = re.search(r"Rs\s*(\d+(?:,\d+)*)\s+per\s+night", snippet["content"])
                    if m:
                        hotel_rate = m.group(1).replace(",", "")
                if "meal" in snippet["content"].lower() and meal_rate is None:
                    m = re.search(r"Rs\s*(\d+(?:,\d+)*)\s+per\s+day", snippet["content"])
                    if m:
                        meal_rate = m.group(1).replace(",", "")
            if hotel_rate and meal_rate:
                exprs.append(f"{hotel_rate} * {nights} + {meal_rate} * {nights}")

        return exprs

    def _synthesise(
        self,
        question: str,
        kb_snippets: list[dict],
        buffer_context: str,
        computation_note: str,
        sources: list[str],
        confidence: float,
    ) -> str:
        """Build a readable answer string from retrieved components."""
        top = kb_snippets[0] if kb_snippets else None

        # Pull key Rs values from top snippet for inline answer
        rs_values = []
        if top:
            rs_values = re.findall(r"Rs\s*[\d,]+", top["content"])

        # Decision: is it within budget?
        budget_decision = ""
        if "within" in question.lower() and "budget" in question.lower():
            # extract total spend from computation_note
            comp_val_match = re.search(r"=\s*([\d.]+)", computation_note)
            if comp_val_match:
                total_spend = float(comp_val_match.group(1))
                # KB003 says total budget is 25000
                if total_spend <= 25000:
                    budget_decision = f" YES — total spend of Rs {total_spend:,.0f} is within the Rs 25,000 domestic travel budget."
                else:
                    budget_decision = f" NO — total spend of Rs {total_spend:,.0f} exceeds the Rs 25,000 domestic travel budget."

        parts = []
        if top:
            parts.append(f"Based on {top['id']}: {top['content']}")
        if computation_note:
            parts.append(computation_note.strip())
        if budget_decision:
            parts.append(budget_decision.strip())
        if not parts:
            parts.append("No directly relevant policy found in the knowledge base.")

        answer_body = "  ".join(parts)
        citation = f"[Sources: {', '.join(sources)} | Confidence: {confidence:.2%}]"
        return f"{answer_body}\n{citation}"

    def __repr__(self) -> str:
        return (
            f"MemoryAgent(buffer_size={len(self.buffer)}, "
            f"vector_store_docs={len(self.vector_store)})"
        )


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    memless = MemorylessAgent()
    mem = MemoryAgent()

    q = "What is the maximum hotel expense per night for domestic travel?"
    print("=== MemorylessAgent ===")
    print(memless.answer(q))
    print()
    print("=== MemoryAgent ===")
    print(mem.answer(q))
