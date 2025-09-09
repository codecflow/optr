"""BackgroundWriter that wraps a writer and makes it thread-safe with background processing."""

import queue
import threading
from collections.abc import Callable
from typing import Literal, Self

from .protocols import Closable

type Event = Literal["complete", "error", "progress"]


class BackgroundWriter[T](Closable[T]):
    """Wraps a Writer and provides non-blocking writes via background queue processing."""

    def __init__(self, writer: Closable[T]) -> None:
        """Initialize and start background processing thread."""
        self.writer = writer
        self.queue: queue.Queue = queue.Queue(maxsize=0)
        self.active = True
        self.queued = 0
        self.written = 0

        # Event callbacks - initialized to noop functions
        self._on_complete: Callable[[], None] = lambda: None
        self._on_error: Callable[[Exception], None] = lambda e: None
        self._on_progress: Callable[[int, int], None] = lambda w, q: None

        # Start processing thread immediately
        self.thread = threading.Thread(
            target=self._process_loop,
            daemon=False,
            name=f"background-writer-{getattr(writer, 'path', 'unknown')}",
        )
        self.thread.start()

    def on(self, event: Event, handler: Callable) -> Self:
        """Register callback for event.

        Args:
            event: Event type ("complete", "error", "progress")
            handler: Callback function

        Returns:
            Self for method chaining
        """
        match event:
            case "complete":
                self._on_complete = handler
            case "error":
                self._on_error = handler
            case "progress":
                self._on_progress = handler
        return self

    def write(self, data: T) -> None:
        """Write data to queue for background processing."""
        if not self.active:
            return

        try:
            self.queue.put_nowait(data.copy() if hasattr(data, "copy") else data)
            self.queued += 1
        except queue.Full:
            print("Warning: BackgroundWriter queue full, dropping data")

    def close(self) -> None:
        """Stop background processing and close underlying writer."""
        if not self.active:
            return

        # Send end-of-stream sentinel
        self.active = False
        self.queue.put(None)  # EOS marker

        # Wait for thread to finish (writer will be closed in _process_loop)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)

            if self.thread.is_alive():
                print(
                    "Warning: BackgroundWriter thread did not stop gracefully within timeout"
                )

    def _process_loop(self) -> None:
        """Process datas from queue in background thread."""
        try:
            while True:
                try:
                    data = self.queue.get(timeout=0.1)

                    # Check for EOS
                    if data is None:
                        break

                    # Write data to underlying writer
                    self.writer.write(data)
                    self.written += 1
                    self.queue.task_done()

                    # Fire progress callback every 10 datas
                    if self.written % 10 == 0:
                        try:
                            self._on_progress(self.written, self.queued)
                        except Exception as e:
                            print(f"Error in progress callback: {e}")

                except queue.Empty:
                    if not self.active:
                        break
                    continue

        except Exception as e:
            # Fire error callback
            try:
                self._on_error(e)
            except Exception as callback_error:
                print(f"Error in error callback: {callback_error}")
            print(f"Error in BackgroundWriter processing loop: {e}")
        finally:
            # Close underlying writer
            try:
                self.writer.close()
            except Exception as e:
                print(f"Error closing writer: {e}")

            # Fire completion callback
            try:
                self._on_complete()
            except Exception as e:
                print(f"Error in completion callback: {e}")
