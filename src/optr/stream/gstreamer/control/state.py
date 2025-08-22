"""Pipeline state management functions."""

from typing import Tuple
from gi.repository import Gst


def play(pipeline: Gst.Pipeline) -> bool:
    """Start pipeline playback (async)."""
    return pipeline.set_state(Gst.State.PLAYING) != Gst.StateChangeReturn.FAILURE


def pause(pipeline: Gst.Pipeline) -> bool:
    """Pause pipeline (async)."""
    return pipeline.set_state(Gst.State.PAUSED) != Gst.StateChangeReturn.FAILURE


def stop(pipeline: Gst.Pipeline) -> bool:
    """Stop pipeline and set to NULL (async)."""
    return pipeline.set_state(Gst.State.NULL) != Gst.StateChangeReturn.FAILURE


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

def wait_for_state_change(pipeline: Gst.Pipeline, target_state: Gst.State, 
                         timeout_seconds: float = 5.0) -> Tuple[bool, str]:
    """Wait for pipeline to reach target state with detailed error reporting."""
    timeout_ns = int(timeout_seconds * Gst.SECOND)
    ret, current, pending = pipeline.get_state(timeout_ns)
    
    if ret == Gst.StateChangeReturn.SUCCESS and current == target_state:
        return True, f"Successfully reached {target_state.value_nick}"
    elif ret == Gst.StateChangeReturn.ASYNC:
        return False, f"Timeout waiting for {target_state.value_nick} (current: {current.value_nick}, pending: {pending.value_nick})"
    elif ret == Gst.StateChangeReturn.FAILURE:
        return False, f"Failed to change state to {target_state.value_nick} (current: {current.value_nick})"
    else:
        return False, f"Unknown state change result: {ret.value_nick}"
