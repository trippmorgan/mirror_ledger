# src/mirror_ledger/api/server.py

from fastapi import FastAPI, Depends, HTTPException, Query
from typing import Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Use absolute imports from the package root
from mirror_ledger.blockchain.ledger import BlockchainLedger
from mirror_ledger.llm.base_model import Generator
from mirror_ledger.llm.reflection_model import Reflector
from mirror_ledger.adaptation.policy import SEALPolicy
from mirror_ledger.api import schemas

# Create a dictionary to hold our live, initialized components
# This acts as a simple, reliable state manager for the app.
app_state = {}

# The 'lifespan' manager is the modern way to handle startup/shutdown events.
# This code will run inside the Uvicorn worker process, solving the reloader issue.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Code to run ONCE on startup ---
    load_dotenv()
    print("--- Lifespan Event: Initializing Mirror Ledger Components ---")

    try:
        # Initialize all our components
        master_ledger = BlockchainLedger(storage_path="data/master_ledger.jsonl")
        llm_generator = Generator(model_name="phi3:mini")
        llm_reflector = Reflector(model_name="gemini-1.5-flash")
        adaptation_policy = SEALPolicy(feedback_threshold=3)

        # Store the live components in our state dictionary
        app_state["ledger"] = master_ledger
        app_state["generator"] = llm_generator
        app_state["reflector"] = llm_reflector
        app_state["policy"] = adaptation_policy

        print(f"--- Components Initialized and Ready ---")
        print(f"Ledger has {len(master_ledger.chain)} blocks.")

    except Exception as e:
        print(f"FATAL ERROR during application startup: {e}")
        raise e

    yield # The application is now running

    # --- Code to run ONCE on shutdown ---
    print("--- Lifespan Event: Shutting down. ---")
    app_state.clear()


app = FastAPI(
    title="Mirror Ledger API",
    description="API for an event-sourced, auditable, and adaptive AI system.",
    version="0.1.0",
    lifespan=lifespan # Attach the lifespan manager to the app
)


# --- Dependency Injection Functions ---
# These have been simplified. They now fetch the initialized
# components directly from our reliable app_state.
def get_ledger() -> BlockchainLedger:
    return app_state["ledger"]

def get_generator() -> Generator:
    return app_state["generator"]

def get_reflector() -> Reflector:
    return app_state["reflector"]

def get_policy() -> SEALPolicy:
    return app_state["policy"]


# --- API Endpoints / Routes ---
# (This section is unchanged)

@app.get("/chain", response_model=schemas.ChainResponse, tags=["Blockchain"])
def get_full_chain(trace_id: Optional[str]=Query(None, description="Filter blocks by a specific trace_id."), ledger: BlockchainLedger=Depends(get_ledger)):
    if trace_id:
        return {"chain": ledger.find_by_trace_id(trace_id)}
    return {"chain": ledger.chain}

@app.get("/block/{index}", response_model=schemas.BlockResponse, tags=["Blockchain"])
def get_block_by_index(index: int, ledger: BlockchainLedger=Depends(get_ledger)):
    try:
        return ledger.chain[index]
    except IndexError:
        raise HTTPException(status_code=404, detail=f"Block with index {index} not found.")

@app.post("/events/intake_drafted", response_model=schemas.BlockResponse, status_code=201, tags=["Events"])
def create_intake_event(
    request: schemas.IntakeDraftRequest,
    ledger: BlockchainLedger = Depends(get_ledger),
    generator: Generator = Depends(get_generator),
    reflector: Reflector = Depends(get_reflector)
):
    draft_content = generator.generate_intake(
        transcript=request.content.get("transcript", ""),
        vitals=request.content.get("vitals", {})
    )
    evaluation = reflector.judge(draft_content)
    if not evaluation.get("ok"):
        raise HTTPException(
            status_code=400,
            detail={"message": "Generated content violates moral constitution and was blocked.", "violations": evaluation.get("violations")}
        )
    block_data = {
        "type": "IntakeDrafted",
        "trace_id": request.trace_id,
        "model": {"name": generator.model_name, "adapter_id": generator.adapter_id},
        "content": draft_content,
        "meta": request.meta,
    }
    initial_feedback = {"violations": evaluation.get("violations", [])}
    if initial_feedback["violations"]:
        initial_feedback["status"] = "under_review"
        initial_feedback["notes"] = "Generated with warnings."
    new_block = ledger.add_block(data=block_data, feedback=initial_feedback)
    return new_block

@app.post("/feedback", response_model=schemas.BlockResponse, tags=["Feedback"])
def submit_feedback(
    request: schemas.FeedbackRequest,
    ledger: BlockchainLedger = Depends(get_ledger),
    policy: SEALPolicy = Depends(get_policy)
):
    try:
        updated_block = ledger.append_feedback(request.block_index, request.feedback_delta)
        if "correction" in request.feedback_delta:
            if policy.record_feedback():
                print("ADAPTATION TRIGGERED! (Stub)")
                ledger.add_block(data={
                    "type": "AdapterPromoted",
                    "trace_id": f"adapt-trigger",
                    "content": {
                        "policy": "SEALPolicy_v1_stub",
                        "message": "Adaptation triggered by feedback threshold."
                    }
                })
        return updated_block
    except IndexError:
        raise HTTPException(status_code=404, detail=f"Block with index {request.block_index} not found.")

@app.get("/validate", response_model=schemas.GeneralResponse, tags=["Blockchain"])
def validate_the_chain(ledger: BlockchainLedger=Depends(get_ledger)):
    try:
        ledger.validate_chain()
        return {"status": "ok", "message": f"Chain with {len(ledger.chain)} blocks is valid."}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Chain validation failed: {str(e)}")