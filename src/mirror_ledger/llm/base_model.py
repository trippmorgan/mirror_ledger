# src/mirror_ledger/llm/base_model.py
import requests
import json
from typing import Dict, Any, Optional # <-- IMPORT 'Optional'

"""
This module contains the LLM 'Generator'.
This implementation calls a local model served by Ollama to handle high-frequency,
domain-specific tasks like drafting clinical notes.
"""

class Generator:
    # VVV --- THIS IS THE LINE WE ARE FIXING --- VVV
    def __init__(self, model_name: str = "phi3:mini", adapter_id: Optional[str] = None, ollama_url: str = "http://localhost:11434/api/generate"):
        """
        Initializes the Generator to connect to a local Ollama instance.

        Args:
            model_name: The name of the model to use in Ollama (e.g., 'phi3:mini').
            adapter_id: The identifier for any PEFT/LoRA adapter being used (for future use).
            ollama_url: The URL of the Ollama API endpoint.
        """
        self.model_name = model_name
        self.adapter_id = adapter_id  # For logging and traceability
        self.url = ollama_url
        print(f"Initialized Ollama Generator with model: '{self.model_name}' at {self.url}")

    def _create_prompt(self, transcript: str, vitals: dict) -> str:
        """Creates a structured prompt for the clinical intake task."""
        return f"""
        **Task:** Generate a concise "History of Present Illness" (HPI) summary.
        **Instructions:**
        - Use the provided transcript and vitals.
        - Be objective and clinical in tone.
        - Do not add information not present in the source.
        - Structure the output as a JSON object with one key: "hpi_summary".

        **Transcript:**
        "{transcript}"

        **Vitals:**
        {json.dumps(vitals)}

        **JSON Output:**
        """

    def generate_intake(self, transcript: str, vitals: dict) -> Dict[str, Any]:
        """
        Generates a structured HPI summary by calling the Ollama API.
        """
        print(f"Generator: Generating intake for transcript: '{transcript[:30]}...'")
        prompt = self._create_prompt(transcript, vitals)

        try:
            response = requests.post(
                self.url,
                json={"model": self.model_name, "prompt": prompt, "stream": False, "format": "json"},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            # Ollama returns the JSON response as a string in the 'response' key.
            response_text = response.json().get("response", "{}")
            generated_content = json.loads(response_text)

            # Combine source data with the LLM's generation for a complete record.
            return {
                "source_transcript": transcript,
                "source_vitals": vitals,
                **generated_content  # Merge the generated hpi_summary
            }

        except requests.exceptions.RequestException as e:
            print(f"ERROR: Could not connect to Ollama. Is it running? Details: {e}")
            # Fallback to a failure message in the content
            return {"error": "Failed to generate content due to connection error.", "hpi_summary": "GENERATION FAILED."}
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to decode JSON from Ollama response: {response_text}. Details: {e}")
            return {"error": "Failed to decode LLM output.", "hpi_summary": "GENERATION FAILED - INVALID FORMAT."}