"""Pipeline state management and control utilities."""

from contextlib import contextmanager
from typing import Callable, Generator

from gi.repository import GLib, Gst


def play(pipeline: Gst.Pipeline) -> bool:
    """Start pipeline playback (async)."""
    return pipeline.set_state(Gst.State.PLAYING) != Gst.StateChangeReturn.FAILURE


def pause(pipeline: Gst.Pipeline) -> bool:
    """Pause pipeline (async)."""
    return pipeline.set_state(Gst.State.PAUSED) != Gst.StateChangeReturn.FAILURE


def stop(pipeline: Gst.Pipeline) -> bool:
    """Stop pipeline and set to NULL (async)."""
    return pipeline.set_state(Gst.State.NULL) != Gst.StateChangeReturn.FAILURE


def play_sync(pipeline: Gst.Pipeline, timeout_ns: int = Gst.SECOND * 5) -> None:
    """Start and wait until PLAYING or raise."""
    if not play(pipeline):
        raise RuntimeError("Failed to start pipeline")
    ret, cur, _ = pipeline.get_state(timeout_ns)
    if ret != Gst.StateChangeReturn.SUCCESS or cur != Gst.State.PLAYING:
        raise RuntimeError(f"Pipeline did not reach PLAYING (ret={ret}, current={cur})")


def pause_sync(pipeline: Gst.Pipeline, timeout_ns: int = Gst.SECOND * 5) -> None:
    if not pause(pipeline):
        raise RuntimeError("Failed to pause pipeline")
    ret, cur, _ = pipeline.get_state(timeout_ns)
    if ret != Gst.StateChangeReturn.SUCCESS or cur != Gst.State.PAUSED:
        raise RuntimeError(f"Pipeline did not reach PAUSED (ret={ret}, current={cur})")


def stop_sync(pipeline: Gst.Pipeline, timeout_ns: int = Gst.SECOND * 5) -> None:
    if not stop(pipeline):
        raise RuntimeError("Failed to stop pipeline")
    ret, cur, _ = pipeline.get_state(timeout_ns)
    if ret != Gst.StateChangeReturn.SUCCESS or cur != Gst.State.NULL:
        raise RuntimeError(f"Pipeline did not reach NULL (ret={ret}, current={cur})")


def get_state(
    pipeline: Gst.Pipeline, timeout_ns: int = Gst.SECOND
) -> tuple[Gst.State, Gst.State]:
    """Get current and pending pipeline state (waits up to timeout_ns)."""
    ret, current, pending = pipeline.get_state(timeout_ns)
    if ret == Gst.StateChangeReturn.SUCCESS:
        return current, pending
    raise RuntimeError(f"Failed to get pipeline state: {ret}")


def wait_for_state(
    pipeline: Gst.Pipeline, state: Gst.State, timeout_ns: int = Gst.SECOND * 5
) -> bool:
    """Wait until `state` or timeout."""
    ret, current, _ = pipeline.get_state(timeout_ns)
    return ret == Gst.StateChangeReturn.SUCCESS and current == state


def is_playing(pipeline: Gst.Pipeline) -> bool:
    try:
        current, _ = get_state(pipeline, timeout_ns=0)
        return current == Gst.State.PLAYING
    except RuntimeError:
        return False


def is_paused(pipeline: Gst.Pipeline) -> bool:
    try:
        current, _ = get_state(pipeline, timeout_ns=0)
        return current == Gst.State.PAUSED
    except RuntimeError:
        return False


def seek(pipeline: Gst.Pipeline, position_seconds: float) -> bool:
    """Seek to position (seconds)."""
    position_ns = int(position_seconds * Gst.SECOND)
    return pipeline.seek_simple(
        Gst.Format.TIME,
        Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
        position_ns,
    )


def wait_for_eos(pipeline: Gst.Pipeline, timeout_seconds: float | None = None) -> bool:
    """Block until EOS, or raise on ERROR. Returns True on EOS, False on timeout."""
    bus = pipeline.get_bus()
    timeout_ns = (
        int(timeout_seconds * Gst.SECOND)
        if timeout_seconds is not None
        else Gst.CLOCK_TIME_NONE
    )
    msg = bus.timed_pop_filtered(
        timeout_ns, Gst.MessageType.EOS | Gst.MessageType.ERROR
    )
    if not msg:
        return False
    if msg.type == Gst.MessageType.EOS:
        return True
    if msg.type == Gst.MessageType.ERROR:
        err, debug = msg.parse_error()
        raise RuntimeError(f"Pipeline error: {err.message} (debug: {debug or 'n/a'})")
    return False


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


@contextmanager
def running_pipeline(pipeline: Gst.Pipeline) -> Generator[Gst.Pipeline, None, None]:
    """Start pipeline on enter; ensure it is stopped on exit."""
    try:
        play_sync(pipeline)  # raises on failure
        yield pipeline
    finally:
        stop_sync(pipeline)


def run_until_eos(pipeline: Gst.Pipeline) -> None:
    """Convenience: start, run a main loop, stop at EOS or ERROR."""

    def _on_bus(msg: Gst.Message) -> bool:
        t = msg.type
        if t == Gst.MessageType.EOS:
            loop.quit()
            return False
        if t == Gst.MessageType.ERROR:
            err, debug = msg.parse_error()
            loop.quit()
            raise RuntimeError(
                f"Pipeline error: {err.message} (debug: {debug or 'n/a'})"
            )
        return True

    with running_pipeline(pipeline):
        with mainloop() as loop:
            handle_messages(
                pipeline, _on_bus, Gst.MessageType.EOS | Gst.MessageType.ERROR
            )
            loop.run()
