"""Frame rendering for MuJoCo simulation."""

import mujoco
import numpy as np

from .camera import resolve


class Renderer:
    """Minimal MuJoCo renderer - renders any data you provide."""

    def __init__(
        self,
        model: mujoco.MjModel,
        /,
        width: int = 1920,
        height: int = 1080,
        camera: int | str | None = None,
    ):
        """Initialize renderer with model and configuration.

        Args:
            model: MuJoCo model
            width: Render width in pixels
            height: Render height in pixels
            camera: Default camera to render from
        """
        self.model = model
        self.width = width
        self.height = height

        self.renderer = mujoco.Renderer(self.model, height, width)
        resolved = resolve(self.model, camera)
        self.camera = -1 if resolved is None else resolved

        self.buffer = np.empty((height, width, 3), dtype=np.uint8)

    def render(
        self, data: mujoco.MjData, camera: int | str | None = None
    ) -> np.ndarray:
        """Render the provided data to RGB array.

        Returns a reference to internal buffer. The contents will be
        overwritten on next render call. Copy if you need to preserve.

        Args:
            data: MuJoCo data to render
            camera: Optional camera to render from

        Returns:
            RGB array of shape (height, width, 3) - reference to internal buffer
        """
        if camera is None:
            cam = self.camera
        else:
            resolved = resolve(self.model, camera)
            cam = -1 if resolved is None else resolved

        self.renderer.update_scene(data, camera=cam)
        return self.renderer.render(out=self.buffer)

    def close(self) -> None:
        """Clean up renderer resources."""
        if self.renderer:
            self.renderer.close()
        self.renderer = None
        self.buffer = None  # type: ignore

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
