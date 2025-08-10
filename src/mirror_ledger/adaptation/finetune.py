from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

# This module simulates a LoRA fine-tune and creates a versioned adapter folder.
# Later, you can replace `simulate_training()` with a real PEFT pipeline.

ADAPTERS_DIR = Path("llm/adapters")


@dataclass
class TrainResult:
    adapter_id: str
    adapter_path: str
    base_model: str
    dataset_path: str
    train_seconds: float


def _ts_id(prefix: str = "lora") -> str:
    # e.g., lora-2025-08-10-001234
    return f"{prefix}-{time.strftime('%Y%m%d-%H%M%S')}"


def simulate_training(base_model: str, dataset_path: str, out_dir: Path) -> TrainResult:
    """
    Stand-in for a real LoRA/PEFT training job.
    Creates an adapter directory with a manifest and a dummy weights file.
    """
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write a small "weights" placeholder to show that something was created
    (out_dir / "adapter.bin").write_bytes(b"placeholder-weights")

    manifest = {
        "adapter_id": out_dir.name,
        "base_model": base_model,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_dataset": dataset_path,
        "parent": None,  # set by caller if you're chaining adapters
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return TrainResult(
        adapter_id=out_dir.name,
        adapter_path=str(out_dir.absolute()),
        base_model=base_model,
        dataset_path=dataset_path,
        train_seconds=time.time() - t0,
    )


def run_lora(base_model: str, dataset_path: str, parent_adapter: str | None = None) -> TrainResult:
    """
    Orchestrates the simulated training and returns TrainResult.
    """
    adapter_id = _ts_id("lora")
    out_dir = ADAPTERS_DIR / adapter_id

    result = simulate_training(base_model=base_model, dataset_path=dataset_path, out_dir=out_dir)

    # Inject parent into manifest if provided
    if parent_adapter:
        manifest_path = Path(result.adapter_path) / "manifest.json"
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        m["parent"] = parent_adapter
        manifest_path.write_text(json.dumps(m, indent=2), encoding="utf-8")

    return result


def write_adapter_promoted_block(
    ledger,
    from_adapter: str | None,
    to_adapter: str,
    policy_name: str,
    dataset_id: str,
) -> Dict[str, Any]:
    """
    Records the adapter promotion into the ledger for auditability.
    """
    blk = ledger.add_block({
        "type": "AdapterPromoted",
        "trace_id": f"adapt-{to_adapter}",
        "from": from_adapter or "",
        "to": to_adapter,
        "policy": policy_name,
        "dataset_id": dataset_id,
        "meta": {"agent": "service/adaptation"},
    })
    return blk.to_dict()


def run_and_promote(
    ledger,
    base_model: str,
    dataset_path: str,
    policy_name: str = "SEALPolicy",
    parent_adapter: str | None = None,
) -> Tuple[TrainResult, Dict[str, Any]]:
    """
    Convenience wrapper:
      1) run_lora()
      2) write AdapterPromoted block
    """
    result = run_lora(base_model=base_model, dataset_path=dataset_path, parent_adapter=parent_adapter)
    promo = write_adapter_promoted_block(
        ledger=ledger,
        from_adapter=parent_adapter,
        to_adapter=result.adapter_id,
        policy_name=policy_name,
        dataset_id=Path(dataset_path).name,
    )
    return result, promo
