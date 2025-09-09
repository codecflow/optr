"""Optimized benchmarks for recorder - only meaningful performance tests."""

import tempfile
import time
from pathlib import Path

import pytest

from .recorder import Recorder
from .test_helpers import create_solid_frame, create_test_frame


@pytest.mark.benchmark
class TestRecorderPerformance:
    """Performance benchmarks for real-world recorder usage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up after tests."""
        # Clean up any test files
        for file_path in Path(self.temp_dir).glob("*.mp4"):
            try:
                file_path.unlink()
            except Exception:
                pass

    def test_benchmark_real_mp4_encoding_throughput(self, benchmark):
        """Benchmark actual MP4 encoding performance with real writer."""
        recorder = Recorder(
            output_dir=self.temp_dir,
            width=640,
            height=480,
            fps=30.0,
            # Use default factory (BackgroundWriter + MP4Writer)
        )

        try:
            action_id = "mp4_throughput_test"
            num_frames = 30  # 1 second at 30fps

            # Pre-create frames to isolate encoding performance
            frames = []
            for i in range(num_frames):
                frame = create_solid_frame(
                    (i * 8 % 256, 128, 255 - i * 8 % 256), width=640, height=480
                )
                frames.append(frame)

            def encode_video():
                recorder.start(action_id)
                for frame_bytes in frames:
                    recorder.write(action_id, frame_bytes)
                final_path = recorder.stop(action_id)

                # Verify file was actually created
                if final_path and Path(final_path).exists():
                    return Path(final_path).stat().st_size
                return 0

            file_size = benchmark(encode_video)

            # Verify we actually encoded something
            assert file_size > 0, "No MP4 file was created"

        finally:
            recorder.close()

    def test_benchmark_sustained_write_performance(self, benchmark):
        """Benchmark sustained write performance over longer duration."""
        recorder = Recorder(
            output_dir=self.temp_dir,
            width=320,
            height=240,
            fps=30.0,
        )

        try:
            action_id = "sustained_write_test"
            num_frames = 150  # 5 seconds at 30fps

            # Create varied frames to simulate real usage
            frames = []
            for i in range(num_frames):
                # Alternate between different patterns
                if i % 3 == 0:
                    frame = create_solid_frame((255, 0, 0), width=320, height=240)
                elif i % 3 == 1:
                    frame = create_solid_frame((0, 255, 0), width=320, height=240)
                else:
                    frame = create_test_frame(i, width=320, height=240)
                frames.append(frame)

            def sustained_recording():
                recorder.start(action_id)

                start_time = time.time()
                for frame_bytes in frames:
                    recorder.write(action_id, frame_bytes)
                write_duration = time.time() - start_time

                recorder.stop(action_id)

                # Return frames per second achieved
                return len(frames) / write_duration if write_duration > 0 else 0

            fps_achieved = benchmark(sustained_recording)

            # Should achieve reasonable throughput
            assert fps_achieved > 10, f"Too slow: {fps_achieved:.1f} fps"

        finally:
            recorder.close()

    @pytest.mark.parametrize(
        "resolution",
        [
            (320, 240),  # Small - baseline
            (640, 480),  # Medium - common
            (1280, 720),  # HD - performance test
        ],
    )
    def test_benchmark_resolution_encoding_performance(self, benchmark, resolution):
        """Benchmark encoding performance across different resolutions."""
        width, height = resolution
        recorder = Recorder(
            output_dir=self.temp_dir,
            width=width,
            height=height,
            fps=30.0,
        )

        try:
            action_id = f"resolution_{width}x{height}_test"
            # Scale frame count by resolution to keep test duration reasonable
            base_frames = 30
            scale_factor = (width * height) / (320 * 240)
            num_frames = max(10, int(base_frames / scale_factor))

            # Create frames with actual content
            frames = []
            for i in range(num_frames):
                frame = create_solid_frame(
                    (i * 10 % 256, 128, 255 - i * 10 % 256), width=width, height=height
                )
                frames.append(frame)

            def encode_at_resolution():
                recorder.start(action_id)
                for frame_bytes in frames:
                    recorder.write(action_id, frame_bytes)
                final_path = recorder.stop(action_id)

                # Return encoding rate (pixels per second)
                if final_path and Path(final_path).exists():
                    return width * height * num_frames
                return 0

            pixels_encoded = benchmark(encode_at_resolution)
            assert pixels_encoded > 0, f"Failed to encode {width}x{height}"

        finally:
            recorder.close()

    def test_benchmark_concurrent_recording_performance(self, benchmark):
        """Benchmark performance with multiple concurrent recordings."""
        recorder = Recorder(
            output_dir=self.temp_dir,
            width=320,
            height=240,
            fps=30.0,
        )

        try:
            num_recordings = 3
            frames_per_recording = 20

            # Pre-create frames for each recording
            all_frames = {}
            for recording_id in range(num_recordings):
                frames = []
                for frame_num in range(frames_per_recording):
                    # Different color per recording
                    color = (recording_id * 80 % 256, 128, frame_num * 10 % 256)
                    frame = create_solid_frame(color, width=320, height=240)
                    frames.append(frame)
                all_frames[f"concurrent_{recording_id}"] = frames

            def concurrent_recordings():
                # Start all recordings
                for recording_id in all_frames.keys():
                    recorder.start(recording_id)

                # Write frames to all recordings
                for frame_idx in range(frames_per_recording):
                    for recording_id, frames in all_frames.items():
                        recorder.write(recording_id, frames[frame_idx])

                # Stop all recordings
                final_paths = []
                for recording_id in all_frames.keys():
                    path = recorder.stop(recording_id)
                    if path and Path(path).exists():
                        final_paths.append(path)

                return len(final_paths)

            files_created = benchmark(concurrent_recordings)
            assert files_created == num_recordings, (
                f"Only {files_created}/{num_recordings} files created"
            )

        finally:
            recorder.close()


