"""Core simulation protocol."""

from typing import Protocol, TypeVar

State = TypeVar("State")


class Simulation(Protocol[State]):
    """Base protocol for any simulator."""

    state: State

    def step(self) -> State:
        """Step simulation forward."""
        ...

    def reset(self) -> State:
        """Reset to initial state."""
        ...

    def close(self) -> None:
        """Clean up resources."""
        ...
