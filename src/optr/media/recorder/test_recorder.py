"""Focused test suite for Recorder with deterministic, meaningful tests."""

import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from .recorder import Recorder
from .test_helpers import create_solid_frame, create_test_frame


class MockWriter:
    """Thread-safe mock writer for testing without file I/O."""

    def __init__(self, path):
        self.path = path
        self.frames = []
        self.closed = False
        self.write_calls = 0
        self.lock = threading.Lock()
        self.fail_on_write = False
        self.close_event = threading.Event()

    def write(self, frame):
        with self.lock:
            if self.closed:
                raise RuntimeError("Writer is closed")
            if self.fail_on_write:
                raise RuntimeError("Simulated write failure")
            self.frames.append(frame.copy() if hasattr(frame, "copy") else frame)
            self.write_calls += 1

    def close(self):
        with self.lock:
            self.closed = True
            self.close_event.set()


class TestRecorderCore:
    """Core functionality tests."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_writers = {}

        def mock_factory(path):
            writer = MockWriter(path)
            self.mock_writers[str(path)] = writer
            return writer

        self.recorder = Recorder(
            output_dir=self.temp_dir,
            width=640,
            height=480,
            fps=30.0,
            writer_factory=mock_factory,
        )

    def teardown_method(self):
        self.recorder.close()

    def test_start_creates_recording_with_metadata(self):
        """Test that start() creates recording with proper metadata."""
        with patch("time.time", return_value=1000.0):
            path = self.recorder.start("test")

        assert "test" in self.recorder.recordings
        writer, metadata = self.recorder.recordings["test"]

        assert metadata["status"] == "recording"
        assert metadata["frame_count"] == 0
        assert metadata["start_time"] == 1000.0
        assert path.endswith(".mp4")
        assert str(self.temp_dir) in path

    def test_start_same_id_returns_existing_path(self):
        """Test that starting same ID twice returns same path."""
        path1 = self.recorder.start("test")
        path2 = self.recorder.start("test")

        assert path1 == path2
        assert len(self.recorder.recordings) == 1

    def test_write_frame_data_types(self):
        """Test writing different frame data types."""
        self.recorder.start("test")

        # Test bytes
        frame_bytes = create_test_frame(width=640, height=480)
        success = self.recorder.write("test", frame_bytes)
        assert success

        # Test numpy array
        frame_array = np.zeros((480, 640, 3), dtype=np.uint8)
        frame_array.fill(128)
        success = self.recorder.write("test", frame_array)
        assert success

        # Test multiple frames at once
        frames = [
            create_test_frame(0, width=640, height=480),
            create_test_frame(1, width=640, height=480),
        ]
        success = self.recorder.write("test", frames)
        assert success

        # Verify total frame count
        _, metadata = self.recorder.recordings["test"]
        assert metadata["frame_count"] == 4

    def test_write_to_nonexistent_recording_fails(self):
        """Test writing to non-existent recording returns False."""
        frame_bytes = create_test_frame()
        success = self.recorder.write("nonexistent", frame_bytes)
        assert not success

    def test_stop_removes_recording_and_closes_writer(self):
        """Test stop() removes recording and closes writer."""
        with patch("time.time", side_effect=[1000.0, 1005.0, 1005.0]):
            self.recorder.start("test")
            path = self.recorder.stop("test")

        assert "test" not in self.recorder.recordings
        assert path.endswith(".mp4")

        # Verify writer was closed
        writer = self.mock_writers[path]
        assert writer.closed

    def test_status_returns_correct_info(self):
        """Test status() returns accurate recording information."""
        with patch("time.time", side_effect=[1000.0, 1000.0, 1003.0]):
            self.recorder.start("test")
            self.recorder.write("test", create_test_frame(width=640, height=480))
            status = self.recorder.status("test")

        assert status["status"] == "recording"
        assert status["frame_count"] == 1
        assert status["start_time"] == 1000.0
        assert status["duration"] == 3.0
        assert status["file_path"].endswith(".mp4")

    def test_nonexistent_operations_return_none_or_false(self):
        """Test operations on non-existent recordings return appropriate values."""
        # Stop non-existent recording
        result = self.recorder.stop("nonexistent")
        assert result is None

        # Status for non-existent recording
        result = self.recorder.status("nonexistent")
        assert result is None

        # File for non-existent recording (no files on disk)
        result = self.recorder.file("nonexistent")
        assert result is None

        # Write to non-existent recording
        frame_bytes = create_test_frame()
        success = self.recorder.write("nonexistent", frame_bytes)
        assert not success

    def test_list_returns_all_active_recordings(self):
        """Test list() returns all active recordings with status."""
        with patch(
            "time.time", side_effect=[1000.0, 1000.0, 1001.0, 1001.0, 1005.0, 1005.0]
        ):
            self.recorder.start("test1")
            self.recorder.start("test2")
            recordings = self.recorder.list()

        assert len(recordings) == 2
        assert "test1" in recordings
        assert "test2" in recordings

        for _recording_id, status in recordings.items():
            assert status["status"] == "recording"
            assert "frame_count" in status
            assert "duration" in status

    def test_file_returns_path_for_active_recording(self):
        """Test file() returns path for active recording."""
        path = self.recorder.start("active")
        result = self.recorder.file("active")
        assert result == path

    def test_file_finds_completed_recording_on_disk(self):
        """Test file() can find completed recordings by pattern."""
        # Create a mock file that matches the pattern
        mock_file = Path(self.temp_dir) / "recording_completed_123456.mp4"
        mock_file.touch()

        result = self.recorder.file("completed")
        assert result == str(mock_file)

    def test_close_stops_all_recordings(self):
        """Test close() stops all active recordings."""
        self.recorder.start("test1")
        self.recorder.start("test2")

        self.recorder.close()

        assert len(self.recorder.recordings) == 0

        # Verify all writers were closed
        for writer in self.mock_writers.values():
            assert writer.closed


class TestRecorderErrorHandling:
    """Error handling and edge case tests."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_writers = {}

        def mock_factory(path):
            writer = MockWriter(path)
            self.mock_writers[str(path)] = writer
            return writer

        self.recorder = Recorder(
            output_dir=self.temp_dir,
            width=640,
            height=480,
            fps=30.0,
            writer_factory=mock_factory,
        )

    def teardown_method(self):
        self.recorder.close()

    def test_write_with_writer_error_returns_false(self):
        """Test that writer errors are handled gracefully."""
        failing_writer = Mock()
        failing_writer.write.side_effect = Exception("Write failed")

        def failing_factory(path):
            return failing_writer

        recorder = Recorder(output_dir=self.temp_dir, writer_factory=failing_factory)

        try:
            recorder.start("test")
            success = recorder.write("test", create_test_frame())
            assert not success
        finally:
            recorder.close()

    def test_malformed_bytes_handled_gracefully(self):
        """Test that malformed byte data is caught and handled."""
        self.recorder.start("test")

        # Too short bytes - will cause ValueError in reshape
        success = self.recorder.write("test", b"short")
        assert not success

        # Empty bytes - will cause ValueError in reshape
        success = self.recorder.write("test", b"")
        assert not success

        # Recording should still be usable after errors
        valid_frame = create_test_frame(width=640, height=480)
        success = self.recorder.write("test", valid_frame)
        assert success

        # Frame count should only include successful writes
        _, metadata = self.recorder.recordings["test"]
        assert metadata["frame_count"] == 1

    def test_partial_write_failure_recovery(self):
        """Test recovery from partial write failures."""
        self.recorder.start("test")

        # Get the mock writer and configure it to fail after some writes
        _, metadata = self.recorder.recordings["test"]
        mock_writer = self.mock_writers[metadata["file_path"]]

        # Write some frames successfully
        for i in range(3):
            frame = create_test_frame(i, width=640, height=480)
            success = self.recorder.write("test", frame)
            assert success

        # Configure writer to fail
        mock_writer.fail_on_write = True

        # Next write should fail
        frame = create_test_frame(width=640, height=480)
        success = self.recorder.write("test", frame)
        assert not success

        # Frame count should only include successful writes
        _, metadata = self.recorder.recordings["test"]
        assert metadata["frame_count"] == 3

        # Re-enable writer and verify recording still works
        mock_writer.fail_on_write = False
        success = self.recorder.write("test", frame)
        assert success
        assert metadata["frame_count"] == 4

    def test_write_after_close_fails_gracefully(self):
        """Test that writing after close fails gracefully."""
        self.recorder.start("test")

        # Write a frame successfully
        frame = create_test_frame(width=640, height=480)
        success = self.recorder.write("test", frame)
        assert success

        # Close the recorder
        self.recorder.close()

        # Attempt to write after close should fail
        success = self.recorder.write("test", frame)
        assert not success

        # Recording should no longer exist
        assert "test" not in self.recorder.recordings

    def test_frame_dimension_mismatch_handling(self):
        """Test handling of frames with wrong dimensions."""
        self.recorder.start("test")

        # Test frame with wrong dimensions
        wrong_dims_frame = np.zeros((100, 100, 3), dtype=np.uint8)

        # Convert to bytes (will have wrong size)
        wrong_bytes = wrong_dims_frame.tobytes()

        # This should fail gracefully
        success = self.recorder.write("test", wrong_bytes)
        assert not success

        # Verify recording is still usable with correct dimensions
        correct_frame = create_test_frame(width=640, height=480)
        success = self.recorder.write("test", correct_frame)
        assert success

        _, metadata = self.recorder.recordings["test"]
        assert metadata["frame_count"] == 1  # Only the correct frame counted

    def test_delete_removes_first_matching_file(self):
        """Test delete() removes first matching file with real files."""
        # Create multiple files for the same recording ID
        test_files = []
        for timestamp in [123456, 234567, 345678]:
            test_file = Path(self.temp_dir) / f"recording_test_{timestamp}.mp4"
            test_file.write_text("dummy content")
            test_files.append(test_file)

        # Create a file for different recording ID (should not be deleted)
        other_file = Path(self.temp_dir) / "recording_other_999999.mp4"
        other_file.write_text("other content")

        # Delete should remove first matching file for "test" recording
        result = self.recorder.delete("test")

        # Verify operation succeeded
        assert result is True

        # Verify exactly one file was deleted (the first one found)
        remaining_files = [f for f in test_files if f.exists()]
        deleted_files = [f for f in test_files if not f.exists()]

        assert len(deleted_files) == 1, "Exactly one file should have been deleted"
        assert len(remaining_files) == 2, "Two files should remain"

        # Verify other file was not deleted
        assert other_file.exists(), "Other recording file should not have been deleted"

    def test_delete_no_matching_files_returns_false(self):
        """Test delete() returns False when no files match."""
        # Create some files that don't match the pattern
        unrelated_file = Path(self.temp_dir) / "other_file.mp4"
        unrelated_file.write_text("unrelated")

        # Try to delete non-existent recording
        result = self.recorder.delete("nonexistent")

        assert result is False
        # Unrelated file should still exist
        assert unrelated_file.exists()

    def test_delete_stops_active_recording_first(self):
        """Test delete() stops active recording before deleting files."""
        # Start a recording
        self.recorder.start("test")
        self.recorder.write("test", create_test_frame(width=640, height=480))

        # Verify recording is active
        assert "test" in self.recorder.recordings

        # Delete should stop the recording first
        result = self.recorder.delete("test")

        # Recording should be stopped
        assert "test" not in self.recorder.recordings

        # Should return True even if no files found (since we're using default recorder)
        assert isinstance(result, bool)

    def test_prune_removes_old_files(self):
        """Test prune() removes files older than specified age with real files."""
        import os
        import time

        current_time = time.time()

        # Create old files (should be removed)
        old_files = []
        for i in range(3):
            old_file = Path(self.temp_dir) / f"recording_old_{i}_123456.mp4"
            old_file.touch()
            # Set modification time to 1000 seconds ago
            os.utime(old_file, (current_time - 1000, current_time - 1000))
            old_files.append(old_file)

        # Create recent files (should be kept)
        recent_files = []
        for i in range(2):
            recent_file = Path(self.temp_dir) / f"recording_recent_{i}_123456.mp4"
            recent_file.touch()
            # Set modification time to 100 seconds ago
            os.utime(recent_file, (current_time - 100, current_time - 100))
            recent_files.append(recent_file)

        # Prune files older than 500 seconds
        removed_count = self.recorder.prune(500.0)

        # Verify old files were removed
        assert removed_count == 3
        for old_file in old_files:
            assert not old_file.exists(), f"{old_file} should have been removed"

        # Verify recent files were kept
        for recent_file in recent_files:
            assert recent_file.exists(), f"{recent_file} should have been kept"

    def test_prune_keeps_recent_files(self):
        """Test prune() keeps files newer than specified age with real files."""
        import os
        import time

        current_time = time.time()

        # Create only recent files
        recent_files = []
        for i in range(3):
            recent_file = Path(self.temp_dir) / f"recording_recent_{i}_123456.mp4"
            recent_file.touch()
            # Set modification time to 100 seconds ago (newer than 500s threshold)
            os.utime(recent_file, (current_time - 100, current_time - 100))
            recent_files.append(recent_file)

        # Prune files older than 500 seconds
        removed_count = self.recorder.prune(500.0)

        # No files should be removed
        assert removed_count == 0

        # All files should still exist
        for recent_file in recent_files:
            assert recent_file.exists(), f"{recent_file} should have been kept"

    @patch("pathlib.Path.glob")
    def test_prune_handles_file_errors_gracefully(self, mock_glob):
        """Test prune() handles file operation errors gracefully."""
        mock_file = Mock()
        mock_file.stat.return_value.st_mtime = 1000.0
        mock_file.unlink.side_effect = PermissionError("Cannot delete")
        mock_glob.return_value = [mock_file]

        # Should not crash, should return 0 removed
        with patch("time.time", return_value=2000.0):
            removed_count = self.recorder.prune(500.0)

        assert removed_count == 0

    @patch("pathlib.Path.glob")
    def test_delete_handles_file_errors_gracefully(self, mock_glob):
        """Test delete() handles file operation errors gracefully."""
        mock_file = Mock()
        mock_file.unlink.side_effect = PermissionError("Cannot delete")
        mock_glob.return_value = [mock_file]

        # Should not crash, should return False
        result = self.recorder.delete("test")
        assert result is False

    @patch("pathlib.Path.mkdir")
    def test_output_dir_creation_failure_handled(self, mock_mkdir):
        """Test handling when output dir can't be created."""
        mock_mkdir.side_effect = PermissionError("No permission")

        with pytest.raises(PermissionError):
            Recorder(output_dir="/invalid/path")


