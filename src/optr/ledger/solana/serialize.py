"""
Serialization and compression utilities for on-chain storage
"""

import hashlib
import json
from typing import Any

import msgpack

from ...operator.types import Action


def compress_action(action: Action | dict[str, Any]) -> bytes:
    """
    Compress action for efficient storage

    Args:
        action: Action instance or dict

    Returns:
        Compressed bytes

    Example:
        compressed = compress_action(action)
        # Store compressed data on-chain
    """
    if isinstance(action, Action):
        data = {"type": action.type, "params": action.params}
    else:
        data = action

    return msgpack.packb(data, use_bin_type=True)


def decompress_action(data: bytes) -> dict[str, Any]:
    """
    Decompress action data

    Args:
        data: Compressed bytes

    Returns:
        Action dictionary

    Example:
        action_dict = decompress_action(compressed_data)
        action = Action(**action_dict)
    """
    return msgpack.unpackb(data, raw=False)


def hash_action(action: Action | dict[str, Any]) -> str:
    """
    Create hash of action for verification

    Args:
        action: Action to hash

    Returns:
        Hex string hash

    Example:
        action_hash = hash_action(action)
        # Store hash on-chain for verification
    """
    if isinstance(action, Action):
        data = {"type": action.type, "params": action.params}
    else:
        data = action

    # Ensure consistent ordering
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


def merkle_root(actions: list[Action | dict[str, Any]]) -> str:
    """
    Calculate merkle root of action list

    Args:
        actions: List of actions

    Returns:
        Merkle root hash

    Example:
        root = merkle_root(episode.actions)
        # Store root on-chain for batch verification
    """
    if not actions:
        return hashlib.sha256(b"").hexdigest()

    # Get leaf hashes
    hashes = [hash_action(action) for action in actions]

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


def compress_state(state: dict[str, Any], include_visual: bool = False) -> bytes:
    """
    Compress state for storage

    Args:
        state: State dictionary
        include_visual: Whether to include visual data

    Returns:
        Compressed bytes

    Example:
        compressed = compress_state(state_dict)
        # Store compressed state reference
    """
    data = {
        "timestamp": state.get("timestamp"),
        "metadata": state.get("metadata", {}),
    }

    if include_visual and "visual" in state:
        # Visual data is typically too large for on-chain
        # Store hash reference instead
        visual_hash = hashlib.sha256(state["visual"]).hexdigest()
        data["visual_hash"] = visual_hash

    return msgpack.packb(data, use_bin_type=True)


def create_action_proof(
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
        proof = create_action_proof(action, state1, state2)
        # Store proof on-chain for verification
    """
    return {
        "action_hash": hash_action(action),
        "state_before_hash": hashlib.sha256(
            json.dumps(state_before, sort_keys=True).encode()
        ).hexdigest(),
        "state_after_hash": hashlib.sha256(
            json.dumps(state_after, sort_keys=True).encode()
        ).hexdigest(),
        "combined_hash": hashlib.sha256(
            (
                hash_action(action)
                + hashlib.sha256(
                    json.dumps(state_before, sort_keys=True).encode()
                ).hexdigest()
                + hashlib.sha256(
                    json.dumps(state_after, sort_keys=True).encode()
                ).hexdigest()
            ).encode()
        ).hexdigest(),
    }


def estimate_storage_size(actions: list[dict[str, Any]]) -> int:
    """
    Estimate on-chain storage size

    Args:
        actions: List of actions

    Returns:
        Estimated bytes

    Example:
        size = estimate_storage_size(batch)
        cost = estimate_cost(size)
    """
    compressed = msgpack.packb(actions, use_bin_type=True)
    return len(compressed)
