"""
Tests for MuJoCo codec module
"""

import multiprocessing as mp
import time

import mujoco
import numpy as np
import pytest

from .codec import Codec, Layout

# Simple test model XML
SIMPLE_MODEL_XML = """
<mujoco>
  <worldbody>
    <body name="box" pos="0 0 0.1">
      <joint name="slide" type="slide" axis="0 0 1"/>
      <geom name="box_geom" type="box" size="0.1 0.1 0.1" rgba="1 0 0 1"/>
    </body>
  </worldbody>
</mujoco>
"""

# Model with mocap bodies
MOCAP_MODEL_XML = """
<mujoco>
  <worldbody>
    <body name="box" pos="0 0 0.1">
      <joint name="slide" type="slide" axis="0 0 1"/>
      <geom name="box_geom" type="box" size="0.1 0.1 0.1" rgba="1 0 0 1"/>
    </body>
    <body name="mocap1" mocap="true" pos="0.5 0 0.5">
      <geom name="mocap_geom1" type="sphere" size="0.05" rgba="0 1 0 1"/>
    </body>
    <body name="mocap2" mocap="true" pos="-0.5 0 0.5">
      <geom name="mocap_geom2" type="sphere" size="0.05" rgba="0 0 1 1"/>
    </body>
  </worldbody>
</mujoco>
"""

# Complex model with multiple DOF
COMPLEX_MODEL_XML = """
<mujoco>
  <worldbody>
    <body name="arm" pos="0 0 0">
      <joint name="shoulder" type="hinge" axis="0 0 1"/>
      <geom name="upper_arm" type="capsule" size="0.05" fromto="0 0 0 0.3 0 0"/>
      <body name="forearm" pos="0.3 0 0">
        <joint name="elbow" type="hinge" axis="0 0 1"/>
        <geom name="lower_arm" type="capsule" size="0.04" fromto="0 0 0 0.25 0 0"/>
        <body name="hand" pos="0.25 0 0">
          <joint name="wrist" type="hinge" axis="0 0 1"/>
          <geom name="hand_geom" type="box" size="0.03 0.02 0.01"/>
        </body>
      </body>
    </body>
    <body name="target" mocap="true" pos="0.4 0.4 0.2">
      <geom name="target_geom" type="sphere" size="0.02" rgba="1 0 0 1"/>
    </body>
  </worldbody>
</mujoco>
"""


class TestLayout:
    """Test the Layout enum."""

    def test_layout_enum_values(self):
        """Test that Layout enum has correct values."""
        assert Layout.Render.value == (
            "qpos",
            "qvel",
            "mocap_pos",
            "mocap_quat",
            "time",
        )

    def test_layout_enum_iteration(self):
        """Test that Layout enum can be iterated."""
        fields = list(Layout.Render.value)
        expected = ["qpos", "qvel", "mocap_pos", "mocap_quat", "time"]
        assert fields == expected


class TestCodecInitialization:
    """Test codec initialization."""

    def test_codec_create_simple(self):
        """Test codec creation from simple model."""
        model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)
        codec = Codec.create(model)

        assert isinstance(codec.slices, dict)
        assert codec.length > 0
        assert codec.nbytes > 0
        assert codec.dtype == np.float64

        # Should have qpos, qvel, time (no mocap in simple model)
        assert "qpos" in codec.slices
        assert "qvel" in codec.slices
        assert "time" in codec.slices
        assert "mocap_pos" not in codec.slices
        assert "mocap_quat" not in codec.slices

    def test_codec_create_with_mocap(self):
        """Test codec creation from model with mocap bodies."""
        model = mujoco.MjModel.from_xml_string(MOCAP_MODEL_XML)
        codec = Codec.create(model)

        # Should have all fields including mocap
        assert "qpos" in codec.slices
        assert "qvel" in codec.slices
        assert "mocap_pos" in codec.slices
        assert "mocap_quat" in codec.slices
        assert "time" in codec.slices

        # Check slice sizes
        assert codec.slices["qpos"].stop - codec.slices["qpos"].start == model.nq
        assert codec.slices["qvel"].stop - codec.slices["qvel"].start == model.nv
        assert (
            codec.slices["mocap_pos"].stop - codec.slices["mocap_pos"].start
            == model.nmocap * 3
        )
        assert (
            codec.slices["mocap_quat"].stop - codec.slices["mocap_quat"].start
            == model.nmocap * 4
        )
        assert codec.slices["time"].stop - codec.slices["time"].start == 1

    def test_codec_with_custom_layout(self):
        """Test codec creation with custom layout."""
        model = mujoco.MjModel.from_xml_string(COMPLEX_MODEL_XML)
        codec = Codec.create(model, Layout.Render)

        assert "qpos" in codec.slices
        assert "qvel" in codec.slices
        assert "time" in codec.slices

    def test_codec_with_different_dtype(self):
        """Test codec creation with different dtype."""
        model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)
        codec = Codec.create(model, dtype=np.float32)

        assert codec.dtype == np.float32
        assert codec.nbytes == codec.length * 4  # float32 is 4 bytes

    def test_codec_direct_initialization(self):
        """Test direct codec initialization with slices."""
        slices = {"qpos": slice(0, 3), "qvel": slice(3, 6), "time": slice(6, 7)}
        length = 7
        codec = Codec(slices, length)

        assert codec.slices == slices
        assert codec.length == length
        assert codec.dtype == np.float64
        assert codec.nbytes == length * 8  # float64 is 8 bytes


