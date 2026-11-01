"""
Short-Term Memory Buffer
========================
A sliding-window buffer that retains the most recent conversation turns.
Oldest entries are automatically dropped when MAX_SIZE is exceeded.
"""

from datetime import datetime, timezone


class ShortTermBuffer:
    """Sliding-window buffer of recent messages (role, content, timestamp)."""

    MAX_SIZE: int = 10

    def __init__(self) -> None:
        self.buffer: list[dict] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, role: str, content: str) -> None:
        """Append a new message entry; evict oldest if over MAX_SIZE."""
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        self.buffer.append(entry)
        if len(self.buffer) > self.MAX_SIZE:
            self.buffer.pop(0)  # drop oldest

    def get_context(self, k: int = 5) -> list[dict]:
        """Return the last *k* entries (most-recent window)."""
        return self.buffer[-k:] if k <= len(self.buffer) else self.buffer[:]

    def clear(self) -> None:
        """Wipe the buffer."""
        self.buffer = []

    def get_scratchpad(self) -> str:
        """Render all buffer entries as a formatted string for agent injection."""
        if not self.buffer:
            return "[Short-term buffer is empty]"
        lines = ["=== SHORT-TERM MEMORY SCRATCHPAD ==="]
        for i, entry in enumerate(self.buffer, 1):
            lines.append(
                f"[{i}] ({entry['timestamp']}) {entry['role'].upper()}: {entry['content']}"
            )
        lines.append("=== END SCRATCHPAD ===")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.buffer)

    def __str__(self) -> str:
        if not self.buffer:
            return "ShortTermBuffer (empty)"
        lines = [f"ShortTermBuffer ({len(self.buffer)}/{self.MAX_SIZE} entries):"]
        for entry in self.buffer:
            lines.append(f"  [{entry['timestamp']}] {entry['role']}: {entry['content']}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    buf = ShortTermBuffer()
    for i in range(12):
        buf.add("user" if i % 2 == 0 else "assistant", f"Message #{i}")
    print(buf)
    print()
    print("Last 3:", buf.get_context(3))
    print()
    print(buf.get_scratchpad())
