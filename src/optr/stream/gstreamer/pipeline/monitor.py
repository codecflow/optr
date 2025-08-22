"""Pipeline debugging, monitoring, and utility functions."""

import time
from typing import Any, Dict
from gi.repository import Gst, GLib
from contextlib import contextmanager


def state_name(pipeline: Gst.Pipeline) -> str:
    """Get human-readable pipeline state name."""
    try:
        ret, current, pending = pipeline.get_state(0)
        if ret == Gst.StateChangeReturn.SUCCESS:
            return current.value_nick
        elif ret == Gst.StateChangeReturn.ASYNC:
            return f"{current.value_nick} -> {pending.value_nick}"
        else:
            return f"UNKNOWN ({ret.value_nick})"
    except Exception:
        return "ERROR"
    
class Monitor:
    """Monitor pipeline performance and state."""

    def __init__(self, pipeline: Gst.Pipeline):
        self.pipeline = pipeline
        self.start_time = None
        self.frame_count = 0
        self.last_fps_time = None
        self.fps_history: list[float] = []
        self.error_count = 0
        self.warnings: list[str] = []

    def start(self):
        """Start monitoring."""
        self.start_time = time.time()
        self.last_fps_time = self.start_time
        self.frame_count = 0
        self.error_count = 0
        self.warnings.clear()

    def frame_processed(self):
        """Call when a frame is processed."""
        self.frame_count += 1
        current_time = time.time()

        # Calculate FPS every second
        if current_time - self.last_fps_time >= 1.0:
            fps = self.frame_count / (current_time - self.last_fps_time)
            self.fps_history.append(fps)
            self.last_fps_time = current_time
            self.frame_count = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get current monitoring statistics."""
        current_time = time.time()
        runtime = current_time - self.start_time if self.start_time else 0

        return {
            "runtime_seconds": runtime,
            "current_fps": self.fps_history[-1] if self.fps_history else 0,
            "average_fps": (
                sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
            ),
            "max_fps": max(self.fps_history) if self.fps_history else 0,
            "min_fps": min(self.fps_history) if self.fps_history else 0,
            "error_count": self.error_count,
            "warning_count": len(self.warnings),
            "pipeline_state": state_name(self.pipeline),
        }


@contextmanager
def profiler(pipeline: Gst.Pipeline):
    """Context manager for profiling pipeline performance."""
    monitor = Monitor(pipeline)

    # Set up bus monitoring
    bus = pipeline.get_bus()
    bus.add_signal_watch()

    def on_message(bus, message):
        if message.type == Gst.MessageType.ERROR:
            monitor.error_count += 1
        elif message.type == Gst.MessageType.WARNING:
            monitor.warnings.append(message.parse_warning()[0].message)

    handler_id = bus.connect("message", on_message)

    try:
        monitor.start()
        yield monitor
    finally:
        bus.disconnect(handler_id)
        bus.remove_signal_watch()
