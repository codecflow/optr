"""
Tests for MuJoCo renderer
"""

import mujoco
import numpy as np
import pytest

from .codec import Codec
from .renderer import Renderer

# Simple test model XML
SIMPLE_MODEL_XML = """
<mujoco>
  <visual>
    <global offwidth="2048" offheight="2048"/>
  </visual>
  <worldbody>
    <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
    <body name="box" pos="0 0 0.1">
      <geom name="box_geom" type="box" size="0.1 0.1 0.1" rgba="1 0 0 1"/>
    </body>
    <camera name="fixed" pos="0.5 0.5 0.5" xyaxes="0 -1 0 0 0 1"/>
  </worldbody>
</mujoco>
"""

# Model with multiple cameras
MULTI_CAMERA_MODEL_XML = """
<mujoco>
  <visual>
    <global offwidth="2048" offheight="2048"/>
  </visual>
  <worldbody>
    <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
    <body name="sphere" pos="0 0 0.1">
      <geom name="sphere_geom" type="sphere" size="0.1" rgba="0 1 0 1"/>
    </body>
    <camera name="front" pos="0.3 0 0.2" xyaxes="0 -1 0 0 0 1"/>
    <camera name="side" pos="0 0.3 0.2" xyaxes="-1 0 0 0 0 1"/>
  </worldbody>
</mujoco>
"""


def test_renderer_initialization():
    """Test renderer initialization with real MuJoCo model."""
    model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)
    renderer = Renderer(model, width=320, height=240)

    assert renderer.model == model
    assert renderer.width == 320
    assert renderer.height == 240
    assert renderer.buffer.shape == (240, 320, 3)
    assert renderer.buffer.dtype == np.uint8

    renderer.close()


def test_renderer_default_dimensions():
    """Test renderer with default dimensions."""
    model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)
    renderer = Renderer(model)

    assert renderer.width == 1920
    assert renderer.height == 1080
    assert renderer.buffer.shape == (1080, 1920, 3)

    renderer.close()


def test_render_basic():
    """Test basic rendering functionality."""
    model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)
    data = mujoco.MjData(model)
    renderer = Renderer(model, width=160, height=120)

    frame = renderer.render(data)

    assert isinstance(frame, np.ndarray)
    assert frame.shape == (120, 160, 3)
    assert frame.dtype == np.uint8
    # Just verify we get a valid frame (may be black due to lighting/camera)

    renderer.close()


def test_render_with_named_camera():
    """Test rendering with named camera."""
    model = mujoco.MjModel.from_xml_string(MULTI_CAMERA_MODEL_XML)
    data = mujoco.MjData(model)
    renderer = Renderer(model, width=160, height=120)

    # Render with front camera
    frame_front = renderer.render(data, camera="front")

    # Render with side camera
    frame_side = renderer.render(data, camera="side")

    assert frame_front.shape == (120, 160, 3)
    assert frame_side.shape == (120, 160, 3)

    # Both should be valid frames (content may be same if cameras see nothing)

    renderer.close()


def test_render_with_camera_id():
    """Test rendering with camera ID."""
    model = mujoco.MjModel.from_xml_string(MULTI_CAMERA_MODEL_XML)
    data = mujoco.MjData(model)
    renderer = Renderer(model, width=160, height=120)

    # Render with camera ID 0 (front)
    frame_0 = renderer.render(data, camera=0)

    # Render with camera ID 1 (side)
    frame_1 = renderer.render(data, camera=1)

    assert frame_0.shape == (120, 160, 3)
    assert frame_1.shape == (120, 160, 3)

    # Both should be valid frames

    renderer.close()


def test_render_free_camera():
    """Test rendering with free camera (default)."""
    model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)
    data = mujoco.MjData(model)
    renderer = Renderer(model, width=160, height=120)

    # Render with free camera (camera=-1)
    frame = renderer.render(data, camera=-1)

    assert frame.shape == (120, 160, 3)
    # Just verify we get a valid frame

    renderer.close()


