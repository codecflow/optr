"""
Tests for the simulation runner system
"""

import time

import pytest

from .clock import Clock, Null
from .runner import run


class MockSimulator:
    """Mock simulator for testing."""

    def __init__(self):
        self.step_count = 0
        self.state = {"step": 0}

    def step(self):
        """Step simulation forward."""
        self.step_count += 1
        self.state = {"step": self.step_count}
        return self.state

    def reset(self):
        """Reset to initial state."""
        self.step_count = 0
        self.state = {"step": 0}
        return self.state

    def close(self):
        """Clean up resources."""
        pass




def test_runner_with_null_clock():
    """Test runner with Null clock (fast execution)"""
    sim = MockSimulator()
    clock = Null()

    start_time = time.time()
    states = list(run(sim, steps=5, clock=clock))
    elapsed = time.time() - start_time

    assert len(states) == 5
    assert states[-1]["step"] == 5
    assert elapsed < 0.1  # Should be very fast


def test_runner_with_realtime_clock():
    """Test runner with Clock FPS control"""
    sim = MockSimulator()
    clock = Clock(fps=10, realtime=True)

    start_time = time.time()
    states = list(run(sim, steps=3, clock=clock))
    elapsed = time.time() - start_time

    expected_time = 3 / 10  # 3 steps at 10 FPS = 0.3s

    assert len(states) == 3
    assert states[-1]["step"] == 3
    assert elapsed >= expected_time * 0.8  # Allow some tolerance


def test_runner_no_clock():
    """Test runner with no clock (defaults to Null)"""
    sim = MockSimulator()

    start_time = time.time()
    states = list(run(sim, steps=3))
    elapsed = time.time() - start_time

    assert len(states) == 3
    assert states[-1]["step"] == 3
    assert elapsed < 0.1  # Should be fast without clock


def test_runner_infinite_steps():
    """Test runner with infinite steps (None)"""
    sim = MockSimulator()
    clock = Null()

    states = []
    for i, state in enumerate(run(sim, steps=None, clock=clock)):
        states.append(state)
        if i >= 4:  # Stop after 5 iterations
            break

    assert len(states) == 5
    assert states[-1]["step"] == 5


def test_runner_zero_steps():
    """Test runner with zero steps"""
    sim = MockSimulator()
    states = list(run(sim, steps=0))
    assert len(states) == 0




def test_simulator_state_progression():
    """Test that simulator state progresses correctly"""
    sim = MockSimulator()

    states = list(run(sim, steps=3))

    assert states[0]["step"] == 1
    assert states[1]["step"] == 2
    assert states[2]["step"] == 3


def test_simulator_reset():
    """Test simulator reset functionality"""
    sim = MockSimulator()

    # Step a few times
    list(run(sim, steps=3))
    assert sim.step_count == 3

    # Reset
    reset_state = sim.reset()
    assert reset_state["step"] == 0
    assert sim.step_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
