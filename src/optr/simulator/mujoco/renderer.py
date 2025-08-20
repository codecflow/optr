"""Frame rendering for MuJoCo simulation."""

import mujoco
import numpy as np

from .camera import resolve
from .simulation import Simulation


class Renderer:
    """Handles rendering frames from MuJoCo simulation with automatic caching."""

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
            config: Rendering configuration
        """
        self.simulation = simulation
        self.width = width
        self.height = height
        self.model = self.simulation.state.model

        self.renderer = mujoco.Renderer(self.model, height, width)

        self.camera = resolve(self.model, camera)

        self.cache: dict[int | None, dict[int, np.ndarray]] = {}

    def render(self, camera: int | None = None) -> np.ndarray:
        """Render current simulation state to RGB array with automatic caching.

        Args:
            camera: Optional camera to render from

        Returns:
            RGB array of shape (height, width, 3)
        """

        data = self.simulation.state.data
        camera = resolve(self.model, camera) or self.camera

        # Ensure camera is not None - default to -1 (free camera)
        if camera is None:
            camera = -1

        cache = self.cache.get(camera, {})
        time = self.simulation.state.data.time

        if time not in cache:
            self.renderer.update_scene(data, camera=camera)
            frame = self.renderer.render()
            cache[time] = frame
            self.cache[camera] = cache

        return cache[time]

    def close(self) -> None:
        """Clean up renderer resources."""
        self.renderer = None
        self.cache = None