class TestRecorderIntegration:
    """Integration tests with real components."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.recorder = Recorder(output_dir=self.temp_dir)

    def teardown_method(self):
        self.recorder.close()

    def test_full_recording_workflow(self):
        """Test complete recording workflow."""
        # Start recording
        path = self.recorder.start("workflow_test")
        assert Path(path).parent == Path(self.temp_dir)

        # Write some frames
        for i in range(5):
            frame = create_solid_frame(
                (i * 50, 128, 255 - i * 50), width=1280, height=720
            )
            success = self.recorder.write("workflow_test", frame)
            assert success

        # Check status
        status = self.recorder.status("workflow_test")
        assert status["frame_count"] == 5
        assert status["status"] == "recording"

        # Stop recording
        final_path = self.recorder.stop("workflow_test")
        assert final_path == path
        assert "workflow_test" not in self.recorder.recordings

    def test_concurrent_recordings_isolated(self):
        """Test multiple recordings don't interfere."""
        # Start multiple recordings
        path1 = self.recorder.start("test1")
        path2 = self.recorder.start("test2")

        assert path1 != path2
        assert len(self.recorder.recordings) == 2

        # Write different amounts to each
        for i in range(3):
            self.recorder.write("test1", create_test_frame(i, width=1280, height=720))
        for i in range(7):
            self.recorder.write("test2", create_test_frame(i, width=1280, height=720))

        # Check frame counts are independent
        status1 = self.recorder.status("test1")
        status2 = self.recorder.status("test2")

        assert status1["frame_count"] == 3
        assert status2["frame_count"] == 7

        # Stop both
        self.recorder.stop("test1")
        self.recorder.stop("test2")

        assert len(self.recorder.recordings) == 0

    def test_integration_with_real_mp4_writer(self):
        """Test actual MP4Writer integration."""
        # Use real writer factory (default)
        recorder = Recorder(
            output_dir=self.temp_dir,
            width=320,
            height=240,
            fps=30.0,
            # No writer_factory override - uses default BackgroundWriter(MP4Writer)
        )

        try:
            recorder.start("real_test")

            # Write a few frames
            for _i in range(3):
                frame = create_solid_frame((255, 0, 0), width=320, height=240)
                success = recorder.write("real_test", frame)
                assert success

            # Stop and verify file exists
            final_path = recorder.stop("real_test")
            assert Path(final_path).exists()
            assert Path(final_path).stat().st_size > 0

        finally:
            recorder.close()


