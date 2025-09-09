"""Main loop utilities for pipeline control."""

from collections.abc import Generator
from contextlib import contextmanager

from gi.repository import GLib


@contextmanager
def mainloop() -> Generator[GLib.MainLoop, None, None]:
    """
    Context manager for a GLib MainLoop. Does NOT change pipeline state.
    Combine with `running_pipeline` if you want auto start/stop.
    """
    loop = GLib.MainLoop()
    try:
        yield loop
    finally:
        if loop.is_running():
            loop.quit()
