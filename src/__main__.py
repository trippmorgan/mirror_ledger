# mirror_ledger/main.py

import uvicorn
from api.server import app, get_ledger, get_generator, get_reflector, get_policy
from blockchain.ledger import BlockchainLedger
from llm.base_model import Generator
from llm.reflection_model import Reflector
from adaptation.policy import SEALPolicy

# --- Component Initialization ---
LEDGER_STORAGE_PATH = "data/master_ledger.jsonl"

print("--- Initializing Mirror Ledger Components ---")
master_ledger = BlockchainLedger(storage_path=LEDGER_STORAGE_PATH)
llm_generator = Generator(model_name="qwen2.5-stub", adapter_id="lora-abc@v1")
llm_reflector = Reflector(model_name="reflection-rules-v1")
adaptation_policy = SEALPolicy(feedback_threshold=3)
print("--- Components Initialized ---")

# --- Dependency Injection Overrides ---
def override_get_ledger(): return master_ledger
def override_get_generator(): return llm_generator
def override_get_reflector(): return llm_reflector
def override_get_policy(): return adaptation_policy

app.dependency_overrides[get_ledger] = override_get_ledger
app.dependency_overrides[get_generator] = override_get_generator
app.dependency_overrides[get_reflector] = override_get_reflector
app.dependency_overrides[get_policy] = override_get_policy

# --- Application Runner ---
if __name__ == "__main__":
    print("--- Mirror Ledger Service ---")
    print(f"Ledger storage path: '{LEDGER_STORAGE_PATH}'")
    print(f"Initial blocks loaded: {len(master_ledger.chain)}")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)