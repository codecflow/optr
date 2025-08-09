"""Base controller interfaces and protocols."""

from typing import Protocol

import mujoco


class Controller(Protocol):
    """Protocol for robot controllers."""

    def get_control(self, model: mujoco.MjModel, data: mujoco.MjData) -> None:
        """Compute and apply control signal to the robot."""
        ...

    def reset(self) -> None:
        """Reset controller state."""
        ...

    def get_status(self) -> dict:
        """Get controller status for logging/monitoring.

        Returns:
            dict: Status information including movement state, velocity, etc.
        """
        ...
