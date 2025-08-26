"""Frame rendering for MuJoCo simulation."""

import mujoco
import numpy as np

from .camera import resolve
from .simulation import Simulation


class Renderer:
    """Handles rendering frames from MuJoCo simulation."""

    def __init__(
        self,
        simulation: Simulation,
        /,
        width: int = 1920,
        height: int = 1080,
        camera: int | str | None = None,
    ):
        """Initialize renderer with simulation and configuration.

        Args:
            simulation: MuJoCo simulation object
            width: Render width in pixels
            height: Render height in pixels
            camera: Default camera to render from
        """
        self.simulation = simulation
        self.width = width
        self.height = height
        self.model = self.simulation.state.model

        self.renderer = mujoco.Renderer(self.model, height, width)
        self.camera = resolve(self.model, camera) or -1

        self.buffer = np.empty((height, width, 3), dtype=np.uint8)

    def render(self, camera: int | None = None) -> np.ndarray:
        """Render current simulation state to RGB array.

        Returns a reference to internal buffer. The contents will be
        overwritten on next render call. Copy if you need to preserve.

        Args:
            camera: Optional camera to render from

        Returns:
            RGB array of shape (height, width, 3) - reference to internal buffer
        """
        data = self.simulation.state.data
        camera = self.camera if camera is None else resolve(self.model, camera)

        self.renderer.update_scene(data, camera=camera)

        return self.renderer.render(out=self.buffer)

    def close(self) -> None:
        """Clean up renderer resources."""
        self.renderer = None
        self.buffer = None
