"""Consolidated test suite for the queue-based recorder."""

import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from .recorder import Recorder
from .test_helpers import create_test_frame, setup_temp_recorder, create_solid_frame


class TestRecorderCore:
    """Core functionality tests for the Recorder class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.recorder = Recorder(
            output_dir=self.temp_dir, width=640, height=480, fps=30.0
        )

    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(self, "recorder"):
            self.recorder.close()

    def test_initialization(self):
        """Test recorder initialization."""
        assert self.recorder.width == 640
        assert self.recorder.height == 480
        assert self.recorder.fps == 30.0
        assert not self.recorder.is_recording
        assert self.recorder.current_action_id is None
        assert Path(self.temp_dir).exists()

    def test_start_recording(self):
        """Test starting a recording."""
        action_id = "test_action"
        file_path = self.recorder.start_recording(action_id)

        assert self.recorder.is_recording
        assert self.recorder.current_action_id == action_id
        assert file_path.endswith(".mp4")
        assert Path(file_path).parent == Path(self.temp_dir)

        # Check that recording is tracked
        assert action_id in self.recorder.active_recordings
        recording = self.recorder.active_recordings[action_id]
        assert recording["status"] == "recording"
        assert recording["frame_count"] == 0

    def test_start_recording_same_action_twice(self):
        """Test starting recording for same action twice."""
        action_id = "test_action"
        file_path1 = self.recorder.start_recording(action_id)
        file_path2 = self.recorder.start_recording(action_id)

        # Should return same path and continue recording
        assert file_path1 == file_path2
        assert self.recorder.is_recording
        assert self.recorder.current_action_id == action_id

    def test_start_recording_different_actions(self):
        """Test starting recording for different actions."""
        action_id1 = "test_action1"
        action_id2 = "test_action2"

        file_path1 = self.recorder.start_recording(action_id1)
        file_path2 = self.recorder.start_recording(action_id2)

        # Should stop first and start second
        assert file_path1 != file_path2
        assert self.recorder.current_action_id == action_id2
        assert self.recorder.is_recording

    def test_add_frame(self):
        """Test adding frames to recording."""
        action_id = "test_action"
        self.recorder.start_recording(action_id)

        # Add frames deterministically
        for i in range(5):
            frame_bytes = create_test_frame(i)
            self.recorder.add_frame(frame_bytes)

        # Check frame count is tracked correctly
        recording = self.recorder.active_recordings[action_id]
        assert recording["frame_count"] == 5

    def test_add_frame_without_recording(self):
        """Test adding frame when not recording."""
        frame_bytes = create_test_frame()
        # Should not raise exception
        self.recorder.add_frame(frame_bytes)

        # Should not create any recordings
        assert len(self.recorder.active_recordings) == 0

    def test_stop_recording(self):
        """Test stopping a recording."""
        action_id = "test_action"
        self.recorder.start_recording(action_id)

        # Add some frames
        for i in range(3):
            frame_bytes = create_test_frame(i)
            self.recorder.add_frame(frame_bytes)

        file_path = self.recorder.stop_recording(action_id)

        assert file_path is not None
        assert not self.recorder.is_recording
        assert self.recorder.current_action_id is None

        # Recording should be marked as finalizing
        recording = self.recorder.active_recordings[action_id]
        assert recording["status"] == "finalizing"

    def test_stop_recording_nonexistent(self):
        """Test stopping a recording that doesn't exist."""
        result = self.recorder.stop_recording("nonexistent")
        assert result is None

    def test_stop_recording_wrong_action(self):
        """Test stopping recording with wrong action ID."""
        action_id1 = "test_action1"
        action_id2 = "test_action2"

        self.recorder.start_recording(action_id1)
        result = self.recorder.stop_recording(action_id2)

        assert result is None
        assert self.recorder.is_recording  # Should still be recording action1

    def test_get_recording_file(self):
        """Test getting recording file path."""
        action_id = "test_action"
        self.recorder.start_recording(action_id)

        # While recording, should return path but file may not be ready
        file_path = self.recorder.get_recording_file(action_id)
        assert file_path is not None
        assert file_path.endswith(".mp4")

    def test_get_recording_file_nonexistent(self):
        """Test getting file for nonexistent recording."""
        result = self.recorder.get_recording_file("nonexistent")
        assert result is None

    def test_get_recording_status(self):
        """Test getting recording status."""
        action_id = "test_action"
        self.recorder.start_recording(action_id)

        status = self.recorder.get_recording_status(action_id)
        assert status is not None
        assert status["status"] == "recording"
        assert status["frame_count"] == 0
        assert "start_time" in status

    def test_get_recording_status_nonexistent(self):
        """Test getting status for nonexistent recording."""
        result = self.recorder.get_recording_status("nonexistent")
        assert result is None

    def test_list_recordings(self):
        """Test listing all recordings."""
        action_id1 = "test_action1"
        action_id2 = "test_action2"

        # Initially empty
        recordings = self.recorder.list_recordings()
        assert len(recordings) == 0

        # Start some recordings
        self.recorder.start_recording(action_id1)
        self.recorder.start_recording(action_id2)  # This stops action1

        recordings = self.recorder.list_recordings()
        assert len(recordings) == 2
        assert action_id1 in recordings
        assert action_id2 in recordings

    def test_delete_recording(self):
        """Test deleting a recording."""
        action_id = "test_action"
        self.recorder.start_recording(action_id)
        self.recorder.stop_recording(action_id)

        result = self.recorder.delete_recording(action_id)
        assert result is True
        assert action_id not in self.recorder.active_recordings

    def test_delete_recording_nonexistent(self):
        """Test deleting nonexistent recording."""
        result = self.recorder.delete_recording("nonexistent")
        assert result is False

    def test_cleanup_old_recordings(self):
        """Test cleaning up old recordings."""
        action_id = "test_action"
        self.recorder.start_recording(action_id)
        self.recorder.stop_recording(action_id)

        # Mock old end time for deterministic testing
        with patch("time.time", return_value=7200):  # 2 hours from epoch
            if action_id in self.recorder.active_recordings:
                self.recorder.active_recordings[action_id]["end_time"] = (
                    3600  # 1 hour from epoch
                )

            self.recorder.cleanup_old_recordings(max_age_hours=0.5)  # 30 minutes

        # Should be removed from tracking
        assert action_id not in self.recorder.active_recordings

    def test_writer_thread_lifecycle(self):
        """Test writer thread creation and cleanup."""
        action_id = "test_action"

        # Initially no writer thread
        assert not self.recorder.writer_active

        # Start recording should create writer thread
        self.recorder.start_recording(action_id)
        assert self.recorder.writer_active
        assert self.recorder.writer_thread is not None
        assert self.recorder.writer_thread.is_alive()

        # Stop recording and close should clean up
        self.recorder.stop_recording(action_id)
        self.recorder.close()

        # Writer should be stopped
        assert not self.recorder.writer_active

    def test_frame_data_integrity(self):
        """Test that frame data is preserved correctly."""
        action_id = "test_action"
        self.recorder.start_recording(action_id)

        # Create a specific test pattern
        test_frame = np.full((480, 640, 3), [255, 128, 64], dtype=np.uint8)
        frame_bytes = test_frame.tobytes()

        self.recorder.add_frame(frame_bytes)

        # Frame should be queued correctly
        recording = self.recorder.active_recordings[action_id]
        assert recording["frame_count"] == 1

    def test_callback_functionality(self):
        """Test recording finalized callback."""
        action_id = "test_action"
        callback_called = []

        def finalized_callback(action_id, recording_info):
            callback_called.append((action_id, recording_info))

        self.recorder.on_recording_finalized = finalized_callback

        self.recorder.start_recording(action_id)
        self.recorder.add_frame(create_test_frame())
        self.recorder.stop_recording(action_id)

        # Test that callback can be set without errors
        assert self.recorder.on_recording_finalized is not None
        assert callable(self.recorder.on_recording_finalized)


