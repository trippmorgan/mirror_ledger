# mirror_ledger/blockchain/utils.py

import hashlib
import json
from datetime import datetime

"""
This utility module provides foundational, stateless functions required by the blockchain components.
Its primary responsibilities are deterministic data serialization and cryptographic hashing, which are
the cornerstones of creating a tamper-proof, verifiable ledger.

From a research perspective, the integrity of the audit trail is paramount. Any non-determinism in the
hashing process would invalidate the chain's verifiability. Therefore, this module ensures that
the same block data will *always* produce the same hash.
"""

def serialize_block_data(data: dict) -> str:
    """
    Serializes a dictionary into a deterministic JSON string.

    The key to ensuring a consistent hash is to have a consistent input string. By sorting the keys
    of the dictionary before serialization, we guarantee that the JSON string output is identical
    for the same data, regardless of the initial in-memory ordering of the keys. This is a critical
    step for cryptographic verification of the chain.

    Args:
        data: The dictionary containing the block's immutable data.

    Returns:
        A sorted, compact JSON string representation of the data.
    """
    return json.dumps(data, sort_keys=True, separators=(',', ':'))

def calculate_sha256_hash(*args) -> str:
    """
    Calculates a SHA-256 hash from a series of string arguments.

    This function concatenates all provided arguments into a single string and computes its SHA-256 hash.
    SHA-256 is selected for its widespread adoption, strong collision resistance, and sufficient security
    for this application's purpose of data integrity verification.

    Args:
        *args: A variable number of string arguments to be included in the hash.

    Returns:
        The hexadecimal representation of the SHA-256 hash.
    """
    hashing_text = "".join(map(str, args))
    return hashlib.sha256(hashing_text.encode('utf-8')).hexdigest()

def get_utc_timestamp() -> str:
    """
    Returns the current time as an ISO 8601 formatted string in UTC.

    Using UTC (Coordinated Universal Time) is a best practice for server applications and distributed
    systems, as it provides a universal time standard, free from the ambiguities of time zones and
    daylight saving time.

    Returns:
        The current UTC timestamp in ISO 8601 format.
    """
    return datetime.utcnow().isoformat()