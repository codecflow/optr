"""GStreamer element factory functions organized by category."""

# Core functionality
from .base import create

# Application interface elements
from .app import AppSink, AppSrc, appsink, appsrc

# Network streaming elements
from .network import (
    RTMPSink,
    RTPSource,
    SHMSink,
    SHMSource,
    UDPSink,
    UDPSource,
    rtmpsink,
    rtmpsrc,
    shmsink,
    shmsrc,
    udpsink,
    udpsrc,
)

# Encoding/decoding elements
from .encoding import AVDecH264, DecodeBin, X264Enc, avdec_h264, decodebin, x264enc

# Video processing elements
from .processing import (
    CapsFilter,
    Queue,
    Tee,
    VideoConvert,
    VideoScale,
    capsfilter,
    queue,
    tee,
    videoconvert,
    videoscale,
)

# Muxing and payload elements
from .muxing import (
    FLVMux,
    MP4Mux,
    RTPH264Depay,
    RTPH264Pay,
    flvmux,
    mp4mux,
    payloader,
    rtph264depay,
)

# File I/O elements
from .file import FileSink, FileSource, filesink, filesrc

# Test elements
from .test import VideoTestSource, videotestsrc

__all__ = [
    # Core
    "create",
    # App elements
    "appsrc",
    "appsink",
    "AppSrc",
    "AppSink",
    # Network elements
    "shmsink",
    "shmsrc",
    "udpsink",
    "udpsrc",
    "rtmpsink",
    "rtmpsrc",
    "SHMSink",
    "SHMSource",
    "UDPSink",
    "UDPSource",
    "RTMPSink",
    "RTPSource",
    # Encoding elements
    "x264enc",
    "decodebin",
    "avdec_h264",
    "X264Enc",
    "DecodeBin",
    "AVDecH264",
    # Processing elements
    "queue",
    "capsfilter",
    "videoconvert",
    "videoscale",
    "tee",
    "Queue",
    "CapsFilter",
    "VideoConvert",
    "VideoScale",
    "Tee",
    # Muxing elements
    "flvmux",
    "mp4mux",
    "payloader",
    "rtph264depay",
    "FLVMux",
    "MP4Mux",
    "RTPH264Pay",
    "RTPH264Depay",
    # File elements
    "filesrc",
    "filesink",
    "FileSource",
    "FileSink",
    # Test elements
    "videotestsrc",
    "VideoTestSource",
]
