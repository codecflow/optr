"""
Tests for the clock timing system
"""

import time

import pytest

from .clock import Clock, Null


def test_clock_creation():
    """Test basic clock creation"""
    clock = Clock(fps=30, realtime=True)
    assert clock.fps == 30
    assert clock.realtime is True
    assert clock.duration == 1.0 / 30


def test_clock_with_no_fps():
    """Test clock with no FPS limit"""
    clock = Clock(fps=None, realtime=True)
    assert clock.fps is None
    assert clock.duration == 0


def test_clock_non_realtime():
    """Test clock with realtime disabled"""
    clock = Clock(fps=30, realtime=False)
    assert clock.realtime is False

    # tick and sync should do nothing when not realtime
    start_time = time.time()
    clock.tick()
    clock.sync()
    elapsed = time.time() - start_time
    assert elapsed < 0.01  # Should be very fast


def test_clock_timing_control():
    """Test clock FPS timing control"""
    clock = Clock(fps=10, realtime=True)
    
    start_time = time.time()
    clock.tick()
    clock.sync()
    elapsed = time.time() - start_time
    
    expected_duration = 1.0 / 10  # 0.1 seconds
    assert elapsed >= expected_duration * 0.8  # Allow some tolerance


def test_clock_fast_execution():
    """Test clock doesn't delay when execution is already slow"""
    clock = Clock(fps=1000, realtime=True)  # Very high FPS
    
    start_time = time.time()
    clock.tick()
    # Simulate slow work
    time.sleep(0.01)
    clock.sync()
    elapsed = time.time() - start_time
    
    # Should not add additional delay since work already took longer than frame time
    assert elapsed < 0.02


def test_null_clock_creation():
    """Test Null clock creation"""
    clock = Null()
    # Should have tick and sync methods that do nothing
    clock.tick()
    clock.sync()


def test_null_clock_performance():
    """Test Null clock has no timing overhead"""
    clock = Null()
    
    start_time = time.time()
    for _ in range(100):
        clock.tick()
        clock.sync()
    elapsed = time.time() - start_time
    
    assert elapsed < 0.01  # Should be very fast


def test_clock_zero_fps():
    """Test clock with zero FPS"""
    with pytest.raises(ValueError):
        Clock(fps=0, realtime=True)


def test_clock_negative_fps():
    """Test clock with negative FPS"""
    with pytest.raises(ValueError):
        Clock(fps=-10, realtime=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
