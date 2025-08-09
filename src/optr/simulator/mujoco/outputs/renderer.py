"""Frame rendering for MuJoCo simulation."""

from dataclasses import dataclass

import numpy as np

import mujoco


@dataclass
class RendererConfig:
    """Video rendering configuration."""

    width: int = 1920
    height: int = 1080
    fps: int = 30


class Renderer:
    """Handles rendering frames from MuJoCo simulation with automatic caching."""

    def __init__(
        self, model: mujoco.MjModel, data: mujoco.MjData, config: RendererConfig
    ):
        """Initialize renderer with model and configuration."""
        self.model = model
        self.data = data
        self.config = config

        self._renderer = mujoco.Renderer(model, config.height, config.width)

        self._camera_id = None

        self._cached_frame = None
        self._cache_time = -1

        self._setup_camera()

    @property
    def width(self) -> int:
        """Get frame width."""
        return self.config.width

    @property
    def height(self) -> int:
        """Get frame height."""
        return self.config.height

    def render(self, camera_id: int | None = None) -> np.ndarray:
        """Render current simulation state to RGB array with automatic caching.

        Args:
            camera_id: Optional camera ID to render from

        Returns:
            RGB array of shape (height, width, 3)
        """

        current_time = self.data.time
        if self._cache_time != current_time or self._cached_frame is None:
            cam_id = (
                camera_id
                if camera_id is not None
                else (self._camera_id if self._camera_id is not None else -1)
            )

            self._renderer.update_scene(self.data, camera=cam_id)
            self._cached_frame = self._renderer.render()
            self._cache_time = current_time

        return self._cached_frame

    def _setup_camera(self) -> None:
        """Discover and setup the best available camera."""

        track_cam_id = None
        available_cameras = []

        for i in range(self.model.ncam):
            cam_name = self.model.cam(i).name
            available_cameras.append(f"{i}: {cam_name}")
            if cam_name == "track":
                track_cam_id = i

        if available_cameras:
            print(f"Available cameras: {', '.join(available_cameras)}")

        if track_cam_id is not None:
            self.set_camera(track_cam_id)
            print("Using 'track' camera (follows robot)")
        else:
            print("Warning: 'track' camera not found, using default free camera")

    def set_camera(self, camera_id: int | None) -> None:
        """Set default camera for rendering."""
        self._camera_id = camera_id

    def close(self) -> None:
        """Clean up renderer resources."""

        pass
