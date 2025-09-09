"""Core buffer operations for GStreamer - bytes focused."""

from gi.repository import Gst


def write(
    data: bytes, timestamp_ns: int = 0, duration_ns: int | None = None
) -> Gst.Buffer:
    """Create a Gst.Buffer from bytes data."""
    buf = Gst.Buffer.new_allocate(None, len(data), None)
    buf.fill(0, data)
    buf.pts = timestamp_ns
    buf.dts = timestamp_ns
    if duration_ns is not None:
        buf.duration = duration_ns
    return buf


def read(buffer: Gst.Buffer) -> bytes:
    """Extract bytes data from a Gst.Buffer."""
    ok, info = buffer.map(Gst.MapFlags.READ)
    if not ok:
        raise RuntimeError("Failed to map buffer for READ")

    try:
        data = bytes(info.data)
    finally:
        buffer.unmap(info)

    return data


def push(
    appsrc: Gst.Element,
    data: bytes,
    timestamp_ns: int = 0,
    duration_ns: int | None = None,
) -> Gst.FlowReturn:
    """Push bytes data to appsrc."""
    buf = write(data, timestamp_ns, duration_ns)
    return appsrc.emit("push-buffer", buf)


def pull(appsink: Gst.Element, timeout_ns: int = Gst.SECOND) -> bytes | None:
    """Pull bytes data from appsink."""
    sample = appsink.emit("try-pull-sample", timeout_ns)
    if not sample:
        return None

    try:
        buf = sample.get_buffer()
        return read(buf)
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


def info(buffer: Gst.Buffer) -> dict:
    """Get buffer metadata information."""
    return {
        "size": buffer.get_size(),
        "pts": buffer.pts,
        "dts": buffer.dts,
        "duration": buffer.duration,
        "offset": buffer.offset,
        "offset_end": buffer.offset_end,
    }


def copy_metadata(src: Gst.Buffer, dst: Gst.Buffer) -> Gst.Buffer:
    """Copy metadata from source buffer to destination buffer."""
    dst.pts = src.pts
    dst.dts = src.dts
    dst.duration = src.duration
    dst.offset = src.offset
    dst.offset_end = src.offset_end
    return dst
