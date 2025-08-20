"""Core I/O protocols and utilities."""

from .iterator import IterableReader, ReaderIterator, closing, copy, fanout
from .protocols import Closer, Reader, Writer

__all__ = [
    # Protocols
    "Reader",
    "Writer",
    "Closer",
    # Adapters
    "IterableReader",
    "ReaderIterator",
    # Utilities
    "copy",
    "fanout",
    "closing",
]
