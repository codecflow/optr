"""Pipe output for raw video frames."""

import fcntl
import os
import stat
from dataclasses import dataclass

import numpy as np

import mujoco

from .base import Output
from .renderer import Renderer


@dataclass
class PipeConfig:
    """Pipe output configuration."""

    enabled: bool = False
    path: str = "/tmp/sim.pipe"
    create_pipe: bool = True


class PipeOutput(Output):
    """Output raw RGB frames to a named pipe."""

    def __init__(self, renderer: Renderer, config: PipeConfig):
        """Initialize pipe output.

        Args:
            renderer: Renderer instance for getting frames
            config: Pipe configuration
        """
        self.renderer = renderer
        self.config = config
        self._pipe_fd: int | None = None

        self._setup_pipe()

    def _setup_pipe(self) -> None:
        """Setup the named pipe."""
        path = self.config.path

        if self.config.create_pipe and not os.path.exists(path):
            pipe_dir = os.path.dirname(path)
            if pipe_dir and not os.path.exists(pipe_dir):
                os.makedirs(pipe_dir, exist_ok=True)

            os.mkfifo(path)
            print(f"Created named pipe: {path}")

        if os.path.exists(path):
            if not stat.S_ISFIFO(os.stat(path).st_mode):
                raise ValueError(f"{path} exists but is not a named pipe")
        else:
            raise FileNotFoundError(f"Named pipe {path} does not exist")

        print(f"Pipe output configured: {path}")
        print(
            f"  Frame format: RGB24 {self.renderer.config.width}x{self.renderer.config.height}"
        )
        print(f"  Frame size: {self._frame_size} bytes")

    @property
    def _frame_size(self) -> int:
        """Calculate frame size in bytes."""
        return self.renderer.config.width * self.renderer.config.height * 3

    def _open_pipe(self) -> None:
        """Open the pipe for writing."""
        if self._pipe_fd is None:
            try:
                self._pipe_fd = os.open(self.config.path, os.O_WRONLY | os.O_NONBLOCK)

                flags = fcntl.fcntl(self._pipe_fd, fcntl.F_GETFL)
                fcntl.fcntl(self._pipe_fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)
                print(f"Opened pipe for writing: {self.config.path}")
            except OSError as e:
                if e.errno == 6:
                    pass
                else:
                    print(f"Error opening pipe: {e}")
                    raise

    def process(self, model: mujoco.MjModel, data: mujoco.MjData) -> None:
        """Process simulation state and write frame to pipe."""

        if self._pipe_fd is None:
            try:
                self._open_pipe()
            except OSError:
                return

        frame = self.renderer.render()
        self._write_frame(frame)

    def _write_frame(self, frame: np.ndarray) -> None:
        """Write frame to pipe."""
        if self._pipe_fd is None:
            return

        try:
            frame_bytes = frame.tobytes()
            total_bytes = len(frame_bytes)
            bytes_written = 0

            while bytes_written < total_bytes:
                try:
                    chunk_written = os.write(self._pipe_fd, frame_bytes[bytes_written:])
                    if chunk_written == 0:
                        print("Warning: Pipe write returned 0 bytes")
                        break
                    bytes_written += chunk_written
                except OSError as e:
                    if e.errno == 11:
                        continue
                    else:
                        raise

            if bytes_written != total_bytes:
                print(
                    f"Warning: Only wrote {bytes_written}/{total_bytes} bytes to pipe"
                )

        except OSError as e:
            if e.errno == 32:
                print("Pipe reader disconnected, closing pipe")
                self._close_pipe()
            else:
                print(f"Error writing to pipe: {e}")
                self._close_pipe()
        except Exception as e:
            print(f"Unexpected error writing to pipe: {e}")
            self._close_pipe()

    def _close_pipe(self) -> None:
        """Close the pipe file descriptor."""
        if self._pipe_fd is not None:
            try:
                os.close(self._pipe_fd)
                print(f"Closed pipe: {self.config.path}")
            except OSError as e:
                print(f"Error closing pipe: {e}")
            finally:
                self._pipe_fd = None

    def close(self) -> None:
        """Clean up resources."""
        self._close_pipe()

        if self.config.create_pipe and os.path.exists(self.config.path):
            try:
                os.unlink(self.config.path)
                print(f"Removed pipe file: {self.config.path}")
            except OSError as e:
                print(f"Warning: Could not remove pipe file: {e}")