class TestCodecEncodeDecode:
    """Test encode/decode functionality."""

    def test_encode_decode_simple_model(self):
        """Test encode/decode round trip with simple model."""
        model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)
        data = mujoco.MjData(model)
        codec = Codec.create(model)

        # Set some test values
        data.qpos[0] = 0.5
        data.qvel[0] = 1.2
        data.time = 2.5

        # Encode
        buffer = codec.empty()
        encoded = codec.encode(data, buffer)

        # Create new data and decode
        data2 = mujoco.MjData(model)
        codec.decode(encoded, data2)

        # Verify round trip
        assert np.allclose(data.qpos, data2.qpos)
        assert np.allclose(data.qvel, data2.qvel)
        assert abs(data.time - data2.time) < 1e-10

    def test_encode_decode_with_mocap(self):
        """Test encode/decode with mocap bodies."""
        model = mujoco.MjModel.from_xml_string(MOCAP_MODEL_XML)
        data = mujoco.MjData(model)
        codec = Codec.create(model)

        # Set test values including mocap
        data.qpos[0] = 0.3
        data.qvel[0] = -0.8
        data.time = 1.5
        data.mocap_pos[0] = [1.0, 2.0, 3.0]
        data.mocap_pos[1] = [4.0, 5.0, 6.0]
        data.mocap_quat[0] = [1.0, 0.0, 0.0, 0.0]
        data.mocap_quat[1] = [0.0, 1.0, 0.0, 0.0]

        # Encode/decode
        buffer = codec.empty()
        encoded = codec.encode(data, buffer)

        data2 = mujoco.MjData(model)
        codec.decode(encoded, data2)

        # Verify all fields
        assert np.allclose(data.qpos, data2.qpos)
        assert np.allclose(data.qvel, data2.qvel)
        assert np.allclose(data.mocap_pos, data2.mocap_pos)
        assert np.allclose(data.mocap_quat, data2.mocap_quat)
        assert abs(data.time - data2.time) < 1e-10

    def test_encode_decode_complex_model(self):
        """Test encode/decode with complex multi-DOF model."""
        model = mujoco.MjModel.from_xml_string(COMPLEX_MODEL_XML)
        data = mujoco.MjData(model)
        codec = Codec.create(model)

        # Set random joint positions and velocities
        data.qpos[:] = np.random.randn(model.nq) * 0.5
        data.qvel[:] = np.random.randn(model.nv) * 0.2
        data.time = np.random.rand() * 10

        # Set mocap data
        if model.nmocap > 0:
            data.mocap_pos[:] = np.random.randn(model.nmocap, 3)
            data.mocap_quat[:] = np.random.randn(model.nmocap, 4)
            # Normalize quaternions
            for i in range(model.nmocap):
                data.mocap_quat[i] /= np.linalg.norm(data.mocap_quat[i])

        # Encode/decode
        buffer = codec.empty()
        encoded = codec.encode(data, buffer)

        data2 = mujoco.MjData(model)
        codec.decode(encoded, data2)

        # Verify round trip
        assert np.allclose(data.qpos, data2.qpos, rtol=1e-10)
        assert np.allclose(data.qvel, data2.qvel, rtol=1e-10)
        if model.nmocap > 0:
            assert np.allclose(data.mocap_pos, data2.mocap_pos, rtol=1e-10)
            assert np.allclose(data.mocap_quat, data2.mocap_quat, rtol=1e-10)
        assert abs(data.time - data2.time) < 1e-10

    def test_buffer_reuse(self):
        """Test that buffers can be reused efficiently."""
        model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)
        data = mujoco.MjData(model)
        codec = Codec.create(model)

        # Create buffer once
        buffer = codec.empty()
        buffer_id = id(buffer)

        # Use same buffer multiple times
        for i in range(5):
            data.qpos[0] = i * 0.1
            data.time = i * 0.5

            encoded = codec.encode(data, buffer)
            assert id(encoded) == buffer_id  # Same buffer object

            # Verify encoding worked
            data2 = mujoco.MjData(model)
            codec.decode(encoded, data2)
            assert abs(data.qpos[0] - data2.qpos[0]) < 1e-10
            assert abs(data.time - data2.time) < 1e-10

    def test_encode_without_buffer(self):
        """Test encoding with fresh buffer."""
        model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)
        data = mujoco.MjData(model)
        codec = Codec.create(model)

        data.qpos[0] = 0.7
        data.time = 3.2

        # Encode with fresh buffer
        encoded = codec.encode(data, codec.empty())

        assert isinstance(encoded, np.ndarray)
        assert encoded.shape == (codec.length,)
        assert encoded.dtype == codec.dtype

        # Verify decoding works
        data2 = mujoco.MjData(model)
        codec.decode(encoded, data2)
        assert abs(data.qpos[0] - data2.qpos[0]) < 1e-10


