"""Core I/O protocols."""

from typing import Protocol, TypeVar

TCO = TypeVar("TCO", covariant=True)
TCONTRA = TypeVar("TCONTRA", contravariant=True)


class Reader(Protocol[TCO]):
    """Generic reader protocol."""

    def read(self) -> TCO | None:
        """Read next item, returns None only when no more data."""
        ...


class Writer(Protocol[TCONTRA]):
    """Generic writer protocol."""

    def write(self, item: TCONTRA) -> None:
        """Write an item."""
        ...


class Closer(Protocol):
    """Closeable resource."""

    def close(self) -> None:
        """Close and cleanup resources."""
        ...
