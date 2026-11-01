"""
Safe Code Execution Tool
========================
Executes simple math expressions and safe Python one-liners using eval()
inside a tightly restricted namespace.  Dangerous constructs (imports,
file I/O, network calls, etc.) are blocked before evaluation.
"""

import math
import re


# ---------------------------------------------------------------------------
# Forbidden keywords / patterns
# ---------------------------------------------------------------------------
_FORBIDDEN_PATTERNS = [
    r"\bimport\b",
    r"\b__import__\b",
    r"\bopen\b",
    r"\bexec\b",
    r"\beval\b",         # nested eval
    r"\bos\b",
    r"\bsys\b",
    r"\bsubprocess\b",
    r"\bsocket\b",
    r"\burllib\b",
    r"\brequests\b",
    r"\bfile\b",
    r"\bwrite\b",
    r"\bread\b",
    r"\bcompile\b",
    r"\bglobals\b",
    r"\blocals\b",
    r"\bvars\b",
    r"\bgetattr\b",
    r"\bsetattr\b",
    r"\bdelattr\b",
    r"\b__\w+__\b",      # dunder attributes
]

_FORBIDDEN_RE = re.compile("|".join(_FORBIDDEN_PATTERNS))

# Safe namespace exposed to eval
_SAFE_NAMESPACE: dict = {
    "__builtins__": {},   # no builtins
    # Math functions
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "pow": pow,
    "len": len,
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
    "range": range,
    # math module functions
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "floor": math.floor,
    "ceil": math.ceil,
    "pi": math.pi,
    "e": math.e,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
}


class SafeCodeExecTool:
    """Safely evaluates math expressions and simple Python one-liners."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(self, code_str: str) -> dict:
        """
        Execute *code_str* in a restricted namespace.

        Parameters
        ----------
        code_str : str
            A Python expression or simple arithmetic string.

        Returns
        -------
        dict with keys:
            output  – string representation of the result
            success – bool
            error   – error message (empty string on success)
        """
        code_str = code_str.strip()

        # --- Safety gate ---
        if _FORBIDDEN_RE.search(code_str):
            return {
                "output": "",
                "success": False,
                "error": (
                    f"Unsafe code detected: forbidden construct found in '{code_str}'. "
                    "Execution blocked."
                ),
            }

        # --- Evaluation ---
        try:
            result = eval(code_str, _SAFE_NAMESPACE.copy())  # noqa: S307
            return {"output": str(result), "success": True, "error": ""}
        except Exception as exc:  # noqa: BLE001
            return {"output": "", "success": False, "error": str(exc)}

    def __repr__(self) -> str:
        return "SafeCodeExecTool(sandbox=restricted_eval)"


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tool = SafeCodeExecTool()

    tests = [
        "2 + 2",
        "sqrt(144)",
        "round(15 / 100 * 1500, 2)",
        "5000 * 3 + 1500 * 3",          # hotel + meals for 3 nights
        "8500 + 4000 * 2",              # flight + hotel 2 nights
        "import os",                    # should be blocked
        "open('secret.txt')",           # should be blocked
        "__import__('os').system('ls')",# should be blocked
    ]

    for t in tests:
        result = tool.execute(t)
        status = "✓" if result["success"] else "✗"
        print(f"{status} `{t}` → output={result['output']!r}  error={result['error']!r}")
