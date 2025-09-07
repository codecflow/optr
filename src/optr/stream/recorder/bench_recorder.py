"""Consolidated benchmarks for the queue-based recorder."""

import tempfile

import numpy as np
import pytest

from .recorder import Recorder
from .test_helpers import (
    create_gradient_frame,
    create_random_frame,
    create_solid_frame,
    create_test_frame,
)


@pytest.mark.benchmark
class TestRecorderBenchmarks:
    """Core recorder operation benchmarks."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.recorder = Recorder(
            output_dir=self.temp_dir, width=640, height=480, fps=30.0
        )

    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(self, "recorder") and self.recorder:
            try:
                self.recorder.close()
            except Exception as e:
                print(f"Warning: Error during recorder cleanup: {e}")
            finally:
                self.recorder = None

    def test_benchmark_frame_addition(self, benchmark):
        """Benchmark single frame addition performance."""
        action_id = "benchmark_frame_test"
        self.recorder.start_recording(action_id)

        frame_bytes = create_test_frame()

        # Benchmark the frame addition
        benchmark(self.recorder.add_frame, frame_bytes)

        self.recorder.stop_recording(action_id)

    def test_benchmark_start_recording(self, benchmark):
        """Benchmark recording start performance."""
        action_id = "benchmark_start_test"

        def start_recording():
            self.recorder.start_recording(action_id)
            # Clean up for next iteration
            if self.recorder.is_recording:
                self.recorder.stop_recording(action_id)

        benchmark(start_recording)

    def test_benchmark_stop_recording(self, benchmark):
        """Benchmark recording stop performance."""
        action_id = "benchmark_stop_test"

        def stop_recording():
            # Start recording first
            self.recorder.start_recording(action_id)
            # Add a frame to make it realistic
            frame_bytes = create_test_frame()
            self.recorder.add_frame(frame_bytes)
            # Benchmark the stop operation
            self.recorder.stop_recording(action_id)

        benchmark(stop_recording)

    def test_benchmark_recording_lifecycle(self, benchmark):
        """Benchmark complete recording lifecycle."""
        action_id = "benchmark_lifecycle_test"

        def recording_lifecycle():
            self.recorder.start_recording(action_id)

            # Add 10 frames
            for i in range(10):
                frame_bytes = create_test_frame(i)
                self.recorder.add_frame(frame_bytes)

            self.recorder.stop_recording(action_id)

        benchmark(recording_lifecycle)

    def test_benchmark_concurrent_frame_addition(self, benchmark):
        """Benchmark concurrent frame additions."""
        action_id = "benchmark_concurrent_test"
        self.recorder.start_recording(action_id)

        frames = [create_test_frame(i) for i in range(5)]

        def add_multiple_frames():
            for frame_bytes in frames:
                self.recorder.add_frame(frame_bytes)

        benchmark(add_multiple_frames)

        self.recorder.stop_recording(action_id)

    def test_benchmark_get_recording_status(self, benchmark):
        """Benchmark recording status retrieval."""
        action_id = "benchmark_status_test"
        self.recorder.start_recording(action_id)

        benchmark(self.recorder.get_recording_status, action_id)

        self.recorder.stop_recording(action_id)

    def test_benchmark_list_recordings(self, benchmark):
        """Benchmark listing all recordings."""
        # Create multiple recordings
        for i in range(5):
            action_id = f"benchmark_list_test_{i}"
            self.recorder.start_recording(action_id)
            frame_bytes = create_test_frame(i)
            self.recorder.add_frame(frame_bytes)

        benchmark(self.recorder.list_recordings)

        # Clean up
        for i in range(5):
            action_id = f"benchmark_list_test_{i}"
            self.recorder.stop_recording(action_id)

    @pytest.mark.parametrize(
        "resolution",
        [
            (320, 240),  # Small
            (640, 480),  # Medium
            (1280, 720),  # HD
        ],
    )
    def test_benchmark_different_resolutions(self, benchmark, resolution):
        """Benchmark recording with different resolutions."""
        width, height = resolution
        recorder = Recorder(
            output_dir=self.temp_dir, width=width, height=height, fps=30.0
        )

        try:
            action_id = f"benchmark_resolution_{width}x{height}_test"
            num_frames = 20

            # Pre-create frames
            frames = []
            for i in range(num_frames):
                frame = np.zeros((height, width, 3), dtype=np.uint8)
                frame[:, :] = [i % 256, (i * 2) % 256, (i * 3) % 256]
                frames.append(frame.tobytes())

            def record_frames():
                recorder.start_recording(action_id)
                for frame_bytes in frames:
                    recorder.add_frame(frame_bytes)
                recorder.stop_recording(action_id)

            benchmark(record_frames)

        finally:
            recorder.close()

    @pytest.mark.parametrize("fps", [24.0, 30.0, 60.0])
    def test_benchmark_different_fps_settings(self, benchmark, fps):
        """Benchmark recorder with different FPS settings."""
        recorder = Recorder(output_dir=self.temp_dir, width=640, height=480, fps=fps)

        try:
            action_id = f"benchmark_fps_{int(fps)}_test"

            def test_fps_recording():
                recorder.start_recording(action_id)

                # Add 10 frames
                for i in range(10):
                    frame_bytes = create_test_frame(i)
                    recorder.add_frame(frame_bytes)

                recorder.stop_recording(action_id)

            benchmark(test_fps_recording)

        finally:
            recorder.close()


@pytest.mark.benchmark
class TestFrameProcessingBenchmarks:
    """Frame creation and processing benchmarks."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up after tests."""
        pass

    def test_benchmark_frame_creation_baseline(self, benchmark):
        """Benchmark test frame creation (baseline)."""
        benchmark(create_test_frame, 42)

    @pytest.mark.parametrize(
        "width,height",
        [
            (320, 240),  # Small
            (640, 480),  # Medium
            (1280, 720),  # HD
        ],
    )
    def test_benchmark_frame_processing_by_size(self, benchmark, width, height):
        """Benchmark frame processing by size - frame operations only."""

        def process_frames():
            # Create frame data
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:, :] = [128, 64, 192]  # Simple pattern

            # Convert to bytes (what recorder.add_frame() receives)
            frame_bytes = frame.tobytes()

            # Simulate frame validation (what recorder does internally)
            expected_size = width * height * 3
            if len(frame_bytes) != expected_size:
                raise ValueError(
                    f"Frame size mismatch: {len(frame_bytes)} != {expected_size}"
                )

            # Convert back to array (for processing)
            frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            processed_frame = frame_array.reshape((height, width, 3))

            return processed_frame.copy()

        benchmark(process_frames)

    def test_benchmark_frame_conversion(self, benchmark):
        """Benchmark frame data conversion from bytes to numpy array."""
        width, height = 640, 480
        frame_size = width * height * 3

        # Create test frame bytes
        frame_bytes = np.random.randint(0, 256, frame_size, dtype=np.uint8).tobytes()

        def convert_frame():
            frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = frame_array.reshape((height, width, 3))
            return frame.copy()

        benchmark(convert_frame)

    def test_benchmark_gradient_frame_creation(self, benchmark):
        """Benchmark gradient frame creation."""
        benchmark(create_gradient_frame)

    def test_benchmark_gradient_frame_creation_vectorized(self, benchmark):
        """Benchmark vectorized gradient frame creation."""
        width, height = 640, 480

        def create_vectorized_frame():
            # Create gradient using vectorized operations
            y_gradient = np.linspace(0, 255, height, dtype=np.uint8)
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:, :, 0] = y_gradient[:, np.newaxis]
            frame[:, :, 1] = 255 - y_gradient[:, np.newaxis]
            frame[:, :, 2] = y_gradient[:, np.newaxis] // 2
            return frame.tobytes()

        benchmark(create_vectorized_frame)

    def test_benchmark_random_frame_creation(self, benchmark):
        """Benchmark random frame creation."""
        benchmark(create_random_frame)

    def test_benchmark_solid_frame_creation(self, benchmark):
        """Benchmark solid color frame creation."""
        benchmark(create_solid_frame)

    def test_benchmark_frame_memory_copy(self, benchmark):
        """Benchmark frame memory copy operations."""
        width, height = 640, 480

        # Create source frame
        source_frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)

        def copy_frame():
            return source_frame.copy()

        benchmark(copy_frame)

    def test_benchmark_frame_serialization(self, benchmark):
        """Benchmark frame serialization to bytes."""
        width, height = 640, 480

        # Create source frame
        source_frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)

        def serialize_frame():
            return source_frame.tobytes()

        benchmark(serialize_frame)

    @pytest.mark.parametrize("pattern_type", ["gradient", "random", "solid"])
    def test_benchmark_frame_patterns(self, benchmark, pattern_type):
        """Benchmark different frame creation patterns."""
        width, height = 640, 480

        if pattern_type == "gradient":

            def create_frame():
                return create_gradient_frame(width, height)
        elif pattern_type == "random":

            def create_frame():
                return create_random_frame(width, height)
        else:  # solid

            def create_frame():
                return create_solid_frame((128, 64, 192), width, height)

        benchmark(create_frame)

    @pytest.mark.slow
    def test_benchmark_4k_frame_processing(self, benchmark):
        """Benchmark processing of 4K frames (3840x2160)."""
        recorder = Recorder(output_dir=self.temp_dir, width=3840, height=2160, fps=30.0)

        try:
            action_id = "benchmark_4k_frame_test"
            num_frames = 10  # Fewer frames for 4K due to size

            # Pre-create frames
            frames = []
            for i in range(num_frames):
                frame = np.zeros((2160, 3840, 3), dtype=np.uint8)
                # Create gradient pattern
                for row in range(2160):
                    intensity = int(255 * row / 2160)
                    frame[row, :] = (intensity, (intensity + i) % 256, 255 - intensity)
                frames.append(frame.tobytes())

            def process_4k_frames():
                recorder.start_recording(action_id)
                for frame_bytes in frames:
                    recorder.add_frame(frame_bytes)
                recorder.stop_recording(action_id)

            benchmark(process_4k_frames)

        finally:
            recorder.close()
