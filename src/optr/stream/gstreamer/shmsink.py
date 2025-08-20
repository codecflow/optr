"""GStreamer-compatible buffer implementation using shmsink."""

from gi.repository import Gst
from .sink import Sink
from .utils import delete_socket


class SHMSink(Sink):
    """Buffer that uses GStreamer's shmsink for shared memory."""

    def __init__(
        self,
        socket_path: str,
        width: int,
        height: int,
        fps: float = 30.0,
        format: str = "RGB",
        shm_size: int = 10000000,
    ):
        """Initialize SHM sink.
        
        Args:
            socket_path: Path to the shared memory socket
            width: Frame width in pixels
            height: Frame height in pixels
            fps: Frames per second
            format: Pixel format (RGB, RGBA, I420, NV12)
            shm_size: Size of shared memory buffer in bytes
        """
        self.socket_path = socket_path
        self.shm_size = shm_size
        
        # Clean up any existing socket
        delete_socket(socket_path)
        
        # Initialize base class
        super().__init__(
            width=width,
            height=height,
            fps=fps,
            format=format,
            sink_type="shmsink",
            use_timestamps=True,  # SHM needs timestamps for synchronization
        )
    
    def _create_sink_element(self):
        """Create the shmsink element."""
        shmsink = Gst.ElementFactory.make("shmsink", "sink")
        if not shmsink:
            raise RuntimeError("Failed to create shmsink element")
        
        # Configure shmsink
        shmsink.set_property("socket-path", self.socket_path)
        shmsink.set_property("wait-for-connection", False)
        shmsink.set_property("shm-size", self.shm_size)
        shmsink.set_property("sync", True)  # Important for timing
        
        return shmsink
    
    def _on_started(self):
        """Log socket path when started."""
        print(f"SHM socket: {self.socket_path}")
    
    def _cleanup(self):
        """Clean up socket file."""
        delete_socket(self.socket_path)
