"""
Core action system
Simple, composable, and extensible
"""

from types import SimpleNamespace
from typing import Protocol


class Action(Protocol):
    type: str


def action(type: str, **parms) -> Action:
    return SimpleNamespace(type=type, **parms)


def chain(*actions: Action) -> list[Action]:
    """Chain actions together"""
    return list(actions)


def batch(*actions: Action) -> Action:
    """Batch actions for parallel execution"""
    return action("batch", actions=list(actions))


def sequence(*actions: Action, delay: float = 0) -> Action:
    """Create sequence with optional delay between actions"""
    return action("sequence", actions=list(actions), delay=delay)


def pipe(*funcs):
    """Pipe functions together"""

    def piped(initial):
        result = initial
        for f in funcs:
            result = f(result)
        return result

    return piped


def compose(*funcs):
    """Compose functions right-to-left"""
    return pipe(*reversed(funcs))


# Generic actions
def wait(duration: float) -> Action:
    """Wait for specified duration"""
    return action("wait", duration=duration)


def capture() -> Action:
    """Capture current state"""
    return action("capture")


def record(start: bool = True) -> Action:
    """Start or stop recording"""
    return action("record", start=start)


def parallel(*actions: Action) -> Action:
    """Execute actions in parallel"""
    return action("parallel", actions=list(actions))


def retry(a: Action, attempts: int = 3, delay: float = 1.0) -> Action:
    """Retry an action with backoff"""
    return action("retry", action=a, attempts=attempts, delay=delay)


def throttle(a: Action, rate: float) -> Action:
    """Throttle action execution rate"""
    return action("throttle", action=a, rate=rate)


def debounce(a: Action, delay: float) -> Action:
    """Debounce action execution"""
    return action("debounce", action=a, delay=delay)
