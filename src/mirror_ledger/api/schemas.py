# mirror_ledger/api/schemas.py

from pydantic import BaseModel, Field
from typing import Dict, Any, List

"""
This module defines the Pydantic models that serve as the data contracts for our API.
Using Pydantic provides several key advantages for a research prototype and beyond:
  1.  Data Validation: Incoming request bodies are automatically parsed and validated
      against these schemas. This prevents malformed data from ever reaching our
      core application logic.
  2.  Type Safety: We get modern, type-hinted objects to work with in our endpoints,
      reducing bugs and improving developer experience.
  3.  Automatic Documentation: FastAPI uses these models to generate interactive
      API documentation (via OpenAPI/Swagger), making the system self-documenting
      and easy to test.
"""

# --- Request Models ---

class IntakeDraftRequest(BaseModel):
    """
    Schema for the initial event that kicks off a workflow trace.
    """
    trace_id: str = Field(..., description="Unique ID for this entire workflow/encounter.")
    content: Dict[str, Any] = Field(..., description="The initial data payload, e.g., vitals and transcript.")
    meta: Dict[str, Any] = Field({}, description="Metadata like IP address or user agent.")

class FeedbackRequest(BaseModel):
    """
    Schema for submitting feedback to an existing block.
    """
    block_index: int = Field(..., description="The index of the block to receive feedback.")
    feedback_delta: Dict[str, Any] = Field(..., description="The new feedback data to merge, e.g., {'status': 'approved', 'notes': '...'}.")


# --- Response Models ---

class BlockResponse(BaseModel):
    """
    Schema for representing a single block in API responses. This decouples our
    API contract from the internal `Block` dataclass implementation.
    """
    index: int
    timestamp: str
    previous_hash: str
    hash: str
    data: Dict[str, Any]
    feedback: Dict[str, Any]

    class Config:
        # This allows Pydantic to create this model directly from our internal `Block` objects.
        from_attributes = True

class ChainResponse(BaseModel):
    """
    Schema for returning the entire blockchain or a subset of it.
    """
    chain: List[BlockResponse]

class GeneralResponse(BaseModel):
    """
    A generic response model for simple status messages.
    """
    status: str
    message: str