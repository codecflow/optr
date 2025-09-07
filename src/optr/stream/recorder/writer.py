"""Video writers for the recorder."""

from pathlib import Path
from typing import Protocol

import imageio
import numpy as np

from optr.core.io import protocols


class Writer[T](protocols.Writer[T], protocols.Closer, Protocol):
    """Writer protocol for writing frames of type T."""

    def write(self, frame: T) -> None:
        """Write a frame."""
        ...


class MP4Writer(Writer[np.ndarray]):
    """MP4 video writer using imageio."""

    def __init__(
        self,
        path: Path,
        width: int,
        height: int,
        fps: float = 30.0,
        codec: str = "libx264",
        quality: int = 8,
    ):
        self.path = path
        self.width = width
        self.height = height
        self._closed = False

        self.writer = imageio.get_writer(
            str(path),
            fps=fps,
            codec=codec,
            quality=quality,
            pixelformat="yuv420p",
            macro_block_size=1,
        )

    def write(self, frame: np.ndarray) -> None:
        """Write frame to video."""
        if not self._closed and self.writer:
            self.writer.append_data(frame)

    def close(self) -> None:
        """Close and finalize video file."""
        if not self._closed and self.writer:
            self.writer.close()
            self._closed = True
