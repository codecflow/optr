"""GStreamer-compatible buffer implementation using udpsink."""

from gi.repository import Gst

from .sink import Sink


class UDPSink(Sink):
    """Buffer that uses GStreamer's udpsink to publish frames over UDP."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5000,
        width: int = 640,
        height: int = 480,
        fps: float = 30.0,
        format: str = "RGB",
        multicast: bool = False,
        ttl: int = 64,
    ):
        """Initialize UDP sink.

        Args:
            host: Target host IP address
            port: Target UDP port
            width: Frame width in pixels
            height: Frame height in pixels
            fps: Frames per second
            format: Pixel format (RGB, RGBA, I420, NV12)
            multicast: Enable multicast mode
            ttl: Time-to-live for multicast packets
        """
        # Check for UDP plugin availability
        if not Gst.ElementFactory.find("udpsink"):
            raise RuntimeError(
                "GStreamer udp plugin not found. "
                "Ensure GStreamer with 'udp' plugin is installed."
            )

        self.host = host
        self.port = port
        self.multicast = multicast
        self.ttl = ttl

        # Initialize base class
        super().__init__(
            width=width,
            height=height,
            fps=fps,
            format=format,
            sink_type="udpsink",
            use_timestamps=False,  # UDP doesn't need timestamps with sync=False
        )

    def _create_sink_element(self):
        """Create the udpsink element."""
        udpsink = Gst.ElementFactory.make("udpsink", "sink")
        if not udpsink:
            raise RuntimeError("Failed to create udpsink element")

        # Configure udpsink
        udpsink.set_property("host", self.host)
        udpsink.set_property("port", self.port)

        # Configure for live streaming
        udpsink.set_property("sync", False)  # Don't sync to clock
        udpsink.set_property("async", False)  # Don't wait for preroll

        # Set multicast properties if enabled
        if self.multicast:
            udpsink.set_property("auto-multicast", True)

        # Set TTL for multicast
        udpsink.set_property("ttl", self.ttl)

        # Optional: Set buffer properties for better performance
        udpsink.set_property("qos", False)  # Disable QoS events
        udpsink.set_property("max-lateness", -1)  # Never drop buffers

        return udpsink

    def _on_started(self):
        """Log UDP streaming details."""
        multicast_info = f" (multicast, ttl={self.ttl})" if self.multicast else ""
        print(f"UDP streaming to {self.host}:{self.port}{multicast_info}")
