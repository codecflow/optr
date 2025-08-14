"""
Solana-specific action utilities
Functional utilities for compressing, hashing, and verifying actions on-chain
"""

import hashlib
import json
from typing import Any

import msgpack

from ...operator.action import Action


def compress(action: Action | dict[str, Any]) -> bytes:
    """
    Compress action for on-chain storage

    Args:
        action: Action to compress

    Returns:
        Compressed bytes

    Example:
        from optr.operator.action import action
        from optr.ledger.solana.action import compress

        a = action('click', x=100, y=200)
        compressed = compress(a)
    """
    return msgpack.packb(action, use_bin_type=True)


def decompress(data: bytes) -> dict[str, Any]:
    """
    Decompress action data from chain

    Args:
        data: Compressed bytes

    Returns:
        Action dictionary

    Example:
        action = decompress(compressed_data)
    """
    return msgpack.unpackb(data, raw=False)


def hash(action: Action | dict[str, Any]) -> str:
    """
    Create hash of action for verification

    Args:
        action: Action to hash

    Returns:
        Hex string hash

    Example:
        from optr.operator.action import action
        from optr.ledger.solana.action import hash

        a = action('click', x=100, y=200)
        action_hash = hash(a)
    """
    json_str = json.dumps(action, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


def merkle_root(actions: list[Action | dict[str, Any]]) -> str:
    """
    Calculate merkle root for action batch

    Args:
        actions: List of actions

    Returns:
        Merkle root hash

    Example:
        from optr.operator.action import chain, action
        from optr.ledger.solana.action import merkle_root

        actions = chain(
            action('click', x=100, y=200),
            action('type', text='hello'),
            action('wait', duration=1.0)
        )
        root = merkle_root(actions)
    """
    if not actions:
        return hashlib.sha256(b"").hexdigest()

    # Get leaf hashes
    hashes = [hash(action) for action in actions]

    # Build merkle tree
    while len(hashes) > 1:
        # Pad with last hash if odd number
        if len(hashes) % 2 == 1:
            hashes.append(hashes[-1])

        # Combine pairs
        new_hashes = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i + 1]
            new_hash = hashlib.sha256(combined.encode()).hexdigest()
            new_hashes.append(new_hash)

        hashes = new_hashes

    return hashes[0]


def proof(
    action: Action | dict[str, Any],
    state_before: dict[str, Any],
    state_after: dict[str, Any],
) -> dict[str, str]:
    """
    Create cryptographic proof of action execution

    Args:
        action: Action that was executed
        state_before: State before action
        state_after: State after action

    Returns:
        Proof dictionary with hashes

    Example:
        from optr.operator.action import action
        from optr.ledger.solana.action import proof

        a = action('click', x=100, y=200)
        p = proof(a, state_before, state_after)
    """
    action_hash = hash(action)
    before_hash = hashlib.sha256(
        json.dumps(state_before, sort_keys=True).encode()
    ).hexdigest()
    after_hash = hashlib.sha256(
        json.dumps(state_after, sort_keys=True).encode()
    ).hexdigest()

    return {
        "action": action_hash,
        "before": before_hash,
        "after": after_hash,
        "combined": hashlib.sha256(
            (action_hash + before_hash + after_hash).encode()
        ).hexdigest(),
    }


def size(actions: list[dict[str, Any]]) -> int:
    """
    Estimate storage size for actions

    Args:
        actions: List of actions

    Returns:
        Size in bytes

    Example:
        from optr.operator.action import chain, action
        from optr.ledger.solana.action import size

        actions = chain(
            action('click', x=100, y=200),
            action('type', text='hello')
        )
        bytes_needed = size(actions)
    """
    compressed = msgpack.packb(actions, use_bin_type=True)
    return len(compressed)


def verify(action: Action | dict[str, Any], expected_hash: str) -> bool:
    """
    Verify action against expected hash

    Args:
        action: Action to verify
        expected_hash: Expected hash value

    Returns:
        True if hash matches

    Example:
        from optr.ledger.solana.action import hash, verify

        a = action('click', x=100, y=200)
        h = hash(a)

        # Later, verify
        is_valid = verify(a, h)
    """
    return hash(action) == expected_hash


def batch_compress(actions: list[Action | dict[str, Any]]) -> bytes:
    """
    Compress multiple actions as a batch

    Args:
        actions: List of actions

    Returns:
        Compressed batch

    Example:
        from optr.operator.action import chain, action
        from optr.ledger.solana.action import batch_compress

        actions = chain(
            action('click', x=100, y=200),
            action('type', text='hello')
        )
        compressed = batch_compress(actions)
    """
    return msgpack.packb(actions, use_bin_type=True)


def batch_decompress(data: bytes) -> list[dict[str, Any]]:
    """
    Decompress batch of actions

    Args:
        data: Compressed batch data

    Returns:
        List of actions

    Example:
        actions = batch_decompress(compressed_data)
    """
    return msgpack.unpackb(data, raw=False)