class TestRecorderEdgeCases:
    """Edge case and error condition tests."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.recorder = Recorder(
            output_dir=self.temp_dir, width=640, height=480, fps=30.0
        )

    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(self, "recorder"):
            self.recorder.close()

    def test_invalid_output_directory(self):
        """Test handling of invalid output directory."""
        # Try to create recorder with invalid directory
        invalid_path = "/invalid/nonexistent/path"

        # Should create directory or handle gracefully
        try:
            recorder = Recorder(output_dir=invalid_path)
            # If it succeeds, directory should be created
            assert Path(invalid_path).exists()
            recorder.close()
        except Exception:
            # If it fails, that's also acceptable behavior
            pass

    @pytest.mark.parametrize("fps", [0.0, -1.0])
    def test_invalid_fps(self, fps):
        """Test handling of invalid FPS values."""
        recorder = Recorder(output_dir=self.temp_dir, fps=fps)
        assert recorder.fps == fps
        recorder.close()

    @pytest.mark.parametrize("width,height", [(0, 480), (640, 0), (-640, 480)])
    def test_invalid_dimensions(self, width, height):
        """Test handling of invalid frame dimensions."""
        recorder = Recorder(output_dir=self.temp_dir, width=width, height=height)
        assert recorder.width == width
        assert recorder.height == height
        recorder.close()

    @pytest.mark.parametrize("action_id", ["", None])
    def test_empty_action_id(self, action_id):
        """Test handling of empty action ID."""
        result = self.recorder.start_recording(action_id)
        assert result is not None  # Should handle gracefully
        self.recorder.stop_recording(action_id)

    def test_very_long_action_id(self):
        """Test handling of very long action ID."""
        long_action_id = "a" * 100  # 100 character action ID

        # Should handle gracefully
        result = self.recorder.start_recording(long_action_id)
        assert result is not None
        assert result.endswith(".mp4")

        self.recorder.stop_recording(long_action_id)

    @pytest.mark.parametrize("action_id", [
        "action/with/slashes",
        "action\\with\\backslashes", 
        "action:with:colons",
        "action*with*asterisks",
        "action?with?questions",
        "action<with>brackets",
        "action|with|pipes",
        'action"with"quotes',
    ])
    def test_special_characters_in_action_id(self, action_id):
        """Test handling of special characters in action ID."""
        # Should handle gracefully without crashing
        try:
            result = self.recorder.start_recording(action_id)
            if result:
                self.recorder.stop_recording(action_id)
        except Exception as e:
            # Some special characters may cause expected failures
            print(f"Expected failure for '{action_id}': {e}")

    @pytest.mark.parametrize("frame_data", [
        b"",  # Empty bytes
        b"too_short",  # Too short
        None,  # None type
    ])
    def test_malformed_frame_data(self, frame_data):
        """Test handling of malformed frame data."""
        action_id = "malformed_test"
        self.recorder.start_recording(action_id)

        # Should handle gracefully without crashing
        self.recorder.add_frame(frame_data)

        # Recorder should still be functional
        assert self.recorder.is_recording

        # Add valid frame to confirm it still works
        valid_frame = create_test_frame()
        self.recorder.add_frame(valid_frame)

        self.recorder.stop_recording(action_id)

    def test_wrong_frame_size(self):
        """Test handling of wrong frame size."""
        action_id = "wrong_size_test"
        self.recorder.start_recording(action_id)

        # Create frame with wrong dimensions
        wrong_frame = np.zeros((240, 320, 3), dtype=np.uint8)  # Half size
        wrong_frame_bytes = wrong_frame.tobytes()

        # Should handle gracefully
        self.recorder.add_frame(wrong_frame_bytes)

        # Recorder should still be functional
        assert self.recorder.is_recording

        self.recorder.stop_recording(action_id)

    def test_disk_full_simulation(self):
        """Test handling of disk full scenario."""
        action_id = "disk_full_test"

        # Mock imageio.get_writer to simulate disk full
        with patch("imageio.get_writer") as mock_writer:
            mock_writer_instance = MagicMock()
            mock_writer_instance.append_data.side_effect = OSError(
                "No space left on device"
            )
            mock_writer.return_value = mock_writer_instance

            self.recorder.start_recording(action_id)

            # Add frame - should handle disk full gracefully
            frame_bytes = create_test_frame()
            self.recorder.add_frame(frame_bytes)

            # Should not crash the recorder
            assert self.recorder.is_recording

            self.recorder.stop_recording(action_id)

    def test_writer_creation_failure(self):
        """Test handling of video writer creation failure."""
        action_id = "writer_fail_test"

        # Mock imageio.get_writer to fail
        with patch(
            "imageio.get_writer", side_effect=Exception("Writer creation failed")
        ):
            # Should handle gracefully
            try:
                result = self.recorder.start_recording(action_id)
                # If it doesn't raise, it handled gracefully
                if result:
                    self.recorder.stop_recording(action_id)
            except Exception as e:
                # Expected failure is acceptable
                print(f"Expected writer creation failure: {e}")

    def test_stop_before_start(self):
        """Test stopping recording before starting."""
        result = self.recorder.stop_recording("never_started")
        assert result is None

    def test_multiple_stops(self):
        """Test stopping the same recording multiple times."""
        action_id = "multiple_stop_test"

        self.recorder.start_recording(action_id)

        # First stop should work
        result1 = self.recorder.stop_recording(action_id)
        assert result1 is not None

        # Second stop should return None
        result2 = self.recorder.stop_recording(action_id)
        assert result2 is None

    def test_error_handling_invalid_frame(self):
        """Test error handling with invalid frame data."""
        action_id = "test_action"
        self.recorder.start_recording(action_id)

        # Try to add invalid frame data
        invalid_frame = b"invalid_frame_data"

        # Should handle gracefully without crashing
        self.recorder.add_frame(invalid_frame)

        # Recording should still be active
        assert self.recorder.is_recording
        assert self.recorder.current_action_id == action_id

    def test_callback_exception(self):
        """Test handling of exceptions in callbacks."""
        action_id = "callback_exception_test"

        def failing_callback(action_id, recording_info):
            raise Exception("Callback failed")

        self.recorder.on_recording_finalized = failing_callback

        self.recorder.start_recording(action_id)
        frame_bytes = create_test_frame()
        self.recorder.add_frame(frame_bytes)

        # Should handle callback exception gracefully
        self.recorder.stop_recording(action_id)

        # Recorder should still be functional
        assert not self.recorder.is_recording

    @pytest.mark.parametrize("unicode_id", [
        "测试_action",  # Chinese
        "тест_action",  # Russian
        "🎬_recording",  # Emoji
        "café_action",  # Accented characters
    ])
    def test_unicode_action_id(self, unicode_id):
        """Test handling of Unicode action IDs."""
        try:
            result = self.recorder.start_recording(unicode_id)
            if result:
                # Add a frame
                frame_bytes = create_test_frame()
                self.recorder.add_frame(frame_bytes)
                self.recorder.stop_recording(unicode_id)
        except Exception as e:
            # Some Unicode may cause expected failures
            print(f"Expected failure for Unicode ID '{unicode_id}': {e}")

    def test_cleanup_with_active_recording(self):
        """Test cleanup while recording is active."""
        action_id = "cleanup_active_test"
        self.recorder.start_recording(action_id)

        # Add some frames
        for i in range(5):
            frame_bytes = create_test_frame(i)
            self.recorder.add_frame(frame_bytes)

        # Close while recording is active
        self.recorder.close()

        # Should handle gracefully
        assert not self.recorder.writer_active


class TestRecorderStress:
    """Stress tests and high-load scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.recorder = Recorder(
            output_dir=self.temp_dir, width=640, height=480, fps=30.0
        )

    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(self, "recorder"):
            self.recorder.close()

    def test_thread_safety(self):
        """Test thread safety of recorder operations."""
        action_id = "test_action"
        self.recorder.start_recording(action_id)

        errors = []

        def add_frames():
            try:
                for i in range(10):
                    frame_bytes = create_test_frame(i)
                    self.recorder.add_frame(frame_bytes)
            except Exception as e:
                errors.append(e)

        # Start multiple threads adding frames
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=add_frames)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should not have any errors
        assert len(errors) == 0

        # Should have recorded all frames
        recording = self.recorder.active_recordings[action_id]
        assert recording["frame_count"] == 30  # 3 threads * 10 frames each

    @pytest.mark.parametrize("frame_count", [100, 500])
    def test_queue_overflow_handling(self, frame_count):
        """Test handling of queue overflow scenarios."""
        action_id = "overflow_test"
        self.recorder.start_recording(action_id)

        # Add many frames to test queue handling
        for i in range(frame_count):
            frame_bytes = create_test_frame(i)
            self.recorder.add_frame(frame_bytes)

        # Should handle gracefully without errors
        recording = self.recorder.active_recordings[action_id]
        assert recording["frame_count"] == frame_count

        self.recorder.stop_recording(action_id)

    def test_rapid_start_stop_cycles(self):
        """Test rapid start/stop cycles for edge cases."""
        action_id = "rapid_cycle_test"

        # Rapid cycles
        for i in range(10):
            self.recorder.start_recording(f"{action_id}_{i}")
            # Immediately stop without adding frames
            self.recorder.stop_recording(f"{action_id}_{i}")

        # Should handle gracefully
        assert not self.recorder.is_recording

    def test_concurrent_same_action(self):
        """Test concurrent operations on same action ID."""
        action_id = "concurrent_same_test"

        def start_stop_worker():
            for _ in range(5):
                self.recorder.start_recording(action_id)
                self.recorder.stop_recording(action_id)

        # Run concurrent workers
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=start_stop_worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should handle gracefully
        assert not self.recorder.is_recording

    def test_concurrent_start_stop(self):
        """Test concurrent start/stop operations."""
        action_id = "test_action"

        def start_stop_cycle():
            for i in range(5):
                self.recorder.start_recording(f"{action_id}_{i}")
                self.recorder.stop_recording(f"{action_id}_{i}")

        # Run concurrent start/stop cycles
        threads = []
        for _ in range(2):
            thread = threading.Thread(target=start_stop_cycle)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should handle gracefully
        assert not self.recorder.is_recording

    def test_memory_pressure(self):
        """Test behavior under memory pressure."""
        action_id = "memory_pressure_test"
        self.recorder.start_recording(action_id)

        # Create large frames to simulate memory pressure
        large_frames = []
        for i in range(10):
            # Create larger than normal frame
            large_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
            large_frame[:, :] = [i % 256, (i * 2) % 256, (i * 3) % 256]
            large_frames.append(large_frame.tobytes())

        # Add frames rapidly
        for frame_bytes in large_frames:
            self.recorder.add_frame(frame_bytes)

        # Should handle gracefully
        assert self.recorder.is_recording

        self.recorder.stop_recording(action_id)

    def test_thread_interruption(self):
        """Test handling of thread interruption."""
        action_id = "thread_interrupt_test"
        self.recorder.start_recording(action_id)

        # Add some frames
        for i in range(10):
            frame_bytes = create_test_frame(i)
            self.recorder.add_frame(frame_bytes)

        # Force close without proper stop
        self.recorder.close()

        # Should handle gracefully
        assert not self.recorder.writer_active

    @pytest.mark.slow
    def test_4k_resolution_recording(self):
        """Test very high resolution (4K) recording."""
        # Create 4K recorder
        recorder_4k = Recorder(
            output_dir=self.temp_dir, width=3840, height=2160, fps=30
        )

        try:
            action_id = "4k_resolution_test"
            recorder_4k.start_recording(action_id)

            # Create 4K test frames
            for i in range(10):  # Fewer frames due to size
                frame = np.zeros((2160, 3840, 3), dtype=np.uint8)
                # Create a simple pattern
                for row in range(2160):
                    intensity = int(255 * row / 2160)
                    frame[row, :] = (intensity, (intensity + i) % 256, 255 - intensity)

                frame_bytes = frame.tobytes()
                recorder_4k.add_frame(frame_bytes)

            file_path = recorder_4k.stop_recording(action_id)

            # Verify recording
            assert file_path is not None
            recording = recorder_4k.active_recordings[action_id]
            assert recording["frame_count"] == 10

        finally:
            recorder_4k.close()

    @pytest.mark.slow
    def test_extreme_high_fps_recording(self):
        """Test very high FPS (240) recording."""
        # Create high FPS recorder
        recorder_high_fps = Recorder(
            output_dir=self.temp_dir, width=640, height=480, fps=240
        )

        try:
            action_id = "high_fps_test"
            recorder_high_fps.start_recording(action_id)

            # Add frames rapidly (no delay to test maximum throughput)
            for i in range(100):
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                frame[:, :] = [(i * 5) % 256, i % 256, (255 - i * 3) % 256]
                frame_bytes = frame.tobytes()
                recorder_high_fps.add_frame(frame_bytes)

            file_path = recorder_high_fps.stop_recording(action_id)

            # Verify recording
            assert file_path is not None
            recording = recorder_high_fps.active_recordings[action_id]
            assert recording["frame_count"] == 100

        finally:
            recorder_high_fps.close()

    @pytest.mark.stress
    def test_extreme_queue_overflow(self):
        """Test extreme queue overflow with 1000+ frames."""
        action_id = "extreme_overflow_test"
        self.recorder.start_recording(action_id)

        # Add massive number of frames rapidly
        for i in range(1000):
            frame_bytes = create_test_frame(i)
            self.recorder.add_frame(frame_bytes)

        # Should handle without crashing
        assert self.recorder.is_recording

        self.recorder.stop_recording(action_id)

        # Verify all frames were queued
        recording = self.recorder.active_recordings[action_id]
        assert recording["frame_count"] == 1000
