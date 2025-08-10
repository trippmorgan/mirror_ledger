# mirror_ledger/blockchain/ledger.py

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Iterable, Optional

from .block import Block
from .utils import utc_iso

"""
This module implements the BlockchainLedger, the primary controller for the chain.
It abstracts the complexities of block creation, validation, and persistence,
providing a clean, "smart contract"-style API for the rest of the system.

Design Choices:
  - Storage Model: Uses a simple JSON Lines (.jsonl) file. Each line is a complete,
    serialized block. This format is human-readable, easily auditable with standard
    command-line tools (like `grep` or `jq`), and robust against corruption (a single
    corrupt line doesn't invalidate the whole file).
  - Persistence Strategy: For simplicity and safety in this prototype stage, feedback
    updates trigger a full rewrite of the storage file (`_rewrite_file`). This is an atomic
    operation (writing to a temporary file then replacing the original) that prevents data
    loss if the process is interrupted. For high-throughput systems, this could be
    optimized or replaced with a transactional database (e.g., SQLite, Postgres)
    without changing the public API of this class.
  - In-Memory Cache: The entire chain is held in a list (`self._chain`) for fast,
    synchronous access and querying. The file on disk is the source of truth for
    durability.
"""

class BlockchainLedger:
    """
    Manages the collection of blocks, ensuring integrity and providing methods for
    interaction and data retrieval. It serves as the single source of truth for the
    AI's entire event history.
    """

    def __init__(self, storage_path: str = "data/blocks.jsonl", auto_bootstrap_genesis: bool = True) -> None:
        """
        Initializes the ledger. If a storage file exists, it loads the chain from disk.
        Otherwise, it creates the storage file and, if requested, a Genesis Block.
        """
        self.path = Path(storage_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._chain: List[Block] = []

        if self.path.exists():
            self._load_from_file()
        else:
            self.path.touch() # Create an empty file

        if auto_bootstrap_genesis and not self._chain:
            # The Genesis block's previous_hash is defined by convention as 64 zeros.
            self.add_block(
                data={"type": "Genesis", "message": "Mirror Ledger initialized."},
                is_genesis=True
            )

    # --- Public API: Write Operations ---

    def add_block(self, data: Dict[str, Any], feedback: Optional[Dict[str, Any]] = None, is_genesis: bool = False) -> Block:
        """
        Creates, validates, and appends a new block to the ledger. This is the primary
        method for recording a new, immutable event.

        Args:
            data: The core event payload (e.g., {"type": "IntakeDrafted", "trace_id": ..., "content": ...}).
            feedback: Optional initial feedback for the mutable tail.
            is_genesis: A flag to handle the special case of the first block.

        Returns:
            The newly created and persisted Block.
        """
        if is_genesis:
            index = 0
            previous_hash = "0" * 64
        else:
            if not self._chain:
                raise RuntimeError("Cannot add a non-genesis block to an empty chain.")
            latest_block = self._chain[-1]
            index = latest_block.index + 1
            previous_hash = latest_block.hash

        block = Block(
            index=index,
            previous_hash=previous_hash,
            data=data,
            feedback=feedback or {},
        )
        self._append_to_file(block)
        return block

    def append_feedback(self, index: int, feedback_delta: Dict[str, Any]) -> Block:
        """
        Merges feedback into the block at `index` without changing its hash. This is the
        core "smart contract" for adding human-in-the-loop annotations.

        Args:
            index: The index of the block to update.
            feedback_delta: A dictionary of new feedback to merge into the existing feedback.

        Returns:
            The updated block with the merged feedback.

        Raises:
            IndexError: If the block index is out of bounds.
        """
        if index < 0 or index >= len(self._chain):
            raise IndexError(f"Block index {index} out of range (0..{len(self._chain)-1})")

        original_block = self._chain[index]
        updated_block = original_block.clone_with_feedback(feedback_delta)

        # Atomically update the state
        self._chain[index] = updated_block
        self._rewrite_file()
        return updated_block

    # --- Public API: Read and Validate Operations ---

    @property
    def chain(self) -> List[Block]:
        """Provides read-only access to the in-memory chain."""
        return list(self._chain)

    def iter_blocks(self) -> Iterable[Block]:
        """Returns an iterator over the blocks in the chain."""
        return iter(self._chain)

    def find_by_trace_id(self, trace_id: str) -> List[Block]:
        """
        Efficiently finds all blocks related to a specific workflow or event trace.
        This is the primary method for auditing a single interaction's lifecycle.

        Args:
            trace_id: The unique identifier for the trace.

        Returns:
            A list of all blocks sharing the given trace_id.
        """
        # This list comprehension is efficient for in-memory searching.
        return [
            b for b in self._chain
            if isinstance(b.data, dict) and b.data.get("trace_id") == trace_id
        ]

    def validate_chain(self) -> bool:
        """
        Performs a full integrity check of the entire blockchain.

        It verifies two things for every block:
        1.  The block's stored hash is correct (`assert_hash_consistent`).
        2.  The block correctly points to the hash of the preceding block.

        Raises:
            ValueError: On the first detected inconsistency (hash mismatch or broken link).
        Returns:
            True if the entire chain is cryptographically valid.
        """
        if not self._chain:
            return True

        # 1. Validate Genesis Block
        genesis = self._chain[0]
        genesis.assert_hash_consistent()
        if genesis.index != 0 or genesis.previous_hash != "0" * 64:
            raise ValueError("Genesis block is malformed.")

        # 2. Validate all subsequent blocks and their links
        for i in range(1, len(self._chain)):
            prev_block = self._chain[i - 1]
            curr_block = self._chain[i]

            curr_block.assert_hash_consistent()

            if curr_block.previous_hash != prev_block.hash:
                raise ValueError(
                    f"Chain link broken at Block {curr_block.index}: "
                    f"previous_hash '{curr_block.previous_hash}' does not match "
                    f"prior block's hash '{prev_block.hash}'."
                )
        return True

    # --- Internal Methods: Persistence and Deserialization ---

    def _load_from_file(self) -> None:
        """Loads the chain from the .jsonl storage file into memory."""
        self._chain.clear()
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                self._chain.append(self._block_from_dict(obj))

    def _rewrite_file(self) -> None:
        """Atomically rewrites the entire storage file with the current in-memory chain state."""
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            for block in self._chain:
                f.write(json.dumps(block.to_dict()) + "\n")
        tmp_path.replace(self.path)

    def _append_to_file(self, block: Block) -> None:
        """Appends a single new block to the in-memory chain and the storage file."""
        self._chain.append(block)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(block.to_dict()) + "\n")

    @staticmethod
    def _block_from_dict(obj: Dict[str, Any]) -> Block:
        """
        Rehydrates a Block object from its dictionary representation (as stored on disk).
        It trusts the stored hash, which is later verified by `validate_chain`.
        """
        b = Block(
            index=int(obj["index"]),
            previous_hash=str(obj["previous_hash"]),
            data=obj.get("data", {}),
            timestamp=str(obj["timestamp"]),
            feedback=obj.get("feedback", {}),
        )
        # We must trust the stored hash during rehydration.
        # The `validate_chain` method is responsible for verifying it.
        b.hash = str(obj["hash"])
        return b