"""
Operator-specific type definitions
"""

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class State:
    """System state snapshot"""

    timestamp: float
    visual: bytes | None = None
    elements: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None

    @classmethod
    def create(cls, visual: bytes | None = None, **kwargs) -> "State":
        """Create state with current timestamp"""
        return cls(timestamp=time.time(), visual=visual, metadata=kwargs)


@dataclass
class Result:
    """Action execution result"""

    success: bool
    data: Any = None
    error: str | None = None
    duration: float = 0.0

    @classmethod
    def success_result(cls, data: Any = None, duration: float = 0.0) -> "Result":
        """Create successful result"""
        return cls(success=True, data=data, duration=duration)

    @classmethod
    def error_result(cls, error: str, duration: float = 0.0) -> "Result":
        """Create error result"""
        return cls(success=False, error=error, duration=duration)
