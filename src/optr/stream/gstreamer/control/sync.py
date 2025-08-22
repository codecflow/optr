"""Synchronous pipeline operations."""

from typing import Optional
from gi.repository import Gst


def seek(pipeline: Gst.Pipeline, position_seconds: float) -> bool:
    """Seek to position (seconds)."""
    position_ns = int(position_seconds * Gst.SECOND)
    return pipeline.seek_simple(
        Gst.Format.TIME,
        Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
        position_ns,
    )


def wait_for_eos(pipeline: Gst.Pipeline, timeout_seconds: float | None = None) -> bool:
    """Block until EOS, or raise on ERROR. Returns True on EOS, False on timeout."""
    bus = pipeline.get_bus()
    timeout_ns = (
        int(timeout_seconds * Gst.SECOND)
        if timeout_seconds is not None
        else Gst.CLOCK_TIME_NONE
    )
    msg = bus.timed_pop_filtered(
        timeout_ns, Gst.MessageType.EOS | Gst.MessageType.ERROR
    )
    if not msg:
        return False
    if msg.type == Gst.MessageType.EOS:
        return True
    if msg.type == Gst.MessageType.ERROR:
        err, debug = msg.parse_error()
        raise RuntimeError(f"Pipeline error: {err.message} (debug: {debug or 'n/a'})")
    return False


def measure_latency(pipeline: Gst.Pipeline, timeout_seconds: float = 5.0) -> Optional[float]:
    """Measure pipeline latency using latency query."""
    query = Gst.Query.new_latency()
    if pipeline.query(query):
        live, min_latency, max_latency = query.parse_latency()
        return min_latency / Gst.SECOND  # Convert to seconds
    return None
