# mirror_ledger/blockchain/block.py

from dataclasses import dataclass, field
from typing import Any, Dict, List
from . import utils

"""
This module defines the fundamental data structure of the Mirror Ledger: the `Block`.
A Block serves as a "data contract" for a single, discrete event in the AI's lifecycle.
It is meticulously designed to separate immutable, observed facts from mutable,
human-provided feedback, which is a core concept of this research.

The choice of a `dataclass` provides a modern, readable, and type-hinted structure.
"""

@dataclass
class Block:
    """
    Represents a single block in the Mirror Ledger. Each block is an immutable record of a
    generation event, coupled with a mutable field for subsequent feedback.

    Attributes:
        index (int): The position of the block in the chain.
        previous_hash (str): The hash of the preceding block, linking them cryptographically.
        timestamp (str): The UTC timestamp of the block's creation.

        data (Dict[str, Any]): The core, immutable data of the event. This dictionary contains
            the "observed facts" of the AI's action (e.g., the prompt, the output, the moral
            judgment). This data is included in the block's hash to make it tamper-proof.

        feedback (Dict[str, Any]): A container for mutable feedback data provided post-creation.
            This includes user ratings, corrected text, etc. This dictionary is *explicitly excluded*
            from the block's hash, allowing it to be updated by "smart contract" methods in the
            Ledger without invalidating the chain's integrity.

        hash (str): The cryptographic hash of the block, calculated on its immutable fields.
            It serves as the block's unique identifier and integrity verifier.
    """
    index: int
    previous_hash: str
    timestamp: str = field(default_factory=utils.get_utc_timestamp)
    
    # --- Core Immutable Data ---
    # This dictionary will be hashed.
    data: Dict[str, Any] = field(default_factory=dict)

    # --- Mutable Feedback Data ---
    # This dictionary is EXCLUDED from the hash.
    feedback: Dict[str, Any] = field(default_factory=dict)
    
    hash: str = field(init=False)

    def __post_init__(self):
        """
        This dataclass method is called automatically after the object is initialized.
        It's the perfect place to compute the hash, as it ensures all other fields
        have been populated.
        """
        self.hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """
        Calculates the SHA-256 hash of the block's immutable contents.

        The hash is derived from the block's index, timestamp, previous hash, and a
        deterministic serialization of its `data` dictionary. Crucially, the `feedback`
        dictionary is omitted. This design choice is fundamental to the Mirror Ledger:
        it allows feedback to be added later without breaking the cryptographic chain,
        embodying the principle of an auditable but updatable record.

        Returns:
            The calculated SHA-256 hash as a hex digest.
        """
        # Serialize the immutable `data` dictionary into a consistent string format.
        serialized_data = utils.serialize_block_data(self.data)

        return utils.calculate_sha256_hash(
            self.index,
            self.previous_hash,
            self.timestamp,
            serialized_data
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Returns a dictionary representation of the block, suitable for JSON serialization.
        """
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
            "data": self.data,
            "feedback": self.feedback
        }