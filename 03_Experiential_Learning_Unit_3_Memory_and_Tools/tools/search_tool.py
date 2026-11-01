"""
Knowledge Search Tool
=====================
Wraps the VectorStore and exposes a simple search interface that returns
top results with a confidence score.
"""

import sys
import os

# Allow running this file directly from any working directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.vector_store import create_knowledge_store


class KnowledgeSearchTool:
    """Searches the pre-loaded business knowledge base."""

    def __init__(self) -> None:
        self._store = create_knowledge_store()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 3) -> dict:
        """
        Search for documents relevant to *query*.

        Returns
        -------
        dict with keys:
            results    – list of {id, content, score} dicts
            sources    – list of document IDs returned
            confidence – average similarity score of top results (0-1)
        """
        raw = self._store.search(query, top_k=top_k)
        results = [
            {"id": r["id"], "content": r["content"], "score": round(r["score"], 4)}
            for r in raw
        ]
        # Additional candidates may be requested for multi-hop reasoning;
        # confidence and default citations describe only the top three hits.
        sources = [r["id"] for r in results[:3]]
        confidence = (
            round(sum(r["score"] for r in results[:3]) / min(len(results), 3), 4)
            if results
            else 0.0
        )
        return {"results": results, "sources": sources, "confidence": confidence}

    def __repr__(self) -> str:
        return f"KnowledgeSearchTool(docs_indexed={len(self._store)})"


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tool = KnowledgeSearchTool()
    print(tool)
    result = tool.search("maximum hotel rate per night domestic")
    print("\nSearch results:")
    for r in result["results"]:
        print(f"  [{r['id']}] score={r['score']}  {r['content'][:90]}...")
    print(f"Sources: {result['sources']}")
    print(f"Confidence: {result['confidence']}")
