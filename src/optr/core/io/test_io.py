"""Tests for core I/O utilities."""

import pytest

from .iterator import IterableReader, ReaderIterator, copy, fanout


class ListWriter:
    """Simple writer that collects items into a list for testing."""

    def __init__(self):
        self.items: list = []

    def write(self, item) -> None:
        self.items.append(item)

    def close(self) -> None:
        pass


class TestIterableReader:
    """Test IterableReader adapter."""

    def test_empty_iterable(self):
        reader = IterableReader([])
        assert reader.read() is None

    def test_single_item(self):
        reader = IterableReader([42])
        assert reader.read() == 42
        assert reader.read() is None

    def test_multiple_items(self):
        reader = IterableReader([1, 2, 3])
        assert reader.read() == 1
        assert reader.read() == 2
        assert reader.read() == 3
        assert reader.read() is None

    def test_string_iterable(self):
        reader = IterableReader("abc")
        assert reader.read() == "a"
        assert reader.read() == "b"
        assert reader.read() == "c"
        assert reader.read() is None

    def test_generator(self):
        def gen():
            yield 1
            yield 2
            yield 3

        reader = IterableReader(gen())
        assert reader.read() == 1
        assert reader.read() == 2
        assert reader.read() == 3
        assert reader.read() is None


class TestReaderIterator:
    """Test ReaderIterator adapter."""

    def test_empty_reader(self):
        reader = IterableReader([])
        iterator = ReaderIterator(reader)
        items = list(iterator)
        assert items == []

    def test_single_item(self):
        reader = IterableReader([42])
        iterator = ReaderIterator(reader)
        items = list(iterator)
        assert items == [42]

    def test_multiple_items(self):
        reader = IterableReader([1, 2, 3])
        iterator = ReaderIterator(reader)
        items = list(iterator)
        assert items == [1, 2, 3]

    def test_iterator_protocol(self):
        reader = IterableReader([1, 2, 3])
        iterator = ReaderIterator(reader)

        assert next(iterator) == 1
        assert next(iterator) == 2
        assert next(iterator) == 3

        with pytest.raises(StopIteration):
            next(iterator)

    def test_for_loop(self):
        reader = IterableReader([1, 2, 3])
        iterator = ReaderIterator(reader)

        result = []
        for item in iterator:
            result.append(item)

        assert result == [1, 2, 3]


class TestCopy:
    """Test copy utility function."""

    def test_empty_iterator(self):
        writer = ListWriter()
        count = copy(writer, iter([]))
        assert count == 0
        assert writer.items == []

    def test_single_item(self):
        writer = ListWriter()
        count = copy(writer, iter([42]))
        assert count == 1
        assert writer.items == [42]

    def test_multiple_items(self):
        writer = ListWriter()
        count = copy(writer, iter([1, 2, 3]))
        assert count == 3
        assert writer.items == [1, 2, 3]

    def test_generator(self):
        def gen():
            yield "a"
            yield "b"
            yield "c"

        writer = ListWriter()
        count = copy(writer, gen())
        assert count == 3
        assert writer.items == ["a", "b", "c"]

    def test_reader_to_writer(self):
        reader = IterableReader([1, 2, 3])
        writer = ListWriter()
        iterator = ReaderIterator(reader)

        count = copy(writer, iterator)
        assert count == 3
        assert writer.items == [1, 2, 3]


class TestFanout:
    """Test fanout utility function."""

    def test_empty_iterator(self):
        writer1 = ListWriter()
        writer2 = ListWriter()
        fanout(iter([]), writer1, writer2)

        assert writer1.items == []
        assert writer2.items == []

    def test_single_writer(self):
        writer = ListWriter()
        fanout(iter([1, 2, 3]), writer)
        assert writer.items == [1, 2, 3]

    def test_multiple_writers(self):
        writer1 = ListWriter()
        writer2 = ListWriter()
        writer3 = ListWriter()

        fanout(iter([1, 2, 3]), writer1, writer2, writer3)

        assert writer1.items == [1, 2, 3]
        assert writer2.items == [1, 2, 3]
        assert writer3.items == [1, 2, 3]

    def test_no_writers(self):
        # Should not raise an error
        fanout(iter([1, 2, 3]))

    def test_generator(self):
        def gen():
            yield "x"
            yield "y"

        writer1 = ListWriter()
        writer2 = ListWriter()
        fanout(gen(), writer1, writer2)

        assert writer1.items == ["x", "y"]
        assert writer2.items == ["x", "y"]


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_iterable_to_reader_to_iterator_to_writer(self):
        # Full pipeline: Iterable -> Reader -> Iterator -> Writer
        data = [1, 2, 3, 4, 5]

        # Iterable -> Reader
        reader = IterableReader(data)

        # Reader -> Iterator
        iterator = ReaderIterator(reader)

        # Iterator -> Writer
        writer = ListWriter()
        count = copy(writer, iterator)

        assert count == 5
        assert writer.items == data

    def test_fanout_with_reader_iterator(self):
        reader = IterableReader([10, 20, 30])
        iterator = ReaderIterator(reader)

        writer1 = ListWriter()
        writer2 = ListWriter()

        fanout(iterator, writer1, writer2)

        assert writer1.items == [10, 20, 30]
        assert writer2.items == [10, 20, 30]

    def test_chained_operations(self):
        # Create a pipeline that processes data through multiple stages
        source_data = range(5)

        # Stage 1: Iterable -> Reader
        reader = IterableReader(source_data)

        # Stage 2: Reader -> Iterator (with transformation)
        iterator = ReaderIterator(reader)
        transformed = (x * 2 for x in iterator)

        # Stage 3: Fanout to multiple writers
        writer1 = ListWriter()
        writer2 = ListWriter()
        fanout(transformed, writer1, writer2)

        expected = [0, 2, 4, 6, 8]
        assert writer1.items == expected
        assert writer2.items == expected


if __name__ == "__main__":
    pytest.main([__file__])