class TestCodecPerformance:
    """Test codec performance characteristics."""

    def test_encode_decode_performance(self):
        """Test encode/decode performance."""
        model = mujoco.MjModel.from_xml_string(COMPLEX_MODEL_XML)
        data = mujoco.MjData(model)
        codec = Codec.create(model)
        buffer = codec.empty()

        # Warm up
        for _ in range(10):
            codec.encode(data, buffer)
            codec.decode(buffer, data)

        # Time encode operations
        start_time = time.perf_counter()
        for _ in range(1000):
            codec.encode(data, buffer)
        encode_time = time.perf_counter() - start_time

        # Time decode operations
        start_time = time.perf_counter()
        for _ in range(1000):
            codec.decode(buffer, data)
        decode_time = time.perf_counter() - start_time

        # Should be very fast (< 10 microseconds per operation)
        avg_encode_time = encode_time / 1000
        avg_decode_time = decode_time / 1000

        print(f"Average encode time: {avg_encode_time * 1e6:.2f} μs")
        print(f"Average decode time: {avg_decode_time * 1e6:.2f} μs")

        # Performance assertions (generous bounds)
        assert avg_encode_time < 50e-6  # < 50 microseconds
        assert avg_decode_time < 50e-6  # < 50 microseconds


class TestCodecEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_model(self):
        """Test codec with minimal model."""
        model_xml = """
        <mujoco>
          <worldbody>
            <geom name="ground" type="plane" size="1 1 0.1"/>
          </worldbody>
        </mujoco>
        """
        model = mujoco.MjModel.from_xml_string(model_xml)
        codec = Codec.create(model)

        # Should work even with no DOF
        assert codec.length >= 1  # At least time
        assert "time" in codec.slices

    def test_model_without_mocap(self):
        """Test codec with model that has no mocap bodies."""
        model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)
        codec = Codec.create(model)

        # Should not have mocap fields
        assert "mocap_pos" not in codec.slices
        assert "mocap_quat" not in codec.slices

        # Should still work for encode/decode
        data = mujoco.MjData(model)
        buffer = codec.empty()
        encoded = codec.encode(data, buffer)

        data2 = mujoco.MjData(model)
        codec.decode(encoded, data2)

        assert np.allclose(data.qpos, data2.qpos)
        assert np.allclose(data.qvel, data2.qvel)

    def test_different_dtypes(self):
        """Test codec with different data types."""
        model = mujoco.MjModel.from_xml_string(SIMPLE_MODEL_XML)

        for dtype in [np.float32, np.float64]:
            codec = Codec.create(model, dtype=dtype)
            data = mujoco.MjData(model)

            data.qpos[0] = 0.5
            data.time = 1.5

            buffer = codec.empty()
            assert buffer.dtype == dtype

            encoded = codec.encode(data, buffer)
            assert encoded.dtype == dtype

            data2 = mujoco.MjData(model)
            codec.decode(encoded, data2)

            # Allow for dtype precision differences
            rtol = 1e-6 if dtype == np.float32 else 1e-10
            assert np.allclose(data.qpos, data2.qpos, rtol=rtol)
            assert abs(data.time - data2.time) < rtol


def _producer_process(shared_array, model_xml, iterations):
    """Producer process for cross-process testing."""
    model = mujoco.MjModel.from_xml_string(model_xml)
    data = mujoco.MjData(model)
    codec = Codec.create(model)

    # Create numpy array from shared memory
    buffer = np.frombuffer(shared_array.get_obj(), dtype=np.float64)

    for i in range(iterations):
        # Update simulation state
        data.qpos[:] = np.sin(i * 0.1) * 0.5
        data.qvel[:] = np.cos(i * 0.1) * 0.2
        data.time = i * 0.01

        if model.nmocap > 0:
            data.mocap_pos[0] = [np.sin(i * 0.1), np.cos(i * 0.1), 0.5]
            data.mocap_quat[0] = [1.0, 0.0, 0.0, 0.0]

        # Step simulation
        mujoco.mj_step(model, data)

        # Encode to shared memory
        codec.encode(data, buffer)

        time.sleep(0.001)  # Small delay


