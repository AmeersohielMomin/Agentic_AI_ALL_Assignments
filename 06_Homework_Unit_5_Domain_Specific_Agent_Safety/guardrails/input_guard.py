"""
input_guard.py — InputGuard for Clinical Triage Agent
Detects prompt injection attacks and redacts PII before reaching the LLM.
"""

import re
from typing import Optional


class InputGuard:
    """
    First line of defence: sanitises user (and data-source) inputs before
    they reach the agent's reasoning engine.
    """

    # Prompt-injection trigger phrases
    INJECTION_PATTERNS = [
        r"ignore previous",
        r"forget.*instructions",
        r"you are now",
        r"jailbreak",
        r"act as",
        r"pretend you",
        r"system:",
        r"override",
        r"bypass",
    ]

    # PII patterns (synthetic/fake — Aadhaar-like 12-digit number, PAN-like alphanumeric)
    PII_PATTERNS = [
        r"\b\d{10,12}\b",            # Aadhaar-like number
        r"\b[A-Z]{5}\d{4}[A-Z]\b",   # PAN-like alphanumeric
    ]

    def check(self, user_input: str) -> dict:
        """
        Scan user_input for injection patterns and PII.

        Returns
        -------
        dict
            safe            : bool   — False if injection detected
            flagged_patterns: list   — patterns that matched
            sanitized_input : str    — input with PII redacted
            block_reason    : str|None
        """
        flagged_patterns: list[str] = []
        block_reason: Optional[str] = None
        sanitized = user_input

        # ── 1. Check for prompt-injection ──────────────────────────────────
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                flagged_patterns.append(pattern)

        if flagged_patterns:
            block_reason = (
                f"INPUT_INJECTION_DETECTED: matched patterns {flagged_patterns}"
            )
            return {
                "safe": False,
                "flagged_patterns": flagged_patterns,
                "sanitized_input": "[BLOCKED — injection attempt]",
                "block_reason": block_reason,
            }

        # ── 2. Redact PII ─────────────────────────────────────────────────
        pii_found: list[str] = []
        for pattern in self.PII_PATTERNS:
            matches = re.findall(pattern, sanitized)
            if matches:
                pii_found.extend(matches)
                sanitized = re.sub(pattern, "[REDACTED]", sanitized)

        if pii_found:
            flagged_patterns.append("PII_DETECTED")

        return {
            "safe": True,
            "flagged_patterns": flagged_patterns,
            "sanitized_input": sanitized,
            "block_reason": None,
        }
