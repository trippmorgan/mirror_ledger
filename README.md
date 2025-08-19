# ✝️ The Mirror Ledger

**An event-sourced, auditable, and adaptive AI system rooted in a moral constitution.**

This project is a functional prototype of the "Mirror Ledger," a system designed to create trustworthy AI through radical transparency and guided adaptation. It combines a blockchain-based immutable ledger, a "mirror neuron" reflection engine for moral self-assessment, and a framework for safe, parameter-efficient fine-tuning.

### Core Concepts

1.  **Event-Sourced Blockchain:** Every significant action—AI generation, human feedback, model adaptation—is recorded as a structured, typed event on a verifiable blockchain. This creates an immutable audit trail, making the AI's entire lifecycle transparent and traceable.
2.  **Mirror Reflection:** Before an AI's output is accepted, it is first "reflected" upon by an internal evaluator. This engine judges the output against a non-negotiable moral constitution, blocking or flagging content that violates core principles.
3.  **Guided Adaptation:** Human feedback, especially corrections, is collected and used to fine-tune the model using parameter-efficient techniques (LoRA). This adaptation process is itself an event that is recorded on the blockchain, ensuring that even the AI's "learning" is part of its auditable history.

### Project Structure

mirror_ledger/
├── llm/ # (STUB) Handles LLM generation and reflection
│ ├── base_model.py
│ └── reflection_model.py
├── blockchain/ # The core ledger implementation
│ ├── block.py
│ ├── ledger.py
│ └── utils.py
├── adaptation/ # (STUB) Manages model fine-tuning
│ ├── policy.py
│ ├── data_manager.py
│ └── finetune.py
├── reflection/ # The moral evaluation engine
│ ├── constitution.py
│ └── evaluator.py
├── api/ # FastAPI server and data schemas
│ ├── server.py
│ └── schemas.py
├── ui/ # (Future) UI components
│ └── dashboard.py
├── main.py # Main application entry point
├── requirements.txt # Python dependencies
└── .gitignore # Git ignore file



### Installation and Setup

This project uses Conda for environment management to ensure reproducibility.

**1. Prerequisites**
*   You must have [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or Anaconda installed.

**2. Clone the Repository**
```bash
git clone <your-repository-url>
cd mirror_ledger-main
ollama pull phi3:mini


conda create --name mirror-ledger python=3.9 -y
conda activate mirror-ledger
pip install -r requirements.txt
pip install -e .
pip install google-generativeai
pip install streamlit requests pandas


### Running the Application

With the Conda environment active, start the FastAPI server with a single command from the project's root directory:

```bash
python main.py```
python -m mirror_ledger
You should see output indicating that the components have been initialized and the Uvicorn server is running.

Run the Dashboard: In a second terminal, run the Streamlit app.


streamlit run dashboard.py


### How to Interact with the API

The system is now running and accessible. You can interact with it using your web browser or a command-line tool like `curl`.

**1. Using the Interactive API Docs (Recommended)**

*   Open your web browser and navigate to **`http://127.0.0.1:8000/docs`**.
*   This will load the auto-generated Swagger UI, where you can explore and execute every API endpoint directly from your browser.

**2. Using `curl` from the Command Line**

*   **Get the entire chain:**
    ```bash
    curl http://127.0.0.1:8000/chain
    ```

*   **Create a new clinical intake event:**
    ```bash
    curl -X POST http://127.0.0.1:8000/events/intake_drafted -H "Content-Type: application/json" -d '{"trace_id": "trace-001", "content": {"transcript": "patient has a headache", "vitals": {"bp": "120/80"}}}'
    ```

*   **Add "approved" feedback to Block 1 (the one you just created):**
    ```bash
    curl -X POST http://127.0.0.1:8000/feedback -H "Content-Type: application/json" -d '{"block_index": 1, "feedback_delta": {"status": "approved", "annotator": "did:clinic:dr_kay"}}'
    ```

*   **Submit a correction to trigger the adaptation policy:**
    (Submit this command 3 times to meet the policy threshold of 3)
    ```bash
    curl -X POST http://127.0.0.1:8000/feedback -H "Content-Type: application/json" -d '{"block_index": 1, "feedback_delta": {"correction": "Patient has a severe migraine, not just a headache."}}'
    ```
    *After the 3rd time, you will see "ADAPTATION TRIGGERED!" in the server logs, and a new `AdapterPromoted` block will appear on the chain.*

*   **Filter the chain to see only events for `trace-001`:**
    ```bash
    curl "http://127.0.0.1:8000/chain?trace_id=trace-001"
    ```

*   **Validate the integrity of the entire chain:**
    ```bash
    curl http://127.0.0.1:8000/validate
    ```
```--- END OF FILE mirror_ledger-main/README.md ---

This is a huge step forward. You now have a complete, well-documented, and runnable prototype. The project is professional, clean, and ready for the next, most exciting phase: replacing the stubs with real, intelligent LLM components.