def _consumer_process(shared_array, model_xml, iterations, results_queue):
    """Consumer process for cross-process testing."""
    model = mujoco.MjModel.from_xml_string(model_xml)
    data = mujoco.MjData(model)
    codec = Codec.create(model)

    # Create numpy array from shared memory
    buffer = np.frombuffer(shared_array.get_obj(), dtype=np.float64)

    decoded_states = []

    for _i in range(iterations):
        # Decode from shared memory
        codec.decode(buffer, data)

        # Store decoded state
        state = {
            "qpos": data.qpos.copy(),
            "qvel": data.qvel.copy(),
            "time": data.time,
        }

        if model.nmocap > 0:
            state["mocap_pos"] = data.mocap_pos.copy()
            state["mocap_quat"] = data.mocap_quat.copy()

        decoded_states.append(state)

        time.sleep(0.001)  # Small delay

    results_queue.put(decoded_states)


class TestCodecCrossProcess:
    """Test codec functionality across processes."""

    def test_cross_process_simple(self):
        """Test codec communication between processes with simple model."""
        model_xml = SIMPLE_MODEL_XML
        model = mujoco.MjModel.from_xml_string(model_xml)
        codec = Codec.create(model)
        iterations = 10

        # Create shared memory array
        shared_array = mp.Array("d", codec.length)  # 'd' for double (float64)
        results_queue = mp.Queue()

        # Start consumer process
        consumer = mp.Process(
            target=_consumer_process,
            args=(shared_array, model_xml, iterations, results_queue),
        )
        consumer.start()

        # Start producer process
        producer = mp.Process(
            target=_producer_process, args=(shared_array, model_xml, iterations)
        )
        producer.start()

        # Wait for completion
        producer.join(timeout=10)
        consumer.join(timeout=10)

        # Get results
        decoded_states = results_queue.get()

        assert len(decoded_states) == iterations

        # Verify that states were transmitted correctly
        for _i, state in enumerate(decoded_states):
            # Check that values are reasonable (not exact due to timing)
            assert len(state["qpos"]) == model.nq
            assert len(state["qvel"]) == model.nv
            assert state["time"] >= 0
            assert np.all(np.abs(state["qpos"]) <= 1.0)  # Reasonable bounds
            assert np.all(np.abs(state["qvel"]) <= 1.0)  # Reasonable bounds

    def test_cross_process_with_mocap(self):
        """Test codec communication with mocap bodies."""
        model_xml = MOCAP_MODEL_XML
        model = mujoco.MjModel.from_xml_string(model_xml)
        codec = Codec.create(model)
        iterations = 5

        # Create shared memory array
        shared_array = mp.Array("d", codec.length)
        results_queue = mp.Queue()

        # Start processes
        consumer = mp.Process(
            target=_consumer_process,
            args=(shared_array, model_xml, iterations, results_queue),
        )
        consumer.start()

        producer = mp.Process(
            target=_producer_process, args=(shared_array, model_xml, iterations)
        )
        producer.start()

        # Wait for completion
        producer.join(timeout=10)
        consumer.join(timeout=10)

        # Get results
        decoded_states = results_queue.get()

        assert len(decoded_states) == iterations

        # Verify mocap data was transmitted
        for state in decoded_states:
            assert "mocap_pos" in state
            assert "mocap_quat" in state
            assert state["mocap_pos"].shape == (model.nmocap, 3)
            assert state["mocap_quat"].shape == (model.nmocap, 4)

    def test_high_frequency_cross_process(self):
        """Test high-frequency cross-process communication."""
        model_xml = SIMPLE_MODEL_XML
        model = mujoco.MjModel.from_xml_string(model_xml)
        codec = Codec.create(model)
        iterations = 100  # Higher frequency test

        shared_array = mp.Array("d", codec.length)
        results_queue = mp.Queue()

        start_time = time.time()

        # Start processes
        consumer = mp.Process(
            target=_consumer_process,
            args=(shared_array, model_xml, iterations, results_queue),
        )
        consumer.start()

        producer = mp.Process(
            target=_producer_process, args=(shared_array, model_xml, iterations)
        )
        producer.start()

        # Wait for completion
        producer.join(timeout=30)
        consumer.join(timeout=30)

        end_time = time.time()
        total_time = end_time - start_time

        # Get results
        decoded_states = results_queue.get()

        assert len(decoded_states) == iterations

        # Performance check - should handle 100 iterations reasonably fast
        assert total_time < 20  # Should complete within 20 seconds

        frequency = iterations / total_time
        print(f"Cross-process communication frequency: {frequency:.1f} Hz")

        # Should achieve reasonable frequency
        assert frequency > 5  # At least 5 Hz


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
