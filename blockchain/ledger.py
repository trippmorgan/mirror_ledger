# mirror_ledger/blockchain/ledger.py

import json
from typing import List, Dict, Any, Optional, Tuple
from copy import deepcopy

from .block import Block
from . import utils

"""
This module implements the `BlockchainLedger`, the high-level manager for the chain.
It acts as the primary interface for all other system components that need to read from or
write to the ledger. Its methods are designed as "smart contracts"—controlled functions that
ensure the chain's rules of integrity and evolution are respected.

This class encapsulates the list of blocks and is responsible for foundational tasks such as
creating the first block (the "Genesis Block") and adding subsequent blocks correctly.
"""

class BlockchainLedger:
    """
    Manages the collection of blocks, ensuring integrity and providing methods for
    interaction and data retrieval. It serves as the single source of truth for the
    AI's entire history.
    """
    def __init__(self):
        """
        Initializes the BlockchainLedger, creating the Genesis Block which serves as
        the anchor and moral foundation of the entire chain.
        """
        self.chain: List[Block] = [self._create_genesis_block()]

    def _create_genesis_block(self) -> Block:
        """
        Creates the very first block in the chain (Block 0).

        The Genesis Block is a conceptual anchor. Its data field contains the foundational
        mission or constitution of the AI system, making the system's core purpose
        an explicit and auditable part of its history from the very beginning.

        Returns:
            The initialized Genesis Block.
        """
        genesis_data = {
            "type": "Genesis Block",
            "purpose": "Moral Foundation & Learning Ledger for the Mirror Ledger System.",
            "directive": "Log all AI generation events, moral reflections, and human feedback "
                         "to create a transparent, auditable, and adaptive learning history."
        }
        return Block(
            index=0,
            previous_hash="0",
            timestamp=utils.get_utc_timestamp(),
            data=genesis_data
        )

    @property
    def latest_block(self) -> Block:
        """Returns the most recent block in the chain."""
        return self.chain[-1]

    def add_block(self, data: Dict[str, Any]) -> Block:
        """
        Mines a new block and adds it to the chain. This method is used for logging
        new, immutable generation events.

        Args:
            data: A dictionary containing the immutable data of the generation event
                  (e.g., prompt, output, moral_judgment).

        Returns:
            The newly created and added block.
        """
        latest = self.latest_block
        new_block = Block(
            index=latest.index + 1,
            previous_hash=latest.hash,
            data=data,
            # Initialize with default pending feedback
            feedback={"status": "pending", "rating": 0, "corrected_completion": None}
        )
        self.chain.append(new_block)
        return new_block
        
    def add_adaptation_event(self, adapter_path: str, used_block_indices: List[int], metrics: dict) -> Block:
        """
        Adds a special block to the ledger to record a model adaptation event.
        This provides a transparent audit trail of *how* and *why* the model evolved.

        Args:
            adapter_path: The file path to the newly trained LoRA adapter.
            used_block_indices: A list of block indices whose feedback was used for training.
            metrics: A dictionary of training metrics (e.g., loss, accuracy).

        Returns:
            The newly created adaptation event block.
        """
        adaptation_data = {
            "type": "Adaptation Event",
            "adapter_path": adapter_path,
            "source_block_indices": used_block_indices,
            "training_metrics": metrics
        }
        return self.add_block(adaptation_data)

    def add_feedback(self, block_index: int, status: str, rating: int, corrected_completion: Optional[str]) -> bool:
        """
        Adds feedback to an existing block. This function acts as a "smart contract" by
        only modifying the `feedback` field, which is explicitly not part of the hash.
        This allows for post-facto annotation without compromising the chain's integrity.

        Args:
            block_index: The index of the block to update.
            status: The new status (e.g., "good", "bad").
            rating: The numerical rating (e.g., +1, -1).
            corrected_completion: The user-provided correction, if any.

        Returns:
            True if the feedback was added successfully, False otherwise.
        """
        if 0 < block_index < len(self.chain):
            self.chain[block_index].feedback["status"] = status
            self.chain[block_index].feedback["rating"] = rating
            if corrected_completion:
                self.chain[block_index].feedback["corrected_completion"] = corrected_completion
            return True
        return False

    def find_good_examples(self, n: int = 2) -> List[Tuple[str, str]]:
        """
        Searches the chain for the most recent high-quality examples to be used for
        few-shot prompting. This is a key part of the learning loop.

        Args:
            n: The maximum number of examples to return.

        Returns:
            A list of (prompt, response) tuples from blocks marked as "good".
        """
        good_examples = []
        # Iterate backwards for recency
        for block in reversed(self.chain):
            if len(good_examples) >= n:
                break
            # Check for the explicit 'good' status from user feedback
            if block.feedback.get("status") == "good":
                prompt = block.data.get("prompt")
                response = block.data.get("output_text")
                if prompt and response:
                    good_examples.append((prompt, response))
        return good_examples

    def to_json(self, indent: int = 4) -> str:
        """
        Serializes the entire blockchain to a JSON string.
        
        Note: We use deepcopy to avoid modifying the original chain if any
        serialization logic were to alter the dicts.

        Args:
            indent: The indentation level for pretty-printing the JSON.

        Returns:
            A JSON string representing the entire chain.
        """
        return json.dumps([deepcopy(block.to_dict()) for block in self.chain], indent=indent)

    def print_chain(self):
        """A utility function to print the entire chain to the console."""
        print(self.to_json())