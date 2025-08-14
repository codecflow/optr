"""
Action batching utilities for efficient on-chain recording
"""

import time
from dataclasses import dataclass
from typing import Any

import msgpack


@dataclass
class BatchConfig:
    """Configuration for action batching"""

    max_size: int = 20  # Max actions per batch
    max_bytes: int = 1000  # Max bytes per batch
    timeout: float = 5.0  # Flush after N seconds
    compression: str = "msgpack"  # Compression method


class ActionBatch:
    """
    Simple action batcher for efficient on-chain storage

    Example:
        batch = ActionBatch(max_size=10, timeout=5.0)

        # Add actions
        batch.add({"type": "click", "x": 100, "y": 200})
        batch.add({"type": "type", "text": "hello"})

        # Check if should flush
        if batch.should_flush():
            actions = batch.flush()
            # Send to chain...
    """

    def __init__(
        self,
        max_size: int = 20,
        max_bytes: int = 1000,
        timeout: float = 5.0,
        compression: str = "msgpack",
    ):
        """
        Initialize batch with config

        Args:
            max_size: Max actions per batch
            max_bytes: Max bytes per batch
            timeout: Flush after N seconds
            compression: Compression method (msgpack, json, none)
        """
        self.config = BatchConfig(
            max_size=max_size,
            max_bytes=max_bytes,
            timeout=timeout,
            compression=compression,
        )
        self.actions: list[dict[str, Any]] = []
        self.start_time: float | None = None
        self.total_bytes: int = 0

    def add(self, action: dict[str, Any]) -> None:
        """
        Add action to batch

        Args:
            action: Action dictionary to add
        """
        if not self.start_time:
            self.start_time = time.time()

        # Estimate size
        action_bytes = len(msgpack.packb(action))

        # Check if adding would exceed limits
        if self.actions and (self.total_bytes + action_bytes > self.config.max_bytes):
            # Don't add, let caller flush first
            return

        self.actions.append(action)
        self.total_bytes += action_bytes

    def should_flush(self) -> bool:
        """
        Check if batch should be flushed

        Returns:
            True if batch should be flushed
        """
        if not self.actions:
            return False

        # Size limit
        if len(self.actions) >= self.config.max_size:
            return True

        # Byte limit
        if self.total_bytes >= self.config.max_bytes:
            return True

        # Time limit
        if self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed >= self.config.timeout:
                return True

        return False

    def flush(self) -> list[dict[str, Any]]:
        """
        Flush and return all actions

        Returns:
            List of actions
        """
        actions = self.actions.copy()
        self.actions = []
        self.start_time = None
        self.total_bytes = 0
        return actions

    def compress(self) -> bytes:
        """
        Compress current batch

        Returns:
            Compressed bytes
        """
        if not self.actions:
            return b""

        if self.config.compression == "msgpack":
            return msgpack.packb(self.actions)
        elif self.config.compression == "json":
            import json

            return json.dumps(self.actions).encode()
        else:
            # No compression
            return str(self.actions).encode()

    def size(self) -> int:
        """Get current batch size"""
        return len(self.actions)

    def is_empty(self) -> bool:
        """Check if batch is empty"""
        return len(self.actions) == 0

    def clear(self) -> None:
        """Clear batch without returning actions"""
        self.actions = []
        self.start_time = None
        self.total_bytes = 0

    def get_stats(self) -> dict[str, Any]:
        """
        Get batch statistics

        Returns:
            Dict with batch stats
        """
        elapsed = 0.0
        if self.start_time:
            elapsed = time.time() - self.start_time

        return {
            "size": len(self.actions),
            "bytes": self.total_bytes,
            "elapsed": elapsed,
            "compression": self.config.compression,
        }


def create_batch_manager(configs: dict[str, BatchConfig]) -> dict[str, ActionBatch]:
    """
    Create multiple named batches

    Args:
        configs: Dict of name -> BatchConfig

    Returns:
        Dict of name -> ActionBatch

    Example:
        batches = create_batch_manager({
            "high_priority": BatchConfig(max_size=5, timeout=1.0),
            "low_priority": BatchConfig(max_size=50, timeout=30.0),
        })

        batches["high_priority"].add(critical_action)
        batches["low_priority"].add(normal_action)
    """
    return {name: ActionBatch(**config.__dict__) for name, config in configs.items()}
