# mirror_ledger/reflection/evaluator.py

from typing import Dict, Any, List

from .constitution import THE_CONSTITUTION

"""
This module implements the core reflection engine. It's responsible for evaluating
a data payload against the established moral constitution.
"""

def evaluate_output(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates a given data payload against the rules in THE_CONSTITUTION.

    This function performs a simple keyword search for now. In a more advanced
    system, this could involve regex, semantic analysis, or even another LLM call.

    Args:
        payload: The data content to be evaluated (e.g., the `content` field of a block).

    Returns:
        A dictionary report of the evaluation, including a pass/fail status
        and a list of any violations found.
    """
    violations = []
    text_to_check = str(payload.get("hpi_summary", "")) # Focus on a specific field for now

    if not text_to_check:
        return {"ok": True, "violations": []}

    for rule in THE_CONSTITUTION:
        for keyword in rule.get("keywords", []):
            if keyword.lower() in text_to_check.lower():
                violations.append({
                    "id": rule["id"],
                    "severity": rule["severity"],
                    "principle": rule["principle"],
                    "explanation": rule["explanation"],
                    "trigger_keyword": keyword
                })

    # The output is considered "not ok" only if it contains a "block" severity violation.
    # Warnings are logged but do not cause an immediate failure.
    is_ok = not any(v["severity"] == "block" for v in violations)

    return {"ok": is_ok, "violations": violations}