class TestRecorderThreadSafety:
    """Thread safety tests with deterministic synchronization."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_writers = {}

        def mock_factory(path):
            writer = MockWriter(path)
            self.mock_writers[str(path)] = writer
            return writer

        self.recorder = Recorder(
            output_dir=self.temp_dir,
            width=640,
            height=480,
            fps=30.0,
            writer_factory=mock_factory,
        )

    def teardown_method(self):
        self.recorder.close()

    def test_concurrent_writes_maintain_frame_integrity(self):
        """Test that concurrent writes don't corrupt frames."""
        self.recorder.start("test")

        # Get the mock writer to verify frame data
        _, metadata = self.recorder.recordings["test"]
        mock_writer = self.mock_writers[metadata["file_path"]]

        results = []
        barrier = threading.Barrier(3)  # 3 threads

        def write_unique_frames(thread_id):
            barrier.wait()  # Synchronize start
            for i in range(10):
                # Create frame with unique pattern for this thread
                frame = np.full((480, 640, 3), thread_id * 100 + i, dtype=np.uint8)
                success = self.recorder.write("test", frame)
                results.append((thread_id, i, success))

        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=write_unique_frames, args=(thread_id,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All writes should succeed
        assert all(success for _, _, success in results)
        assert len(results) == 30

        # Verify all frames were written (30 total)
        assert len(mock_writer.frames) == 30

        # Verify no frames were corrupted (each should have uniform values)
        for frame in mock_writer.frames:
            unique_values = np.unique(frame)
            assert len(unique_values) == 1, (
                f"Frame corrupted: has {len(unique_values)} unique values"
            )

        # Verify frame count is correct
        status = self.recorder.status("test")
        assert status["frame_count"] == 30

    def test_concurrent_start_stop_operations(self):
        """Test concurrent start/stop operations are handled safely."""
        results = []
        barrier = threading.Barrier(5)  # 5 threads

        def start_stop_cycle(recording_id):
            barrier.wait()  # Synchronize start
            try:
                path = self.recorder.start(recording_id)
                if path:
                    frame = create_test_frame(width=640, height=480)
                    write_success = self.recorder.write(recording_id, frame)
                    final_path = self.recorder.stop(recording_id)
                    results.append((recording_id, path == final_path and write_success))
                else:
                    results.append((recording_id, False))
            except Exception as e:
                results.append((recording_id, f"Error: {e}"))

        threads = []
        for i in range(5):
            thread = threading.Thread(target=start_stop_cycle, args=(f"test_{i}",))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All operations should complete successfully
        assert len(results) == 5
        for recording_id, success in results:
            assert success is True, f"Failed for {recording_id}: {success}"

        # No recordings should be active
        assert len(self.recorder.recordings) == 0

        # Verify all writers were properly closed
        assert len(self.mock_writers) == 5
        for writer in self.mock_writers.values():
            assert writer.closed

    def test_concurrent_same_id_start_operations(self):
        """Test concurrent start operations with same ID are handled safely."""
        paths = []
        barrier = threading.Barrier(3)  # 3 threads

        def start_same_id():
            barrier.wait()  # Synchronize start
            path = self.recorder.start("same_id")
            paths.append(path)

        threads = []
        for _ in range(3):
            thread = threading.Thread(target=start_same_id)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All threads should get the same path
        assert len(paths) == 3
        assert all(path == paths[0] for path in paths)

        # Only one recording should exist
        assert len(self.recorder.recordings) == 1
        assert "same_id" in self.recorder.recordings

    def test_deterministic_write_stop_race_condition(self):
        """Test race condition between write and stop operations with deterministic control."""
        self.recorder.start("race_test")

        # Get the mock writer to control when it closes
        _, metadata = self.recorder.recordings["race_test"]
        mock_writer = self.mock_writers[metadata["file_path"]]

        results = {"writes": [], "stop_result": None}
        write_barrier = threading.Barrier(2)
        # Use a semaphore to signal when enough writes have happened
        write_counter = threading.Semaphore(0)
        stop_signal = threading.Event()

        def controlled_writer():
            write_barrier.wait()  # Wait for both threads to be ready

            # Write frames until signaled to stop or writer is closed
            for i in range(20):  # Reduced from 100 for faster test
                if stop_signal.is_set() or mock_writer.close_event.is_set():
                    break

                frame = create_test_frame(i, width=640, height=480)
                success = self.recorder.write("race_test", frame)
                results["writes"].append(success)

                # Signal that a write completed
                write_counter.release()

        def controlled_stopper():
            write_barrier.wait()  # Wait for both threads to be ready

            # Wait for at least 5 writes to complete
            for _ in range(5):
                write_counter.acquire()  # Block until a write completes

            # Signal writer to stop and then stop the recording
            stop_signal.set()
            stop_result = self.recorder.stop("race_test")
            results["stop_result"] = stop_result

        writer_thread = threading.Thread(target=controlled_writer)
        stopper_thread = threading.Thread(target=controlled_stopper)

        writer_thread.start()
        stopper_thread.start()

        # Join with timeout to prevent hanging
        writer_thread.join(timeout=2.0)
        stopper_thread.join(timeout=2.0)

        # Verify threads completed
        assert not writer_thread.is_alive(), "Writer thread should have completed"
        assert not stopper_thread.is_alive(), "Stopper thread should have completed"

        # Stop should have succeeded
        assert results["stop_result"] is not None
        assert results["stop_result"].endswith(".mp4")

        # At least 5 writes should have succeeded before stop
        successful_writes = sum(1 for success in results["writes"] if success)
        assert successful_writes >= 5, (
            f"At least 5 writes should have succeeded, got {successful_writes}"
        )

        # Recording should be removed
        assert "race_test" not in self.recorder.recordings