@pytest.mark.benchmark
@pytest.mark.slow
class TestRecorderMemoryPerformance:
    """Memory and resource usage benchmarks."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up after tests."""
        for file_path in Path(self.temp_dir).glob("*.mp4"):
            try:
                file_path.unlink()
            except Exception:
                pass

    def test_benchmark_memory_usage_large_recording(self, benchmark):
        """Benchmark memory efficiency with large recording."""
        recorder = Recorder(
            output_dir=self.temp_dir,
            width=640,
            height=480,
            fps=30.0,
        )

        try:
            action_id = "memory_test"
            num_frames = 300  # 10 seconds at 30fps

            def large_recording():
                recorder.start(action_id)

                # Generate frames on-the-fly to test memory efficiency
                for i in range(num_frames):
                    # Create frame without storing in memory
                    frame = create_test_frame(i, width=640, height=480)
                    recorder.write(action_id, frame)

                final_path = recorder.stop(action_id)

                if final_path and Path(final_path).exists():
                    return Path(final_path).stat().st_size
                return 0

            file_size = benchmark(large_recording)
            assert file_size > 0, "Large recording failed"

        finally:
            recorder.close()

    def test_benchmark_hd_encoding_performance(self, benchmark):
        """Benchmark HD resolution encoding performance."""
        recorder = Recorder(
            output_dir=self.temp_dir,
            width=1280,
            height=720,
            fps=30.0,
        )

        try:
            action_id = "hd_performance_test"
            num_frames = 60  # 2 seconds at 30fps

            # Pre-create HD frames
            frames = []
            for i in range(num_frames):
                frame = create_solid_frame(
                    (i * 4 % 256, 128, 255 - i * 4 % 256), width=1280, height=720
                )
                frames.append(frame)

            def hd_encoding():
                recorder.start(action_id)

                start_time = time.time()
                for frame_bytes in frames:
                    recorder.write(action_id, frame_bytes)
                encoding_time = time.time() - start_time

                final_path = recorder.stop(action_id)

                # Return megapixels per second
                if final_path and Path(final_path).exists():
                    megapixels = (1280 * 720 * num_frames) / 1_000_000
                    return megapixels / encoding_time if encoding_time > 0 else 0
                return 0

            mp_per_second = benchmark(hd_encoding)
            assert mp_per_second > 0, "HD encoding failed"

        finally:
            recorder.close()
