# src/llm/reflection_model.py
from typing import Dict, Any
# Use an absolute import from the package root
from mirror_ledger.reflection.evaluator import evaluate_output


"""
(STUB) This module provides a 'Reflector' class that wraps the non-AI evaluator.
This acts as an abstraction layer. The API server will call this Reflector.
In the future, we can make this class use a real LLM for more nuanced ethical
judgments, and the API layer won't need to change.
"""

class Reflector:
    def __init__(self, model_name: str = "stub-reflector"):
        self.model_name = model_name
        print(f"Initialized STUB Reflector: {model_name} (wraps rule-based evaluator)")

    def judge(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        (STUB) Wraps the deterministic evaluator.
        """
        print(f"STUB: Judging payload with rule-based evaluator.")
        return evaluate_output(payload)

