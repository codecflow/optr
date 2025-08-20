"""Core I/O utilities - functional toolkit for Reader/Writer protocols."""

from collections.abc import Iterable, Iterator
from contextlib import closing as contextlib_closing
from typing import TypeVar, cast

from .protocols import Reader, Writer

T = TypeVar("T")
_SENTINEL = object()


class IterableReader(Reader[T]):
    """Adapter: Iterable[T] -> Reader[T]."""

    __slots__ = ("_iterator",)

    def __init__(self, items: Iterable[T]):
        self._iterator = iter(items)

    def read(self) -> T | None:
        obj = next(self._iterator, _SENTINEL)
        if obj is _SENTINEL:
            return None
        return cast(T, obj)


class ReaderIterator(Iterator[T]):
    """Adapter: Reader[T] -> Iterator[T]."""

    __slots__ = ("_reader",)

    def __init__(self, reader: Reader[T]):
        self._reader = reader

    def __next__(self) -> T:
        item = self._reader.read()
        if item is None:
            raise StopIteration
        return item


def copy(dst: Writer[T], src: Iterator[T]) -> int:
    """Copy from iterator to writer.

    Args:
        dst: Destination writer
        src: Source iterator

    Returns:
        Number of items copied
    """
    count = 0
    for item in src:
        dst.write(item)
        count += 1
    return count


def fanout(src: Iterator[T], *writers: Writer[T]) -> None:
    """Write each item from source to all writers.

    Args:
        src: Source iterator
        *writers: Destination writers
    """
    for item in src:
        for writer in writers:
            writer.write(item)


# Re-export contextlib.closing for convenience
closing = contextlib_closing
