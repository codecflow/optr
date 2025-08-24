"""GStreamer streaming utilities - functional toolkit."""

# import gi

# gi.require_version("Gst", "1.0")
# gi.require_version("GstVideo", "1.0")
# from gi.repository import Gst

# Gst.init(None)
# Functional primitives
from . import buffer, control, element, pipeline

# from .utils import create_caps_string, delete_socket, get_format_info
# Protocol-compliant wrappers
from .readers import (
    FileReader,
    RTMPReader,
    SHMReader,
    TestPatternReader,
    UDPReader,
    VideoReader,
)
from .writers import FileWriter, RTMPWriter, SHMWriter, UDPWriter, VideoWriter

__all__ = [
    # Functional primitives
    "buffer",
    "control",
    "element",
    "pipeline",
    # Protocol-compliant wrappers
    "VideoReader",
    "VideoWriter",
    "SHMReader",
    "SHMWriter",
    "RTMPReader",
    "RTMPWriter",
    "UDPReader",
    "UDPWriter",
    "FileReader",
    "FileWriter",
    "TestPatternReader",
]
