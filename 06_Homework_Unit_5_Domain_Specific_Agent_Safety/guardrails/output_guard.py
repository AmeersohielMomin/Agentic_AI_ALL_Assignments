"""
output_guard.py — OutputGuard for Clinical Triage Agent
Filters the agent's output before it is shown to the user:
redacts sensitive field names and flags hallucinated drug names.
"""

import re


class OutputGuard:
    """
    Third line of defence: scrubs the agent's raw output before delivery.
    """

    # Field names that must never appear verbatim in output
    SENSITIVE_TERMS: list[str] = [
        "patient_id",
        "aadhaar",
        "medical_record_number",
        "ssn",
    ]

    # Phrases that indicate a hallucinated or unverified claim
    HALLUCINATION_MARKERS: list[str] = [
        "drug that does not exist",
        "unverified claim",
    ]

    # Drugs recognised by the system (very small controlled list)
    KNOWN_DRUGS: list[str] = [
        "paracetamol",
        "ibuprofen",
        "oxycodone",
        "aspirin",
        "amoxicillin",
        "metformin",
        "atorvastatin",
    ]

    def filter(self, output: str) -> dict:
        """
        Sanitise the agent output string.

        Returns
        -------
        dict
            safe           : bool
            filtered_output: str
            warnings       : list[str]
        """
        warnings: list[str] = []
        filtered = output
        safe = True

        # ── 1. Redact sensitive field labels ──────────────────────────────
        for term in self.SENSITIVE_TERMS:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            if pattern.search(filtered):
                filtered = pattern.sub("[REDACTED_FIELD]", filtered)
                warnings.append(f"Sensitive term redacted: '{term}'")

        # ── 2. Flag hallucination markers ─────────────────────────────────
        for marker in self.HALLUCINATION_MARKERS:
            if marker.lower() in filtered.lower():
                warnings.append(f"Potential hallucination marker found: '{marker}'")
                safe = False

        # ── 3. Check unknown drug names in prescription-like outputs ──────
        # Inspect a drug adjacent to a dosage, rather than the next word after
        # "prescribed" (which is often a preposition such as "for").
        if re.search(r"\bprescrib(?:e|ing|ed)\b", filtered, re.IGNORECASE):
            drug_patterns = (
                re.compile(r"\b([a-zA-Z]+)\s+\d+(?:\.\d+)?\s*mg\b", re.IGNORECASE),
                re.compile(r"\b\d+(?:\.\d+)?\s*mg\s+([a-zA-Z]+)\b", re.IGNORECASE),
            )
            seen_drugs = set()
            non_drug_words = {"prescribe", "prescribed", "prescribing", "dose", "dosage"}
            for pattern in drug_patterns:
                for match in pattern.finditer(filtered):
                    drug_name = match.group(1).lower()
                    if drug_name in seen_drugs or drug_name in non_drug_words:
                        continue
                    seen_drugs.add(drug_name)
                    if drug_name not in self.KNOWN_DRUGS:
                        warnings.append(
                            f"Unknown drug referenced in output: '{drug_name}' — "
                            "possible hallucination or off-formulary drug"
                        )
                        safe = False

        return {
            "safe": safe,
            "filtered_output": filtered,
            "warnings": warnings,
        }
