"""Pipeline message handling utilities."""

from typing import Callable
from gi.repository import Gst


def handle_messages(
    pipeline: Gst.Pipeline,
    callback: Callable[[Gst.Message], bool],
    message_types: Gst.MessageType = Gst.MessageType.ANY,
) -> None:
    """
    Connect a bus 'message' handler. The callback should return True to keep watching,
    False to detach. Requires a running GLib main loop.
    """
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    handler_id: int | None = None

    def on_message(_bus: Gst.Bus, message: Gst.Message) -> None:
        nonlocal handler_id
        if message.type & message_types:
            keep = True
            try:
                keep = callback(message)
            finally:
                if not keep:
                    if handler_id is not None:
                        _bus.disconnect(handler_id)
                        handler_id = None
                    _bus.remove_signal_watch()

    handler_id = bus.connect("message", on_message)
