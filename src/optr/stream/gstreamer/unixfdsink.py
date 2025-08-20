"""GStreamer-compatible buffer implementation using unixfdsink."""

from gi.repository import Gst
from .sink import Sink
from .utils import delete_socket


class UnixFDSink(Sink):
    """Buffer that uses GStreamer's unixfdsink to publish frames over a Unix socket."""

    def __init__(
        self,
        socket_path: str,
        width: int,
        height: int,
        fps: float = 30.0,
        format: str = "RGB",
    ):
        """Initialize UnixFD sink.
        
        Args:
            socket_path: Path to the Unix socket
            width: Frame width in pixels
            height: Frame height in pixels
            fps: Frames per second
            format: Pixel format (RGB, RGBA, I420, NV12)
        """
        # Check for unixfdsink availability (requires GStreamer >= 1.24)
        if not Gst.ElementFactory.find("unixfdsink"):
            raise RuntimeError(
                "GStreamer unixfd plugin not found. "
                "Ensure GStreamer >= 1.24 with 'unixfd' is installed. "
                "Consider using SHMSink as an alternative."
            )
        
        self.socket_path = socket_path
        
        # Clean up any existing socket
        delete_socket(socket_path)
        
        # Get format info for frame size calculation
        from .utils import get_format_info
        channels, _ = get_format_info(format)
        self.frame_size = width * height * channels
        
        # Initialize base class
        super().__init__(
            width=width,
            height=height,
            fps=fps,
            format=format,
            sink_type="unixfdsink",
            use_timestamps=False,  # UnixFD handles timing internally
        )
    
    def _create_sink_element(self):
        """Create the unixfdsink element."""
        unixfdsink = Gst.ElementFactory.make("unixfdsink", "sink")
        if not unixfdsink:
            raise RuntimeError("Failed to create unixfdsink element")
        
        # Configure unixfdsink
        unixfdsink.set_property("socket-path", self.socket_path)
        
        # Try to set memory pool size for better performance
        try:
            unixfdsink.set_property("min-memory-size", self.frame_size)
        except TypeError:
            # Property may not exist on older builds; safe to ignore
            pass
        
        return unixfdsink
    
    def _on_started(self):
        """Log socket path when started."""
        print(f"UnixFD socket: {self.socket_path}")
    
    def _cleanup(self):
        """Clean up socket file."""
        delete_socket(self.socket_path)
