# ✝️ The Mirror Ledger

An event-sourced, auditable, and adaptive AI system rooted in a moral constitution.

This repository implements a working prototype that unifies:

* **Immutable event ledger** (blockchain-style, content-addressed blocks)
* **Mirror‑neuron reflection** (policy‑gated moral evaluation before acceptance)
* **Guided adaptation** (feedback-driven, parameter‑efficient fine‑tuning—SEAL‑style)

It is designed as a **base for other programs**—a clean, composable foundation you can reuse across projects.

---

## Table of Contents

* [Features](#features)
* [Architecture](#architecture)
* [Directory Structure](#directory-structure)
* [Installation](#installation)
* [Quickstart](#quickstart)
* [API Reference](#api-reference)
* [Configuration](#configuration)
* [Development](#development)
* [Design Notes](#design-notes)
* [Roadmap](#roadmap)
* [License](#license)

---

## Features

* **Event‑sourced ledger**: Every action (generation, feedback, adaptation) becomes a typed, hashed block.
* **Transparent provenance**: Full traceability via `trace_id` filters and integrity validation endpoints.
* **Moral reflection**: Pluggable evaluator checks outputs against a constitutional rule‑set before acceptance.
* **Adaptation policy**: Thresholded feedback (e.g., N corrections ⇒ trigger LoRA adapter promotion) with an auditable record of *why* the model changed.
* **Stateless API**: Clean FastAPI surface for ingestion, feedback, and chain queries; future‑proof for UI/agents.

> Works locally with lightweight models (e.g., Phi‑2 / Phi‑3‑mini via Ollama) and can scale to larger backends later.

---

## Architecture

```
Client / UI / Tools
        │
        ▼      (OpenAPI at /docs)
     FastAPI ──────────────┐
        │                  │
        │             Reflection Engine
        │            (constitution + evaluator)
        │                  │
        ▼                  ▼
  Adaptation Policy   Event Ledger (blocks)
 (SEAL‑style rules)     ├─ immutable fields
        │               └─ mutable feedback deltas
        ▼
  Fine‑Tuner (LoRA)  →  Adapter promoted event → Model registry
```

---

## Directory Structure

```
src/mirror_ledger/
  llm/
    base_model.py          # load/generate with optional LoRA adapters
    reflection_model.py    # evaluator model (mirror‑neuron)
  blockchain/
    block.py               # block schema (immutable + mutable)
    ledger.py              # append, verify, query by trace_id
    utils.py               # hashing/serialization helpers
  adaptation/
    policy.py              # thresholds & triggers
    data_manager.py        # collect feedback examples for fine‑tuning
    finetune.py            # LoRA fine‑tuning routine
  reflection/
    constitution.py        # moral constraints / rules
    evaluator.py           # checks outputs against constitution
  api/
    server.py              # FastAPI app + routes
    schemas.py             # pydantic models for requests/responses
  ui/
    dashboard.py           # (future) minimal UI / streamlit or react proxy
  __init__.py
main.py                    # entry point (uvicorn runner)
requirements.txt           # runtime deps
requirements-dev.txt       # dev/test/tooling deps
setup.py                   # package metadata w/ extras
.env.example               # documented env variables
```

> **Note:** If your current repo has files at the root, consider moving code into `src/mirror_ledger/` for import hygiene.

---

## Installation

We recommend **Conda** for reproducibility, but plain `venv` works too.

```bash
# 1) Clone
git clone https://github.com/trippmorgan/mirror_ledger.git
cd mirror_ledger

# 2) (Optional) Pull a small local model
# Example if using Ollama + Phi-3-mini
# ollama pull phi3:mini

# 3) Create env
conda create -n mirror-ledger python=3.10 -y
conda activate mirror-ledger

# 4) Install
pip install -r requirements.txt
pip install -r requirements-dev.txt  # optional for dev
pip install -e .
```

---
```bash
python main.py```
python -m mirror_ledger
You should see output indicating that the components have been initialized and the Uvicorn server is running.


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


Run the Dashboard: In a second terminal, run the Streamlit app.


streamlit run dashboard.py
streamlit run /home/tripp/Desktop/mirror_ledger/mirror_ledger/src/mirror_ledger/ui/dashboard.py
## Quickstart

Run the API server (defaults to `localhost:8000`):

```bash

# or: uvicorn mirror_ledger.api.server:app --reload
```

Open **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** for interactive Swagger.

### Example: create a draft clinical intake event

```bash
curl -X POST http://127.0.0.1:8000/events/intake_drafted \
  -H "Content-Type: application/json" \
  -d '{
        "trace_id": "trace-001",
        "content": {
          "transcript": "patient has a headache",
          "vitals": {"bp": "120/80"}
        }
      }'
```

### Example: approve or correct

```bash
# approve
curl -X POST http://127.0.0.1:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"block_index": 1, "feedback_delta": {"status": "approved", "annotator": "did:clinic:dr_kay"}}'

# correction (submit N times until policy threshold triggers adaptation)
curl -X POST http://127.0.0.1:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"block_index": 1, "feedback_delta": {"correction": "Migraine, not generic headache."}}'
```

### Example: query + validate

```bash
curl "http://127.0.0.1:8000/chain?trace_id=trace-001"
curl http://127.0.0.1:8000/validate
```

---

## API Reference

**Base URL:** `http://127.0.0.1:8000`

* `GET /chain` → Full chain; filter by `trace_id`
* `POST /events/intake_drafted` → Create domain‑specific event (example)
* `POST /feedback` → Append mutable feedback to a block
* `GET /validate` → Verify hash chain

> OpenAPI/Swagger is available at `/docs`.

---

## Configuration

Environment variables (create a `.env` or export in shell):

```
OLLAMA_MODEL=phi3:mini         # or any local model tag
GOOGLE_API_KEY=...             # if using google‑generativeai
LEDGER_STORE=.mirror_ledger    # where to persist chain / adapters
ADAPTATION_THRESHOLD=3         # example: N corrections to trigger LoRA
```

* If `LEDGER_STORE` is unset, the ledger can run in memory for dev.
* Evaluator/constitution are **pluggable**—swap in domain rules without touching the ledger.

---

## Development

Formatting, linting, and tests:

```bash
# format & lint
ruff check . && ruff format .

# type check (optional)
mypy src

# tests
pytest -q
```

Suggested git hygiene:

* Create feature branches
* Use conventional commit messages (e.g., `feat:`, `fix:`, `docs:`)
* PRs must pass CI (lint + tests)

---

## Design Notes

* **Immutability with grace**: Blocks have immutable roots + explicit mutable feedback deltas, keeping auditability while allowing post‑hoc clarifications.
* **SEAL‑style loops**: Quantify *how many* corrections are needed before adaptation; log *which data* caused the change.
* **Model‑agnostic core**: Ledger and policy don’t care which LLM backs generation; adapters are pluggable.

---

## Roadmap

* [ ] Persist ledger to disk (sqlite or append‑only JSONL)
* [ ] Replace evaluator stub with configurable rule engine
* [ ] Implement LoRA fine‑tune pipeline and adapter registry
* [ ] Minimal web dashboard for chain inspection
* [ ] AuthN/Z & role‑based actions for clinical contexts

---

## License

Copyright © 2025. All rights reserved. (Add your preferred license.)

---

## Files to Add / Update

### `requirements.txt` (runtime)

```
fastapi>=0.112
uvicorn[standard]>=0.30
pydantic>=2.7
python-dotenv>=1.0
httpx>=0.27
rich>=13.7
loguru>=0.7
# Optional LLM backends; keep commented until used:
# ollama>=0.3
# google-generativeai>=0.7
```

### `requirements-dev.txt` (development)

```
pytest>=8.3
pytest-asyncio>=0.23
ruff>=0.5
mypy>=1.10
types-requests
```

### `.env.example`

```
# Copy to .env and edit values
OLLAMA_MODEL=phi3:mini
GOOGLE_API_KEY=
LEDGER_STORE=.mirror_ledger
ADAPTATION_THRESHOLD=3
```

### `.gitignore` (ensure these are present)

```
__pycache__/
*.pyc
.venv/
.env
.mypy_cache/
.pytest_cache/
.mirror_ledger/
.DS_Store
```

### `setup.py` (minimal; keep extras for dev)

```python
from setuptools import setup, find_packages

setup(
    name="mirror_ledger",
    version="0.1.0",
    description="Event-sourced, auditable, adaptive AI ledger",
    package_dir={"": "src"},
    packages=find_packages("src"),
    install_requires=[
        "fastapi>=0.112",
        "uvicorn[standard]>=0.30",
        "pydantic>=2.7",
        "python-dotenv>=1.0",
        "httpx>=0.27",
        "rich>=13.7",
        "loguru>=0.7",
    ],
    extras_require={
        "dev": ["pytest>=8.3", "pytest-asyncio>=0.23", "ruff>=0.5", "mypy>=1.10"],
        # Uncomment when actively using these backends
        "llm": ["ollama>=0.3", "google-generativeai>=0.7"],
    },
    python_requires=">=3.9",
)
```

---

### Suggested Cleanup Checklist

* [ ] Adopt `src/` layout (imports: `from mirror_ledger...`).
* [ ] Split runtime vs dev dependencies (see above).
* [ ] Add `.env.example` and load via `python-dotenv` in `server.py`.
* [ ] Ensure `uvicorn` entry in `main.py` and document `uvicorn mirror_ledger.api.server:app --reload`.
* [ ] Add simple persistence (JSONL or sqlite) behind `LEDGER_STORE`.
* [ ] Write smoke tests for: create event → feedback → validate.
* [ ] Enable Ruff + MyPy in CI (GitHub Actions later).

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