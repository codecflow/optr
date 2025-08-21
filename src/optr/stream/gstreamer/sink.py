"""Base sink class for GStreamer streaming."""

import threading
from abc import ABC, abstractmethod

import numpy as np
from gi.repository import GLib, Gst

from optr.core.io import Closer, Writer


class Sink(Writer[np.ndarray], Closer, ABC):
    """Abstract base class for all GStreamer sinks with common functionality."""

    def __init__(
        self,
        width: int,
        height: int,
        fps: float = 30.0,
        format: str = "RGB",
        sink_type: str = "sink",
        use_timestamps: bool = True,
    ):
        """Initialize base GStreamer sink.

        Args:
            width: Frame width in pixels
            height: Frame height in pixels
            fps: Frames per second
            format: Pixel format (RGB, RGBA, I420, NV12)
            sink_type: Type of sink for logging
            use_timestamps: Whether to set timestamps on buffers
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.format = format
        self.sink_type = sink_type
        self.use_timestamps = use_timestamps

        # Get format info
        from .utils import get_format_info

        self.channels, self.gst_format = get_format_info(format)
        self.frame_size = width * height * self.channels

        # Timing properties
        self.frame_count = 0
        self.frame_duration = int(Gst.SECOND / fps)

        # Thread safety
        self._lock = threading.Lock()

        # GStreamer objects
        self.pipeline = None
        self.appsrc = None
        self.videoconvert = None
        self.mainloop = None
        self.thread = None
        self._running = False

        # Create pipeline
        self._create_pipeline()

    def _create_pipeline(self):
        """Create the GStreamer pipeline."""
        self.pipeline = Gst.Pipeline.new(f"{self.sink_type}-pipeline")

        # Create common elements
        self.appsrc = Gst.ElementFactory.make("appsrc", "source")
        self.videoconvert = Gst.ElementFactory.make("videoconvert", "convert")

        if not all([self.appsrc, self.videoconvert]):
            raise RuntimeError(
                "Failed to create GStreamer elements (appsrc/videoconvert)"
            )

        # Configure appsrc
        from .utils import create_caps_string

        caps = Gst.Caps.from_string(
            create_caps_string(self.width, self.height, self.fps, self.gst_format)
        )
        self.appsrc.set_property("caps", caps)
        self.appsrc.set_property("format", Gst.Format.TIME)
        self.appsrc.set_property("is-live", True)

        # Add to pipeline
        self.pipeline.add(self.appsrc)
        self.pipeline.add(self.videoconvert)

        # Link appsrc to videoconvert
        if not self.appsrc.link(self.videoconvert):
            raise RuntimeError("Failed to link appsrc to videoconvert")

        # Create and add sink element (implemented by subclass)
        sink = self._create_sink_element()
        if not sink:
            raise RuntimeError(f"Failed to create {self.sink_type} element")

        self.pipeline.add(sink)

        # Link videoconvert to sink
        if not self.videoconvert.link(sink):
            raise RuntimeError(f"Failed to link videoconvert to {self.sink_type}")

        # Set up bus for message handling
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_message)

    @abstractmethod
    def _create_sink_element(self):
        """Create the specific sink element. Must be implemented by subclasses."""
        pass

    def _on_message(self, bus, message):
        """Handle GStreamer bus messages."""
        if message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            element = message.src.get_name()
            print(f"GStreamer Error from {element}: {err}")
            print(f"Debug info: {debug}")
            self.stop()
        elif message.type == Gst.MessageType.EOS:
            print(f"GStreamer {self.sink_type} EOS received")
            self.stop()
        elif message.type == Gst.MessageType.WARNING:
            warn, debug = message.parse_warning()
            print(f"GStreamer Warning: {warn}")

    def start(self):
        """Start the GStreamer pipeline."""
        if self._running:
            return

        # Start pipeline
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            raise RuntimeError(f"Failed to start GStreamer {self.sink_type} pipeline")

        # Start GLib main loop in separate thread
        self.mainloop = GLib.MainLoop()
        self.thread = threading.Thread(target=self.mainloop.run, daemon=True)
        self.thread.start()

        # Send initial segment event for proper timing
        segment = Gst.Segment()
        segment.init(Gst.Format.TIME)
        segment.start = 0
        segment.stop = Gst.CLOCK_TIME_NONE
        segment.time = 0
        segment.position = 0
        segment.rate = 1.0

        segment_event = Gst.Event.new_segment(segment)
        self.appsrc.send_event(segment_event)

        self._running = True
        self._on_started()
        print(f"GStreamer {self.sink_type} started")

    def _on_started(self):
        """Hook called after pipeline starts. Override in subclasses if needed."""
        pass

    def write(self, frame: np.ndarray) -> None:
        """Write frame to GStreamer pipeline."""
        if not self._running:
            self.start()

        # Validate frame shape
        expected_shape = (self.height, self.width, self.channels)
        if frame.shape != expected_shape:
            raise ValueError(
                f"Frame shape {frame.shape} doesn't match expected {expected_shape}"
            )

        with self._lock:
            # Create GStreamer buffer from numpy array
            frame_bytes = frame.tobytes()
            gst_buffer = Gst.Buffer.new_allocate(None, len(frame_bytes), None)
            gst_buffer.fill(0, frame_bytes)

            # Set timestamps if needed
            if self.use_timestamps:
                timestamp = self.frame_count * self.frame_duration
                gst_buffer.pts = timestamp
                gst_buffer.dts = timestamp
                gst_buffer.duration = self.frame_duration

            # Push buffer to appsrc
            ret = self.appsrc.emit("push-buffer", gst_buffer)
            if ret != Gst.FlowReturn.OK:
                print(f"Failed to push buffer to {self.sink_type}: {ret}")

            self.frame_count += 1

    def stop(self):
        """Stop the GStreamer pipeline."""
        if not self._running:
            return

        self._running = False

        # Send EOS signal
        if self.appsrc:
            self.appsrc.emit("end-of-stream")

        # Stop pipeline
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)

        # Stop main loop
        if self.mainloop:
            self.mainloop.quit()

        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            if threading.current_thread() != self.thread:
                self.thread.join(timeout=1.0)

        print(f"GStreamer {self.sink_type} stopped")

    def close(self) -> None:
        """Close the sink and cleanup resources."""
        self.stop()
        self._cleanup()

    def _cleanup(self):
        """Additional cleanup. Override in subclasses if needed."""
        pass
