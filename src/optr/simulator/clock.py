"""Timing utilities for simulation runners."""

import time


class Clock:
    """Manages simulation timing and FPS control."""

    def __init__(self, /, fps: int | None = 30, realtime: bool = True):
        """Initialize clock with FPS and realtime settings.

        Args:
            fps: Target frames per second (None for no limit)
            realtime: Whether to sync with wall clock time
        """
        if fps is not None and fps <= 0:
            raise ValueError("FPS must be positive")
        
        self.fps = fps
        self.realtime = realtime
        self.duration = 1.0 / fps if fps else 0
        self.start = 0.0

    def tick(self):
        """Mark the start of a frame."""
        if self.realtime:
            self.start = time.time()

    def sync(self):
        """Sleep to maintain target FPS if needed."""
        if self.realtime and self.fps:
            elapsed = time.time() - self.start
            sleep = self.duration - elapsed
            if sleep > 0:
                time.sleep(sleep)


class Null:
    """No-op clock for maximum speed computation."""

    def tick(self):
        """No-op tick."""
        pass

    def sync(self):
        """No-op sync."""
        pass
