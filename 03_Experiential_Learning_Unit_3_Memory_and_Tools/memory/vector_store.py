"""
Vector Store (pure Python, no external libraries)
==================================================
Uses a simple TF bag-of-words representation with cosine similarity for
nearest-neighbour retrieval.  Pre-loaded with 10 business knowledge-base
articles covering travel policies, expense limits, and meeting protocols.
"""

import math
import re
import uuid


# ---------------------------------------------------------------------------
# Stop-words to ignore during vectorisation
# ---------------------------------------------------------------------------
_STOP_WORDS = {
    "a", "an", "the", "is", "it", "in", "on", "of", "to", "and", "or",
    "for", "with", "at", "by", "from", "as", "are", "be", "was", "were",
    "this", "that", "these", "those", "can", "will", "may", "all",
}

_KNOWLEDGE_BASE = [
    {
        "id": "KB001",
        "content": (
            "Domestic Travel Policy: Employees are allowed a maximum hotel expense of "
            "Rs 5000 per night for domestic travel. All hotel bookings must be pre-approved "
            "by the direct manager at least 48 hours before travel."
        ),
        "metadata": {"category": "travel", "policy": "hotel"},
    },
    {
        "id": "KB002",
        "content": (
            "Meal Allowance Policy: The maximum allowed meal expense is Rs 1500 per day "
            "for domestic travel. This covers breakfast, lunch, and dinner combined. "
            "Original receipts must be submitted within 7 days of returning."
        ),
        "metadata": {"category": "travel", "policy": "meals"},
    },
    {
        "id": "KB003",
        "content": (
            "Domestic Travel Budget: Total approved travel budget for a standard domestic "
            "trip is Rs 25000. This covers flights, hotel, meals, and local transport. "
            "Any overrun requires VP Finance approval before travel."
        ),
        "metadata": {"category": "travel", "policy": "budget"},
    },
    {
        "id": "KB004",
        "content": (
            "Flight Booking Policy: Economy class is mandatory for all domestic flights. "
            "Business class is only permitted for international flights exceeding 6 hours. "
            "Tickets must be booked through the corporate travel portal to receive GST invoices."
        ),
        "metadata": {"category": "travel", "policy": "flights"},
    },
    {
        "id": "KB005",
        "content": (
            "Meeting Room Booking Policy: For groups of 10 or fewer participants, any "
            "available conference room can be booked via the room-booking portal. "
            "For groups larger than 10 people, the large boardroom (Room 301) must be used "
            "and the booking requires approval from Office Administration at least 24 hours in advance."
        ),
        "metadata": {"category": "meetings", "policy": "rooms"},
    },
    {
        "id": "KB006",
        "content": (
            "Expense Reimbursement Timeline: All travel expense claims must be submitted "
            "within 30 days of trip completion. Claims submitted after 30 days will not be "
            "reimbursed without a written exception approved by the CFO."
        ),
        "metadata": {"category": "finance", "policy": "reimbursement"},
    },
    {
        "id": "KB007",
        "content": (
            "International Travel Policy: International travel requires VP-level approval "
            "at least 2 weeks in advance. Hotel limit is Rs 12000 per night. "
            "Daily meal allowance is Rs 3000 for international destinations."
        ),
        "metadata": {"category": "travel", "policy": "international"},
    },
    {
        "id": "KB008",
        "content": (
            "Local Transport Policy: Taxi and cab expenses up to Rs 500 per day are "
            "reimbursable during domestic travel. For travel within the city, employees "
            "should prefer company-empanelled cab vendors for safety and billing purposes."
        ),
        "metadata": {"category": "travel", "policy": "transport"},
    },
    {
        "id": "KB009",
        "content": (
            "Video Conference Policy: All meetings with external clients or vendors should "
            "first be attempted via video conference before booking in-person travel. "
            "Travel approved only if VC is not feasible and documented in the travel request."
        ),
        "metadata": {"category": "meetings", "policy": "vc"},
    },
    {
        "id": "KB010",
        "content": (
            "Corporate Credit Card Policy: Employees with Grade 3 and above may apply for "
            "a corporate credit card with a monthly limit of Rs 50000. "
            "All corporate card expenses must be reconciled within 15 days of month-end."
        ),
        "metadata": {"category": "finance", "policy": "credit_card"},
    },
]


class VectorStore:
    """
    In-memory vector store backed by TF bag-of-words + cosine similarity.
    No external dependencies required.
    """

    def __init__(self) -> None:
        self.documents: list[dict] = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Lower-case, strip punctuation, remove stop-words."""
        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return [t for t in tokens if t not in _STOP_WORDS]

    def _vectorize(self, text: str) -> dict:
        """Return term-frequency dict for *text*."""
        tokens = self._tokenize(text)
        tf: dict[str, float] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0.0) + 1.0
        # Normalise by document length so short and long docs are comparable
        total = sum(tf.values()) or 1.0
        return {k: v / total for k, v in tf.items()}

    @staticmethod
    def _cosine_similarity(v1: dict, v2: dict) -> float:
        """Compute cosine similarity between two TF dicts."""
        # Dot product over shared terms
        dot = sum(v1[k] * v2.get(k, 0.0) for k in v1)
        mag1 = math.sqrt(sum(x * x for x in v1.values()))
        mag2 = math.sqrt(sum(x * x for x in v2.values()))
        if mag1 == 0.0 or mag2 == 0.0:
            return 0.0
        return dot / (mag1 * mag2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_document(self, doc_id: str, content: str, metadata: dict = None) -> None:
        """Vectorise *content* and store the document."""
        if metadata is None:
            metadata = {}
        self.documents.append(
            {
                "id": doc_id,
                "content": content,
                "metadata": metadata,
                "vector": self._vectorize(content),
            }
        )

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """Return top-k documents ranked by cosine similarity to *query*."""
        q_vec = self._vectorize(query)
        scored = [
            {
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"],
                "score": self._cosine_similarity(q_vec, doc["vector"]),
            }
            for doc in self.documents
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def __len__(self) -> int:
        return len(self.documents)

    def __repr__(self) -> str:
        return f"VectorStore(docs={len(self)})"


# ---------------------------------------------------------------------------
# Factory: returns a VectorStore pre-loaded with the knowledge base
# ---------------------------------------------------------------------------

def create_knowledge_store() -> VectorStore:
    """Return a VectorStore pre-loaded with _KNOWLEDGE_BASE entries."""
    vs = VectorStore()
    for entry in _KNOWLEDGE_BASE:
        vs.add_document(entry["id"], entry["content"], entry["metadata"])
    return vs


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    store = create_knowledge_store()
    print(f"Store contains {len(store)} documents.\n")
    results = store.search("hotel expense domestic travel night", top_k=3)
    for r in results:
        print(f"[{r['id']}] score={r['score']:.4f}  {r['content'][:80]}...")