def test_buffer_reuse():
    """Test that internal buffer is reused across renders."""
    model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)
    data = mujoco.MjData(model)
    renderer = Renderer(model, width=160, height=120)

    # First render
    frame1 = renderer.render(data)
    buffer_id1 = id(frame1)

    # Second render should reuse the same buffer
    frame2 = renderer.render(data)
    buffer_id2 = id(frame2)

    assert buffer_id1 == buffer_id2  # Same buffer object

    renderer.close()


def test_render_with_dynamics():
    """Test rendering after forward dynamics."""
    model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)
    data = mujoco.MjData(model)
    renderer = Renderer(model, width=160, height=120)

    # Initial render
    frame1 = renderer.render(data)

    # Step simulation forward
    mujoco.mj_step(model, data)

    # Render after step
    frame2 = renderer.render(data)

    assert frame1.shape == frame2.shape
    # Both should be valid renders (may be black due to lighting/camera)

    renderer.close()


def test_shared_memory_workflow():
    """Test renderer with shared memory workflow using codec."""
    # Use a model with degrees of freedom for codec testing
    model_xml = """
    <mujoco>
      <visual>
        <global offwidth="2048" offheight="2048"/>
      </visual>
      <worldbody>
        <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
        <body name="box" pos="0 0 1">
          <joint name="slide" type="slide" axis="0 0 1"/>
          <geom name="box_geom" type="box" size="0.1 0.1 0.1" rgba="1 0 0 1"/>
        </body>
      </worldbody>
    </mujoco>
    """

    model = mujoco.MjModel.from_xml_string(model_xml)

    # Create codec for serialization
    codec = Codec.create(model)

    # Source data (simulates main simulation process)
    source_data = mujoco.MjData(model)
    mujoco.mj_step(model, source_data)  # Advance simulation

    # Encode state (simulates writing to shared memory)
    buffer = codec.empty()
    encoded = codec.encode(source_data, buffer)

    # Target data (simulates renderer process)
    target_data = mujoco.MjData(model)

    # Decode state (simulates reading from shared memory)
    codec.decode(encoded, target_data)

    # Forward dynamics to update derived quantities
    mujoco.mj_forward(model, target_data)

    # Render the decoded state
    renderer = Renderer(model, width=160, height=120)
    frame = renderer.render(target_data)

    assert frame.shape == (120, 160, 3)
    # Just verify we get a valid frame (may be black due to lighting/camera)

    # Verify that source and target have same state
    assert np.allclose(source_data.qpos, target_data.qpos)
    assert np.allclose(source_data.qvel, target_data.qvel)
    assert abs(source_data.time - target_data.time) < 1e-10

    renderer.close()


def test_close_cleanup():
    """Test that close method cleans up resources."""
    model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)
    renderer = Renderer(model, width=160, height=120)

    # Verify renderer is working
    data = mujoco.MjData(model)
    frame = renderer.render(data)
    assert frame.shape == (120, 160, 3)

    # Close and verify cleanup
    renderer.close()
    assert renderer.renderer is None
    assert renderer.buffer is None


def test_render_after_close():
    """Test that rendering after close raises appropriate error."""
    model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)
    data = mujoco.MjData(model)
    renderer = Renderer(model, width=160, height=120)

    renderer.close()

    with pytest.raises(AttributeError):
        renderer.render(data)


def test_invalid_camera_name():
    """Test handling of invalid camera name."""
    model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)
    data = mujoco.MjData(model)
    renderer = Renderer(model, width=160, height=120)

    # Should handle invalid camera name gracefully (resolve returns None)
    frame = renderer.render(data, camera="nonexistent")
    assert frame.shape == (120, 160, 3)

    renderer.close()


def test_context_manager():
    """Test renderer as context manager."""
    model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)
    data = mujoco.MjData(model)

    with Renderer(model, width=160, height=120) as renderer:
        frame = renderer.render(data)
        assert frame.shape == (120, 160, 3)

    # Should be closed after context
    assert renderer.renderer is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
