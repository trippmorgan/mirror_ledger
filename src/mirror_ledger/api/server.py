# mirror_ledger/api/server.py
from fastapi import FastAPI, Depends, HTTPException, Query
from typing import List, Optional

# Use absolute imports now that our project is an installed package
from mirror_ledger.blockchain.ledger import BlockchainLedger
from mirror_ledger.llm.base_model import Generator
from mirror_ledger.llm.reflection_model import Reflector
from mirror_ledger.adaptation.policy import SEALPolicy
from mirror_ledger.api import schemas


# --- Dependency Injection (now with more components) ---
def get_ledger() -> BlockchainLedger: raise NotImplementedError()
def get_generator() -> Generator: raise NotImplementedError()
def get_reflector() -> Reflector: raise NotImplementedError()
def get_policy() -> SEALPolicy: raise NotImplementedError()

app = FastAPI(
    title="Mirror Ledger API",
    description="API for an event-sourced, auditable, and adaptive AI system.",
    version="0.1.0",
)

# ... (GET /chain and /block/{index} are unchanged) ...
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
    generator: Generator = Depends(get_generator),     # <-- NEW
    reflector: Reflector = Depends(get_reflector)       # <-- NEW
):
    """
    Full E2E Stub Flow: Generate -> Reflect -> Ledger
    """
    # 1. Generate content with the LLM stub
    draft_content = generator.generate_intake(
        transcript=request.content.get("transcript", ""),
        vitals=request.content.get("vitals", {})
    )

    # 2. Reflect on the generated content
    evaluation = reflector.judge(draft_content)
    if not evaluation["ok"]:
        raise HTTPException(
            status_code=400,
            detail={"message": "Generated content violates moral constitution and was blocked.", "violations": evaluation["violations"]}
        )

    # 3. Log the successful event to the blockchain
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
    policy: SEALPolicy = Depends(get_policy) # <-- NEW
):
    """
    Submits feedback and checks the adaptation policy.
    """
    try:
        # Append feedback to the target block
        updated_block = ledger.append_feedback(request.block_index, request.feedback_delta)

        # If feedback includes a correction, check the adaptation policy
        if "correction" in request.feedback_delta:
            if policy.record_feedback():
                print("ADAPTATION TRIGGERED! (Stub)")
                # In a real system, this would dispatch a background job
                # For now, we'll just log an event to the chain.
                ledger.add_block(data={
                    "type": "AdapterPromoted",
                    "trace_id": f"adapt-{utc_iso()}",
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