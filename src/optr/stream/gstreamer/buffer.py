"""Buffer and frame management utilities for GStreamer."""

import numpy as np
from gi.repository import Gst, GstVideo

from optr.stream.fps import FPS, ConvertibleToFPS
from . import caps


def to_buffer(
    data: bytes, timestamp_ns: int = 0, duration_ns: int | None = None
) -> Gst.Buffer:
    """
    Create a Gst.Buffer from bytes data.
    """
    buf = Gst.Buffer.new_allocate(None, len(data), None)
    buf.fill(0, data)
    buf.pts = timestamp_ns
    buf.dts = timestamp_ns
    if duration_ns is not None:
        buf.duration = duration_ns
    return buf


def from_buffer(buffer: Gst.Buffer, shape: tuple[int, ...]) -> np.ndarray:
    """
    Copy Gst.Buffer into a numpy array with the given shape.
    NOTE: Copies the data so we can safely unmap the buffer.
    """
    ok, info = buffer.map(Gst.MapFlags.READ)
    if not ok:
        raise RuntimeError("Failed to map buffer for READ")

    try:
        arr = np.frombuffer(info.data, dtype=np.uint8, count=info.size).copy()
    finally:
        buffer.unmap(info)

    return arr.reshape(shape)


def push(
    appsrc: Gst.Element,
    data: bytes,
    timestamp_ns: int = 0,
    duration_ns: int | None = None,
) -> Gst.FlowReturn:
    """Push bytes data to appsrc."""
    buf = to_buffer(data, timestamp_ns, duration_ns)
    return appsrc.emit("push-buffer", buf)


def pull(appsink: Gst.Element, timeout_ns: int = Gst.SECOND) -> np.ndarray | None:
    """
    Pull a sample from appsink and convert to ndarray.
    Supports packed/interleaved formats (RGB/BGR/RGBA/BGRA/GRAY8).
    """
    sample = appsink.emit("try-pull-sample", timeout_ns)
    if not sample:
        return None

    try:
        buf = sample.get_buffer()
        caps = sample.get_caps()

        # Parse caps manually since VideoInfo.from_caps() can fail
        structure = caps.get_structure(0)
        format_str = structure.get_string("format")
        width = structure.get_int("width")[1]
        height = structure.get_int("height")[1]
        
        # Map format string to channels
        if format_str in ("RGB", "BGR"):
            channels = 3
        elif format_str in ("RGBA", "BGRA", "ARGB", "ABGR"):
            channels = 4
        elif format_str == "GRAY8":
            channels = 1
        else:
            raise NotImplementedError(
                f"Unsupported pixel format: {format_str!r} (use videoconvert to RGB/RGBA)"
            )

        # Calculate expected size
        expected_size = width * height * channels
        actual_size = buf.get_size()
        
        if actual_size < expected_size:
            raise RuntimeError(f"Buffer too small: got {actual_size}, expected {expected_size}")

        ok, mapinfo = buf.map(Gst.MapFlags.READ)
        if not ok:
            raise RuntimeError("Failed to map buffer for READ")

        try:
            # Use the actual buffer size, but don't exceed expected size
            safe_size = min(mapinfo.size, expected_size)
            data = np.frombuffer(mapinfo.data, dtype=np.uint8, count=safe_size).copy()
        finally:
            buf.unmap(mapinfo)

        # Simple reshape for packed formats (no stride handling needed for RGB)
        if len(data) == expected_size:
            frame = data.reshape((height, width, channels))
        else:
            raise RuntimeError(f"Data size mismatch: got {len(data)}, expected {expected_size}")
            
        return frame
    finally:
        try:
            sample.unref()
        except Exception:
            pass


def set_timestamp(
    buffer: Gst.Buffer,
    pts_ns: int,
    dts_ns: int | None = None,
    duration_ns: int | None = None,
) -> Gst.Buffer:
    """Set PTS/DTS[/duration] on buffer (ns)."""
    buffer.pts = pts_ns
    buffer.dts = pts_ns if dts_ns is None else dts_ns
    if duration_ns is not None:
        buffer.duration = duration_ns
    return buffer
