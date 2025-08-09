from abc import ABC, abstractmethod

import mujoco


class Output(ABC):
    """Base class for all outputs."""

    @abstractmethod
    def process(self, model: mujoco.MjModel, data: mujoco.MjData) -> None:
        """Process simulation state."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Clean up resources."""
        pass
