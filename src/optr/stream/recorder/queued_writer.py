"""QueuedWriter that wraps a writer and makes it thread-safe with background processing."""

import queue
import threading
import time
from typing import TypeVar
import numpy as np
from .writer import Writer

T = TypeVar('T')


class QueuedWriter(Writer[T]):
    """Wraps a Writer and provides non-blocking writes via background queue processing."""
    
    def __init__(self, writer: Writer[T]) -> None:
        """Initialize and start background processing thread."""
        self.writer = writer
        self.queue: queue.Queue = queue.Queue(maxsize=0)
        self.active = True
        self.queued = 0
        self.written = 0
        
        # Start processing thread immediately
        self.thread = threading.Thread(
            target=self._process_loop,
            daemon=False,
            name=f"queued-writer-{getattr(writer, 'path', 'unknown')}"
        )
        self.thread.start()
        
    def write(self, frame: T) -> None:
        """Write frame to queue for background processing."""
        if not self.active:
            return
            
        try:
            self.queue.put_nowait(frame.copy() if hasattr(frame, 'copy') else frame)
            self.queued += 1
        except queue.Full:
            print(f"Warning: QueuedWriter queue full, dropping frame")
            
    def close(self) -> None:
        """Stop background processing and close underlying writer."""
        if not self.active:
            return
            
        # Send end-of-stream sentinel
        self.active = False
        self.queue.put(None)  # EOS marker
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)
            
            if self.thread.is_alive():
                print("Warning: QueuedWriter thread did not stop gracefully within timeout")
            
        # Close underlying writer
        self.writer.close()
        
    def _process_loop(self) -> None:
        """Process frames from queue in background thread."""
        while True:
            try:
                frame = self.queue.get(timeout=0.1)
                
                # Check for EOS
                if frame is None:
                    break
                    
                # Write frame to underlying writer
                self.writer.write(frame)
                self.written += 1
                self.queue.task_done()
                
            except queue.Empty:
                if not self.active:
                    break
                continue
            except Exception as e:
                print(f"Error in QueuedWriter processing loop: {e}")
                continue
