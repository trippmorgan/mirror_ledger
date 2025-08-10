# mirror_ledger/blockchain/block.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any
from .utils import sha256_hex, deterministic_dumps, utc_iso


@dataclass
class Block:
    """
    A blockchain block designed for event-sourcing and clear separation between an
    immutable core and a mutable feedback tail. This structure is central to the
    Mirror Ledger's ability to be both auditable and adaptive.

    - IMMUTABLE CORE (covered by the hash):
        index, timestamp, previous_hash, data.
        The `data` field contains the event payload, including the crucial `type` and
        `trace_id` fields, which make the ledger a queryable event store.

    - MUTABLE TAIL (NOT covered by the hash):
        feedback.
        This allows for post-facto annotations like human reviews, corrections,
        or appeal statuses without invalidating the historical hash chain.

    The block's hash is computed deterministically from its immutable core, ensuring
    tamper-evidence for the recorded event.
    """
    index: int
    previous_hash: str
    data: Dict[str, Any]

    # Timestamp can be provided for back-dating or testing; otherwise, it's set at creation.
    timestamp: str = field(default_factory=utc_iso)

    # The feedback dictionary is the "mutable tail," explicitly excluded from the hash.
    feedback: Dict[str, Any] = field(default_factory=dict)

    # The hash is computed from the immutable core after initialization.
    hash: str = field(init=False)

    def __post_init__(self) -> None:
        """
        Called by the dataclass constructor after all fields are initialized.
        This is the ideal place to compute and set the block's definitive hash.
        """
        self.hash = self.compute_hash()

    def core_dict(self) -> Dict[str, Any]:
        """
        Returns a dictionary containing only the fields covered by the block hash.
        This method serves as the single source of truth for what constitutes the
        immutable, tamper-evident part of the block.
        """
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "data": self.data,
        }

    def compute_hash(self) -> str:
        """
        Computes the block's SHA-256 hash from its immutable core dictionary.
        Uses a deterministic JSON dump to ensure consistent output.
        """
        core_json = deterministic_dumps(self.core_dict())
        return sha256_hex(core_json)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the entire block, including the computed hash and the mutable
        feedback tail, into a dictionary suitable for storage or API responses.
        """
        return {
            **self.core_dict(),
            "hash": self.hash,
            "feedback": self.feedback,
        }

    def assert_hash_consistent(self) -> None:
        """
        Verifies that the block's stored hash matches a fresh computation of its
        core data. This is a critical safety check used during chain validation.
        Raises a ValueError if the hash is inconsistent, indicating tampering.
        """
        computed_hash = self.compute_hash()
        if self.hash != computed_hash:
            raise ValueError(
                f"Block {self.index}: Stored hash '{self.hash}' does not match "
                f"computed hash '{computed_hash}' of the core data."
            )

    def clone_with_feedback(self, feedback_delta: Dict[str, Any]) -> Block:
        """
        Creates a new, identical Block instance with updated feedback.

        This pure functional approach is safer than in-place mutation. The ledger
        can replace the old block instance with this new one. Because the immutable
        core is identical, the original hash is preserved.

        Args:
            feedback_delta: A dictionary of new feedback to merge into the existing feedback.

        Returns:
            A new Block instance with the updated feedback.
        """
        # Perform a deep merge of the feedback dictionaries
        new_feedback = dict(self.feedback or {})
        new_feedback.update(feedback_delta or {})

        # Create a new block with the same core data but new feedback
        new_block = Block(
            index=self.index,
            previous_hash=self.previous_hash,
            data=self.data,
            timestamp=self.timestamp,
            feedback=new_feedback,
        )
        # Manually set the hash to the original, as the core is unchanged.
        new_block.hash = self.hash
        return new_block