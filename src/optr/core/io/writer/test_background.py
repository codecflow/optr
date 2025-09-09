import tempfile
import threading
from pathlib import Path

from .background import BackgroundWriter
from .protocols import Closable


class MockWriter(Closable[bytes]):
    """Mock writer with event-based synchronization."""

    def __init__(self, path: Path):
        self.path = path
        self.closed = False
        self.writes: list[bytes] = []
        self.write_event = threading.Event()

        # Simulate file creation
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch()

    def write(self, data: bytes) -> None:
        if self.closed:
            raise RuntimeError("Writer closed")

        self.writes.append(data)
        self.write_event.set()

    def close(self) -> None:
        self.closed = True

    def wait_write(self, timeout: float = 1.0) -> bool:
        """Wait for write to occur."""
        return self.write_event.wait(timeout)


class FailingWriter(MockWriter):
    """Writer that fails after N writes."""

    def __init__(self, path: Path, fail_after: int):
        super().__init__(path)
        self.fail_after = fail_after

    def write(self, data: bytes) -> None:
        if len(self.writes) >= self.fail_after:
            raise RuntimeError(f"Failed after {self.fail_after} writes")
        super().write(data)


class CopyableData:
    """Data that supports copying."""

    def __init__(self, value: str):
        self.value = value

    def copy(self):
        return CopyableData(self.value)


class TestBackgroundWriter:
    """Essential BackgroundWriter tests."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.path = Path(self.temp_dir) / "test.bin"

    def test_write_and_close(self):
        """Basic write and close functionality."""
        mock = MockWriter(self.path)
        writer = BackgroundWriter(mock)

        writer.write(b"test")
        writer.close()

        assert len(mock.writes) == 1
        assert mock.writes[0] == b"test"
        assert mock.closed

    def test_write_ordering(self):
        """Multiple writes processed in order."""
        mock = MockWriter(self.path)
        writer = BackgroundWriter(mock)

        data = [b"first", b"second", b"third"]
        for d in data:
            writer.write(d)

        writer.close()

        assert mock.writes == data

    def test_non_blocking(self):
        """Write returns immediately."""
        mock = MockWriter(self.path)
        writer = BackgroundWriter(mock)

        writer.write(b"test")

        # Not processed yet
        assert len(mock.writes) == 0

        # Wait for processing
        assert mock.wait_write()
        writer.close()
        assert len(mock.writes) == 1

    def test_thread_safety(self):
        """Concurrent writes work correctly."""
        mock = MockWriter(self.path)
        writer = BackgroundWriter(mock)

        errors = []

        def worker(thread_id: int):
            try:
                for i in range(5):
                    writer.write(f"t{thread_id}-{i}".encode())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        writer.close()

        assert len(errors) == 0
        assert len(mock.writes) == 15

    def test_write_after_close(self):
        """Writes after close are ignored."""
        mock = MockWriter(self.path)
        writer = BackgroundWriter(mock)

        writer.write(b"before")
        writer.close()

        count = len(mock.writes)
        writer.write(b"after")

        assert len(mock.writes) == count

    def test_error_callback(self):
        """Error callback fires on writer failure."""
        failing = FailingWriter(self.path, fail_after=1)
        writer = BackgroundWriter(failing)

        error_caught = []
        error_event = threading.Event()

        def on_error(e):
            error_caught.append(e)
            error_event.set()

        writer.on("error", on_error)

        writer.write(b"first")  # succeeds
        writer.write(b"second")  # fails

        assert error_event.wait(timeout=1.0)
        writer.close()

        assert len(error_caught) == 1
        assert isinstance(error_caught[0], RuntimeError)

    def test_complete_callback(self):
        """Complete callback fires on close."""
        mock = MockWriter(self.path)
        writer = BackgroundWriter(mock)

        completed = []
        complete_event = threading.Event()

        writer.on("complete", lambda: [completed.append(True), complete_event.set()])
        writer.write(b"test")
        writer.close()

        assert complete_event.wait(timeout=1.0)
        assert len(completed) == 1

    def test_data_copy(self):
        """Data with copy method gets copied."""
        mock = MockWriter(self.path)
        writer = BackgroundWriter(mock)

        original = CopyableData("test")
        writer.write(original)
        writer.close()

        written = mock.writes[0]
        assert written.value == "test"
        assert written is not original

    def test_data_passthrough(self):
        """Data without copy method passed through."""
        mock = MockWriter(self.path)
        writer = BackgroundWriter(mock)

        data = b"test"
        writer.write(data)
        writer.close()

        assert mock.writes[0] is data
