"""Base simulation interfaces and protocols."""

from typing import Any, Protocol

import mujoco


class Simulation(Protocol):
    """Protocol for self-contained simulation definitions."""

    def setup(self) -> None:
        """Setup the simulation (load model, create controllers, etc.)."""
        ...

    def step(self, n_steps: int = 1) -> None:
        """Step the simulation forward."""
        ...

    def get_model(self) -> mujoco.MjModel:
        """Get the MuJoCo model."""
        ...

    def get_data(self) -> mujoco.MjData:
        """Get the MuJoCo data."""
        ...

    def cleanup(self) -> None:
        """Clean up simulation resources."""
        ...

    def get_status(self) -> dict[str, Any]:
        """Get simulation status for monitoring."""
        ...
