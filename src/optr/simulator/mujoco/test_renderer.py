"""
Tests for MuJoCo renderer
"""

from unittest.mock import Mock, patch

import numpy as np
import pytest

from .renderer import Renderer


class MockSimulation:
    """Mock MuJoCo simulation for testing."""

    def __init__(self, time=0.0):
        self.state = Mock()
        self.state.model = Mock()
        self.state.data = Mock()
        self.state.data.time = time


class MockMujocoRenderer:
    """Mock MuJoCo renderer for testing."""

    def __init__(self, model, height, width):
        self.model = model
        self.height = height
        self.width = width
        self.update_scene_calls = []
        self.render_calls = 0

    def update_scene(self, data, camera=None):
        """Mock update_scene method."""
        self.update_scene_calls.append((data, camera))

    def render(self):
        """Mock render method."""
        self.render_calls += 1
        # Return a mock RGB array
        return np.zeros((self.height, self.width, 3), dtype=np.uint8)


@patch("optr.simulator.mujoco.renderer.mujoco")
@patch("optr.simulator.mujoco.renderer.resolve")
def test_renderer_initialization(mock_resolve, mock_mujoco):
    """Test renderer initialization."""
    mock_resolve.return_value = 0
    mock_mujoco.Renderer = MockMujocoRenderer

    simulation = MockSimulation()
    renderer = Renderer(simulation, width=640, height=480, camera="front")

    assert renderer.simulation == simulation
    assert renderer.width == 640
    assert renderer.height == 480
    assert renderer.model == simulation.state.model
    assert renderer.camera == 0
    assert isinstance(renderer.cache, dict)

    mock_resolve.assert_called_once_with(simulation.state.model, "front")


@patch("optr.simulator.mujoco.renderer.mujoco")
@patch("optr.simulator.mujoco.renderer.resolve")
def test_renderer_default_values(mock_resolve, mock_mujoco):
    """Test renderer with default values."""
    mock_resolve.return_value = None
    mock_mujoco.Renderer = MockMujocoRenderer

    simulation = MockSimulation()
    renderer = Renderer(simulation)

    assert renderer.width == 1920
    assert renderer.height == 1080
    assert renderer.camera is None


@patch("optr.simulator.mujoco.renderer.mujoco")
@patch("optr.simulator.mujoco.renderer.resolve")
def test_render_basic(mock_resolve, mock_mujoco):
    """Test basic rendering functionality."""
    mock_resolve.return_value = 0
    mock_mujoco.Renderer = MockMujocoRenderer

    simulation = MockSimulation(time=1.0)
    renderer = Renderer(simulation, width=320, height=240)

    frame = renderer.render()

    assert isinstance(frame, np.ndarray)
    assert frame.shape == (240, 320, 3)
    assert len(renderer.renderer.update_scene_calls) == 1
    assert renderer.renderer.render_calls == 1


@patch("optr.simulator.mujoco.renderer.mujoco")
@patch("optr.simulator.mujoco.renderer.resolve")
def test_render_with_camera_parameter(mock_resolve, mock_mujoco):
    """Test rendering with camera parameter."""
    mock_resolve.side_effect = [0, 1]  # First call for init, second for render
    mock_mujoco.Renderer = MockMujocoRenderer

    simulation = MockSimulation(time=1.0)
    renderer = Renderer(simulation, camera="front")

    renderer.render(camera="back")

    # Should resolve camera parameter for render call
    assert mock_resolve.call_count == 2
    assert renderer.renderer.update_scene_calls[0][1] == 1  # camera=1 from "back"


@patch("optr.simulator.mujoco.renderer.mujoco")
@patch("optr.simulator.mujoco.renderer.resolve")
def test_render_with_none_camera(mock_resolve, mock_mujoco):
    """Test rendering when camera resolves to None."""
    mock_resolve.return_value = None
    mock_mujoco.Renderer = MockMujocoRenderer

    simulation = MockSimulation(time=1.0)
    renderer = Renderer(simulation)

    renderer.render()

    # Should default to -1 (free camera) when camera is None
    assert renderer.renderer.update_scene_calls[0][1] == -1


@patch("optr.simulator.mujoco.renderer.mujoco")
@patch("optr.simulator.mujoco.renderer.resolve")
def test_render_caching(mock_resolve, mock_mujoco):
    """Test that rendering results are cached by time."""
    mock_resolve.return_value = 0
    mock_mujoco.Renderer = MockMujocoRenderer

    simulation = MockSimulation(time=1.0)
    renderer = Renderer(simulation)

    # First render
    frame1 = renderer.render()
    assert renderer.renderer.render_calls == 1

    # Second render with same time should use cache
    frame2 = renderer.render()
    assert renderer.renderer.render_calls == 1  # No additional render call
    assert np.array_equal(frame1, frame2)

    # Change time and render again
    simulation.state.data.time = 2.0
    renderer.render()
    assert renderer.renderer.render_calls == 2  # New render call


@patch("optr.simulator.mujoco.renderer.mujoco")
@patch("optr.simulator.mujoco.renderer.resolve")
def test_render_camera_specific_caching(mock_resolve, mock_mujoco):
    """Test that caching is camera-specific."""
    mock_resolve.side_effect = [
        0,
        0,
        1,
        0,
    ]  # init, render cam 0, render cam 1, render cam 0 again
    mock_mujoco.Renderer = MockMujocoRenderer

    simulation = MockSimulation(time=1.0)
    renderer = Renderer(simulation)

    # Render with camera 0
    renderer.render(camera=0)
    assert renderer.renderer.render_calls == 1

    # Render with camera 1 (different camera, same time)
    renderer.render(camera=1)
    assert renderer.renderer.render_calls == 2  # New render call

    # Render with camera 0 again (should use cache)
    renderer.render(camera=0)
    assert renderer.renderer.render_calls == 2  # No additional render call


@patch("optr.simulator.mujoco.renderer.mujoco")
@patch("optr.simulator.mujoco.renderer.resolve")
def test_close_cleanup(mock_resolve, mock_mujoco):
    """Test that close method cleans up resources."""
    mock_resolve.return_value = 0
    mock_mujoco.Renderer = MockMujocoRenderer

    simulation = MockSimulation()
    renderer = Renderer(simulation)

    # Add some cache data
    renderer.render()
    assert len(renderer.cache) > 0

    # Close and verify cleanup
    renderer.close()
    assert renderer.renderer is None
    assert renderer.cache is None


@patch("optr.simulator.mujoco.renderer.mujoco")
@patch("optr.simulator.mujoco.renderer.resolve")
def test_render_after_close(mock_resolve, mock_mujoco):
    """Test that rendering after close raises appropriate error."""
    mock_resolve.return_value = 0
    mock_mujoco.Renderer = MockMujocoRenderer

    simulation = MockSimulation()
    renderer = Renderer(simulation)
    renderer.close()

    with pytest.raises(AttributeError):
        renderer.render()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
