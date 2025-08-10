
```--- END OF FILE mirror_ledger/main.py ---

### How to Run This Commit

1.  **Install Dependencies:**
    ```bash
    pip install "fastapi[all]"
    ```
    *(Note: `[all]` includes `uvicorn`, `pydantic`, etc.)*

2.  **Run the Server:** From your project's root directory (`mirror_ledger/`), run:
    ```bash
    python main.py
    ```

3.  **Interact with the API:**
    *   Open your web browser to **`http://127.0.0.1:8000/docs`**. You will see the auto-generated interactive API documentation.
    *   **Or, use `curl` from another terminal:**
        *   **Get the chain:** `curl http://127.0.0.1:8000/chain`
        *   **Create a new event:**
            ```bash
            curl -X POST http://127.0.0.1:8000/events/intake_drafted -H "Content-Type: application/json" -d '{"trace_id": "trace-001", "content": {"vitals": "120/80"}}'
            ```
        *   **Add feedback to the Genesis block (index 0):**
            ```bash
            curl -X POST http://127.0.0.1:8000/feedback -H "Content-Type: application/json" -d '{"block_index": 0, "feedback_delta": {"status": "approved", "annotator": "did:clinic:dr_kay"}}'
            ```
        *   **Filter by trace_id:** `curl "http://127.0.0.1:8000/chain?trace_id=trace-001"`
        *   **Validate the chain:** `curl http://127.0.0.1:8000/validate`

This completes **Commit 2**. You now have a working, persistent, and interactive blockchain ledger accessible via a modern API. We are ready to build the reflection and adaptation layers on top of this solid foundation.