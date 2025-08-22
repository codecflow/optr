"""Buffer pooling for efficient memory management."""

from typing import Dict, List, Any
from gi.repository import Gst


class BufferPool:
    """Buffer pool for reusing GStreamer buffers to reduce allocations."""
    
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.pools: Dict[int, List[Gst.Buffer]] = {}
    
    def get(self, size: int) -> Gst.Buffer:
        """Get a buffer of the specified size from the pool."""
        if size in self.pools and self.pools[size]:
            return self.pools[size].pop()
        
        # Create new buffer if pool is empty
        return Gst.Buffer.new_allocate(None, size, None)
    
    def put(self, buffer: Gst.Buffer):
        """Return a buffer to the pool for reuse."""
        size = buffer.get_size()
        
        if size not in self.pools:
            self.pools[size] = []
        
        # Only keep up to max_size buffers per size
        if len(self.pools[size]) < self.max_size:
            # Clear buffer metadata for reuse
            buffer.pts = Gst.CLOCK_TIME_NONE
            buffer.dts = Gst.CLOCK_TIME_NONE
            buffer.duration = Gst.CLOCK_TIME_NONE
            buffer.offset = Gst.BUFFER_OFFSET_NONE
            buffer.offset_end = Gst.BUFFER_OFFSET_NONE
            self.pools[size].append(buffer)
    
    def clear(self):
        """Clear all buffers from the pool."""
        self.pools.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        total_buffers = sum(len(pool) for pool in self.pools.values())
        return {
            "total_buffers": total_buffers,
            "buffer_sizes": list(self.pools.keys()),
            "buffers_per_size": {size: len(pool) for size, pool in self.pools.items()}
        }
