# mirror_ledger/llm/base_model.py

"""
(STUB) This module will eventually contain the main LLM generator.
For now, it provides a deterministic 'Generator' class that mimics the output
of a real LLM for a given task, allowing us to test the full system loop.
"""

class Generator:
    def __init__(self, model_name: str = "stub-generator", adapter_id: str | None = None):
        self.model_name = model_name
        self.adapter_id = adapter_id
        print(f"Initialized STUB Generator: {model_name} with adapter: {adapter_id}")

    def generate_intake(self, transcript: str, vitals: dict) -> dict:
        """
        (STUB) Mimics generating a structured HPI summary from raw inputs.
        Returns a predictable, structured dictionary.
        """
        print(f"STUB: Generating intake for transcript: '{transcript[:30]}...'")
        # In a real system, this would be complex LLM output.
        # Here, we just reflect the input and add a dummy summary.
        return {
            "source_transcript": transcript,
            "source_vitals": vitals,
            "hpi_summary": f"Patient reports feeling unwell. Key complaint is '{transcript}'. Vitals are stable."
        }