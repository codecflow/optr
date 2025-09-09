"""Writer protocols for the writer module."""

from typing import Protocol, TypeVar

from optr.core.io.protocols import Closer

T = TypeVar("T", contravariant=True)


class Writer(Protocol[T]):
    """Generic writer protocol."""

    def write(self, item: T) -> None:
        """Write an item."""
        ...


class Closable[T](Writer[T], Closer, Protocol):
    """A protocol for objects that can be written to and closed."""

    ...
