from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

# NOTE: The ledger interface we expect:
#   - ledger.iter_blocks() -> Iterable[Block]
#   - Each Block has .data (dict) and .feedback (dict)
#   - IntakeDrafted blocks: data = {
#       "type":"IntakeDrafted",
#       "trace_id": "...",
#       "patient_id": "...",
#       "encounter_id": "...",
#       "vitals": {...},
#       "hpi_summary": "...",
#       "model": {...},
#       "meta": {...}
#     }
#   - Feedback is appended via /feedback and may include:
#       feedback = {"labels":[...], "notes":"...", "annotator":"...", "status":"approved|..."}
#
# We turn these into training pairs like:
#   {"input":{"vitals":{...},"hpi_summary":"..."}, "labels":[...], "correction":"...", "trace_id":"..."}


@dataclass
class TrainingPair:
    trace_id: str
    input: Dict[str, Any]
    labels: List[str]
    correction: str
    annotator: Optional[str] = None
    adapter_hint: Optional[str] = None  # e.g., prior adapter in use


def _is_intake_block(b: Any) -> bool:
    return isinstance(b.data, dict) and b.data.get("type") == "IntakeDrafted"


def _correction_from_feedback(fb: Dict[str, Any]) -> str:
    """
    We allow two ways to supply corrections:
      - fb["correction"] (preferred, structured in the future)
      - fb["notes"] (fallback for free-text)
    """
    if not fb:
        return ""
    if isinstance(fb.get("correction"), str) and fb["correction"].strip():
        return fb["correction"].strip()
    if isinstance(fb.get("notes"), str):
        return fb["notes"].strip()
    return ""


def _labels_from_feedback(fb: Dict[str, Any]) -> List[str]:
    if not fb:
        return []
    labels = fb.get("labels") or []
    return [str(x) for x in labels if isinstance(x, (str, int))]


def _deidentify(pair: TrainingPair) -> TrainingPair:
    """
    Basic de-identification:
      - drop patient_id / encounter_id from inputs
      - keep vitals and hpi_summary
    Expand this as needed for your compliance profile.
    """
    _in = dict(pair.input or {})
    # defensive: ensure we only keep allowed keys
    keep = {}
    if isinstance(_in.get("vitals"), dict):
        keep["vitals"] = _in["vitals"]
    if isinstance(_in.get("hpi_summary"), str):
        keep["hpi_summary"] = _in["hpi_summary"]

    return TrainingPair(
        trace_id=pair.trace_id,
        input=keep,
        labels=pair.labels,
        correction=pair.correction,
        annotator=pair.annotator,
        adapter_hint=pair.adapter_hint,
    )


def extract_training_pairs(ledger, since_index: int = 0, only_status: Optional[str] = "approved") -> List[TrainingPair]:
    """
    Collect pairs from the ledger:
      - Start with IntakeDrafted blocks
      - Use their mutable feedback tail to find labels/corrections
      - Optionally filter to feedback.status == only_status (default "approved")

    Returns a list of TrainingPair.
    """
    pairs: List[TrainingPair] = []
    for b in ledger.iter_blocks():
        if b.index < since_index:
            continue
        if not _is_intake_block(b):
            continue

        fb = b.feedback or {}
        if only_status is not None:
            if fb.get("status") != only_status:
                continue

        labels = _labels_from_feedback(fb)
        corr = _correction_from_feedback(fb)
        if not labels and not corr:
            # nothing to learn from yet
            continue

        data = b.data or {}
        pair = TrainingPair(
            trace_id=str(data.get("trace_id", "")),
            input={
                "vitals": data.get("vitals", {}),
                "hpi_summary": data.get("hpi_summary", ""),
                # raw identifiers are deliberately not included in inputs
                # "patient_id": data.get("patient_id"),
                # "encounter_id": data.get("encounter_id"),
            },
            labels=labels,
            correction=corr,
            annotator=(b.feedback or {}).get("annotator"),
            adapter_hint=(data.get("model") or {}).get("adapter_id"),
        )

        pairs.append(_deidentify(pair))

    return pairs


def write_jsonl(dataset_path: str | Path, pairs: List[TrainingPair]) -> str:
    """
    Persist training pairs to a JSONL file (one example per line).
    Returns the absolute path to the dataset.
    """
    p = Path(dataset_path).absolute()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for tp in pairs:
            f.write(json.dumps(asdict(tp), ensure_ascii=False) + "\n")
    return str(p)


def summarize_pairs(pairs: List[TrainingPair]) -> Dict[str, Any]:
    """
    Simple metrics to help policies decide:
      - n_pairs
      - labeled_count (has labels)
      - corrected_count (has correction)
    """
    n = len(pairs)
    labeled = sum(1 for x in pairs if x.labels)
    corrected = sum(1 for x in pairs if x.correction)
    return {"n_pairs": n, "labeled_count": labeled, "corrected_count": corrected}
