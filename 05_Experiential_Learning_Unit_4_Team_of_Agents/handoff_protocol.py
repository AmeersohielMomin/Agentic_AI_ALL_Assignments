"""
Handoff Protocol — handoff_protocol.py
=======================================
Implements a structured message-passing protocol for multi-agent communication.
Tracks all messages as an immutable audit trail.
"""

import datetime
from dataclasses import dataclass, field


# ===========================================================================
# Message Dataclass
# ===========================================================================

@dataclass
class Message:
    from_agent: str
    to_agent: str
    task: str
    payload: dict
    status: str = "PENDING"         # PENDING | DELIVERED | PROCESSED | ERROR
    timestamp: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z")
    message_id: str = field(default_factory=lambda: f"MSG-{datetime.datetime.utcnow().strftime('%H%M%S%f')[:12]}")


# ===========================================================================
# HandoffProtocol
# ===========================================================================

class HandoffProtocol:
    """
    Manages message passing between agents with a full audit trail.
    All messages are stored chronologically in self._log.
    """

    def __init__(self) -> None:
        self._log: list[Message] = []
        self._inbox: dict[str, list[Message]] = {}  # agent_name → [messages]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, msg: Message) -> bool:
        """
        Log and deliver *msg* to the recipient's inbox.

        Returns True if delivery succeeded.
        """
        try:
            msg.status = "DELIVERED"
            self._log.append(msg)
            self._inbox.setdefault(msg.to_agent, []).append(msg)
            print(
                f"  [PROTOCOL] {msg.from_agent} ──► {msg.to_agent} | "
                f"Task: '{msg.task}' | MsgID: {msg.message_id}"
            )
            return True
        except Exception as exc:  # noqa: BLE001
            msg.status = "ERROR"
            print(f"  [PROTOCOL ERROR] Failed to deliver {msg.message_id}: {exc}")
            return False

    def receive(self, agent_name: str) -> list[Message]:
        """Return and clear all messages waiting for *agent_name*."""
        messages = self._inbox.pop(agent_name, [])
        for msg in messages:
            msg.status = "PROCESSED"
        return messages

    def get_trace(self) -> list[Message]:
        """Return the full chronological audit trail (immutable view)."""
        return list(self._log)

    def print_trace(self) -> None:
        """Pretty-print the full message passing trace."""
        print("\n" + "=" * 70)
        print("  FULL MESSAGE PASSING TRACE")
        print("=" * 70)
        if not self._log:
            print("  (no messages logged)")
            return
        for msg in self._log:
            print(
                f"\n  [{msg.message_id}] @ {msg.timestamp}\n"
                f"    From   : {msg.from_agent}\n"
                f"    To     : {msg.to_agent}\n"
                f"    Task   : {msg.task}\n"
                f"    Status : {msg.status}\n"
                f"    Payload: {list(msg.payload.keys())}"
            )
        print("\n" + "=" * 70)

    def __len__(self) -> int:
        return len(self._log)


# ===========================================================================
# Demo: 3-Agent Research Crew using HandoffProtocol
# ===========================================================================

def run_handoff_demo() -> None:
    protocol = HandoffProtocol()

    print("=" * 70)
    print("  HANDOFF PROTOCOL DEMO — Research Crew Message Passing")
    print("=" * 70)

    # --- COORDINATOR → RESEARCHER ---
    print("\n[Step 1] Coordinator dispatches research task to Researcher")
    m1 = Message(
        from_agent="Coordinator",
        to_agent="ResearcherAgent",
        task="Research the topic: Artificial Intelligence",
        payload={"topic": "Artificial Intelligence", "depth": "medium"},
    )
    protocol.send(m1)

    # ResearcherAgent picks up its message and does work
    received_by_researcher = protocol.receive("ResearcherAgent")
    research_input = received_by_researcher[0].payload
    print(f"  [ResearcherAgent] Received task: '{received_by_researcher[0].task}'")
    research_output = {
        "topic": research_input["topic"],
        "key_facts": [
            "AI enables machines to mimic human intelligence.",
            "Industry AI adoption grew 37% in 2023.",
            "Ethical concerns: bias, transparency, accountability.",
        ],
        "sources": ["TechReview 2024", "McKinsey 2023", "IEEE Ethics 2024"],
    }
    print(f"  [ResearcherAgent] Research complete. {len(research_output['key_facts'])} facts gathered.")

    # --- RESEARCHER → WRITER ---
    print("\n[Step 2] Researcher hands off to Writer")
    m2 = Message(
        from_agent="ResearcherAgent",
        to_agent="WriterAgent",
        task="Draft report from research summary",
        payload={"research_package": research_output},
    )
    protocol.send(m2)

    received_by_writer = protocol.receive("WriterAgent")
    writer_input = received_by_writer[0].payload["research_package"]
    print(f"  [WriterAgent] Received task: '{received_by_writer[0].task}'")
    draft_output = {
        "title": f"Report on {writer_input['topic']}",
        "body": "\n".join(f"- {fact}" for fact in writer_input["key_facts"]),
        "sources": writer_input["sources"],
        "draft_version": "1.0",
    }
    print(f"  [WriterAgent] Draft written: '{draft_output['title']}'")

    # --- WRITER → EDITOR ---
    print("\n[Step 3] Writer hands off to Editor")
    m3 = Message(
        from_agent="WriterAgent",
        to_agent="EditorAgent",
        task="Review draft for clarity and completeness",
        payload={"draft": draft_output},
    )
    protocol.send(m3)

    received_by_editor = protocol.receive("EditorAgent")
    editor_input = received_by_editor[0].payload["draft"]
    print(f"  [EditorAgent] Received task: '{received_by_editor[0].task}'")
    final_output = {
        **editor_input,
        "review_status": "APPROVED",
        "editorial_notes": "Report is clear, well-sourced, and complete.",
        "draft_version": "1.1 (edited)",
    }
    print(f"  [EditorAgent] Review complete. Status: {final_output['review_status']}")

    # --- EDITOR → COORDINATOR ---
    print("\n[Step 4] Editor returns final report to Coordinator")
    m4 = Message(
        from_agent="EditorAgent",
        to_agent="Coordinator",
        task="Deliver final approved report",
        payload={"final_report": final_output},
    )
    protocol.send(m4)

    received_by_coord = protocol.receive("Coordinator")
    print(f"  [Coordinator] Final report received. Status: "
          f"{received_by_coord[0].payload['final_report']['review_status']}")

    # Print full trace
    protocol.print_trace()
    print(f"\nTotal messages in audit trail: {len(protocol)}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_handoff_demo()
