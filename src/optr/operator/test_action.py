"""
Tests for the action system
"""

import pytest

from .action import (
    Action,
    action,
    batch,
    capture,
    chain,
    compose,
    debounce,
    parallel,
    pipe,
    record,
    retry,
    sequence,
    throttle,
    wait,
)


def test_action_creation():
    """Test basic action creation"""
    a = action("click", x=100, y=200)
    assert a.type == "click"
    assert a.x == 100
    assert a.y == 200


def test_action_spread_params():
    """Test spreading params"""
    a = action("move", joint="arm", position=[1, 2, 3], speed=0.5)
    assert a.type == "move"
    assert a.joint == "arm"
    assert a.position == [1, 2, 3]
    assert a.speed == 0.5


def test_chain():
    """Test chaining actions"""
    a1 = action("click", x=100, y=200)
    a2 = action("type", text="hello")
    a3 = action("wait", duration=1)

    result = chain(a1, a2, a3)
    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0].type == "click"
    assert result[1].type == "type"
    assert result[2].type == "wait"


def test_batch():
    """Test batching actions for parallel execution"""
    a1 = action("fetch", url="api/1")
    a2 = action("fetch", url="api/2")

    result = batch(a1, a2)
    assert result.type == "batch"
    assert len(result.actions) == 2
    assert result.actions[0].url == "api/1"


def test_sequence():
    """Test creating action sequences"""
    a1 = action("click", x=100)
    a2 = action("type", text="test")

    result = sequence(a1, a2, delay=0.5)
    assert result.type == "sequence"
    assert result.delay == 0.5
    assert len(result.actions) == 2


def test_pipe():
    """Test pipe function composition"""

    def add_one(x):
        return x + 1

    def multiply_two(x):
        return x * 2

    piped = pipe(add_one, multiply_two)
    assert piped(5) == 12  # (5 + 1) * 2


def test_compose():
    """Test compose function (right-to-left)"""

    def add_one(x):
        return x + 1

    def multiply_two(x):
        return x * 2

    composed = compose(add_one, multiply_two)
    assert composed(5) == 11  # (5 * 2) + 1


def test_wait():
    """Test wait action"""
    a = wait(2.5)
    assert a.type == "wait"
    assert a.duration == 2.5


def test_capture():
    """Test capture action"""
    a = capture()
    assert a.type == "capture"


def test_record():
    """Test record action"""
    start = record(start=True)
    assert start.type == "record"
    assert start.start is True

    stop = record(start=False)
    assert stop.start is False


def test_parallel():
    """Test parallel action execution"""
    a1 = action("task1")
    a2 = action("task2")

    result = parallel(a1, a2)
    assert result.type == "parallel"
    assert len(result.actions) == 2


def test_retry():
    """Test retry action with backoff"""
    a = action("api_call", endpoint="/data")

    result = retry(a, attempts=5, delay=2.0)
    assert result.type == "retry"
    assert result.action.type == "api_call"
    assert result.attempts == 5
    assert result.delay == 2.0


def test_throttle():
    """Test throttle action"""
    a = action("scroll")

    result = throttle(a, rate=0.1)
    assert result.type == "throttle"
    assert result.action.type == "scroll"
    assert result.rate == 0.1


def test_debounce():
    """Test debounce action"""
    a = action("search", query="test")

    result = debounce(a, delay=0.3)
    assert result.type == "debounce"
    assert result.action.query == "test"
    assert result.delay == 0.3


def test_action_type_annotation():
    """Test that Action type works correctly"""

    def execute(a: Action) -> str:
        return a.type

    a = action("test", value=42)
    assert execute(a) == "test"


def test_nested_actions():
    """Test nesting actions within actions"""
    inner = chain(action("step1"), action("step2"))

    outer = sequence(action("setup"), batch(*inner), action("cleanup"))

    assert outer.type == "sequence"
    assert len(outer.actions) == 3
    assert outer.actions[1].type == "batch"


def test_empty_action():
    """Test action with no params"""
    a = action("noop")
    assert a.type == "noop"
    assert hasattr(a, "type")


def test_action_with_complex_params():
    """Test action with nested complex params"""
    a = action(
        "complex",
        config={"timeout": 30, "retries": 3},
        data=[1, 2, 3],
        nested={"deep": {"value": "test"}},
    )

    assert a.type == "complex"
    assert a.config["timeout"] == 30
    assert a.data == [1, 2, 3]
    assert a.nested["deep"]["value"] == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
