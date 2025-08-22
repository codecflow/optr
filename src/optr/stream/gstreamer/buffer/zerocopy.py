"""Zero-copy buffer operations for GStreamer."""

from contextlib import contextmanager
from gi.repository import Gst


@contextmanager
def readonly(buffer: Gst.Buffer):
    """Context manager for zero-copy read access to buffer data."""
    ok, info = buffer.map(Gst.MapFlags.READ)
    if not ok:
        raise RuntimeError("Failed to map buffer for READ")
    
    try:
        yield info.data
    finally:
        buffer.unmap(info)


@contextmanager
def readwrite(buffer: Gst.Buffer):
    """Context manager for zero-copy read/write access to buffer data."""
    ok, info = buffer.map(Gst.MapFlags.WRITE)
    if not ok:
        raise RuntimeError("Failed to map buffer for WRITE")
    
    try:
        yield info.data
    finally:
        buffer.unmap(info)


def wrap(data: bytes, timestamp_ns: int = 0, duration_ns: int | None = None) -> Gst.Buffer:
    """Create a GStreamer buffer that wraps existing bytes without copying."""
    # Note: This creates a new buffer but tries to minimize copying
    # True zero-copy would require memory that GStreamer can manage directly
    buf = Gst.Buffer.new_wrapped(data)
    buf.pts = timestamp_ns
    buf.dts = timestamp_ns
    if duration_ns is not None:
        buf.duration = duration_ns
    return buf


def allocate(size: int) -> Gst.Buffer:
    """Create a writable buffer of the specified size."""
    return Gst.Buffer.new_allocate(None, size, None)


def make(buffer: Gst.Buffer) -> Gst.Buffer:
    """Ensure buffer is writable, creating a copy if necessary."""
    return buffer.make_writable()


def is_writable(buffer: Gst.Buffer) -> bool:
    """Check if buffer is writable."""
    return buffer.is_writable()


def memory_count(buffer: Gst.Buffer) -> int:
    """Get the number of memory blocks in the buffer."""
    return buffer.n_memory()


def memory_size(buffer: Gst.Buffer, idx: int = -1) -> int:
    """Get size of memory block at index, or total size if idx=-1."""
    if idx == -1:
        return buffer.get_size()
    
    if idx >= buffer.n_memory():
        raise IndexError(f"Memory index {idx} out of range")
    
    memory = buffer.peek_memory(idx)
    return memory.get_size()


def slice(buffer: Gst.Buffer, offset: int, size: int) -> Gst.Buffer:
    """Create a new buffer that shares memory with the original (zero-copy slice)."""
    if offset + size > buffer.get_size():
        raise ValueError("Slice extends beyond buffer size")
    
    return buffer.copy_region(Gst.BufferCopyFlags.MEMORY, offset, size)


def merge(*buffers: Gst.Buffer) -> Gst.Buffer:
    """Merge multiple buffers into one (may involve copying)."""
    if not buffers:
        return Gst.Buffer.new()
    
    if len(buffers) == 1:
        return buffers[0]
    
    # Calculate total size
    total_size = sum(buf.get_size() for buf in buffers)
    
    # Create new buffer
    merged = Gst.Buffer.new_allocate(None, total_size, None)
    
    # Copy data from all buffers
    offset = 0
    for buf in buffers:
        buf_size = buf.get_size()
        merged.fill(offset, bytes(buf))
        offset += buf_size
    
    # Copy metadata from first buffer
    merged.pts = buffers[0].pts
    merged.dts = buffers[0].dts
    merged.duration = sum(buf.duration for buf in buffers if buf.duration != Gst.CLOCK_TIME_NONE)
    
    return merged


def read(buffer: Gst.Buffer) -> bytes:
    """Read bytes from buffer (helper for internal use)."""
    with readonly(buffer) as data:
        return bytes(data)
