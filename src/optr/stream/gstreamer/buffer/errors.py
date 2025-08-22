"""Buffer-specific error classes."""


class BufferError(Exception):
    """Base exception for buffer-related errors."""
    pass


class BufferMapError(BufferError):
    """Raised when buffer mapping fails."""
    
    def __init__(self, operation: str):
        self.operation = operation
        super().__init__(f"Failed to map buffer for {operation}")


class BufferReadError(BufferError):
    """Raised when buffer read operations fail."""
    
    def __init__(self, details: str = ""):
        self.details = details
        super().__init__(f"Buffer read failed{': ' + details if details else ''}")


class BufferWriteError(BufferError):
    """Raised when buffer write operations fail."""
    
    def __init__(self, details: str = ""):
        self.details = details
        super().__init__(f"Buffer write failed{': ' + details if details else ''}")


class BufferSliceError(BufferError):
    """Raised when buffer slice operations fail."""
    
    def __init__(self, offset: int, size: int, buffer_size: int):
        self.offset = offset
        self.size = size
        self.buffer_size = buffer_size
        super().__init__(f"Slice [{offset}:{offset + size}] extends beyond buffer size {buffer_size}")
