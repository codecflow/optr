"""Simplified video recorder with clean API."""

import time
from collections.abc import Callable
from pathlib import Path

import numpy as np

from optr.core.io.writer import BackgroundWriter, Closable
from optr.stream.mp4 import MP4Writer


class Recorder:
    """Video recorder with simplified API."""

    def __init__(
        self,
        output_dir: str = "/recordings",
        width: int = 1280,
        height: int = 720,
        fps: float = 24.0,
        writer_factory: Callable[[Path], Closable] | None = None,
    ):
        """Initialize recorder.

        Args:
            output_dir: Directory to save recordings
            width: Frame width
            height: Frame height
            fps: Frames per second
            writer_factory: Factory function to create writers (defaults to BackgroundWriter(MP4Writer))
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Video settings
        self.width = width
        self.height = height
        self.fps = fps

        # Writer factory - defaults to background MP4 writer for non-blocking writes
        self.writer_factory = writer_factory or (
            lambda path: BackgroundWriter(MP4Writer(path, width, height, fps))
        )

        # Active recordings: id -> (Writer, metadata)
        self.recordings: dict[str, tuple[Closable, dict]] = {}

    def start(self, id: str) -> str:
        """Start recording.

        Args:
            id: Recording identifier

        Returns:
            str: Path to recording file
        """
        # If already recording this id, return existing path
        if id in self.recordings:
            return self.recordings[id][1]["file_path"]

        # Generate filename
        timestamp = int(time.time() * 1000)
        filename = f"recording_{id}_{timestamp}.mp4"
        output_path = self.output_dir / filename

        # Create writer
        writer = self.writer_factory(output_path)

        # Create metadata
        metadata = {
            "start_time": time.time(),
            "frame_count": 0,
            "status": "recording",
            "file_path": str(output_path),
        }

        # Track recording
        self.recordings[id] = (writer, metadata)

        return str(output_path)

    def stop(self, id: str) -> str | None:
        """Stop recording.

        Args:
            id: Recording identifier

        Returns:
            str: Path to recording file, or None if not found
        """
        if id not in self.recordings:
            return None

        # Get the recording components
        writer, metadata = self.recordings.pop(id)

        # Update metadata
        metadata["status"] = "completed"
        metadata["end_time"] = time.time()
        metadata["duration"] = metadata["end_time"] - metadata["start_time"]

        # Stop the writer
        writer.close()

        return metadata["file_path"]

    def write(
        self, id: str, frames: bytes | np.ndarray | list[bytes | np.ndarray]
    ) -> bool:
        """Write frames to recording.

        Args:
            id: Recording identifier
            frames: Single frame or list of frames (bytes or numpy arrays)

        Returns:
            bool: True if frames were written successfully
        """
        if id not in self.recordings:
            return False

        writer, metadata = self.recordings[id]

        # Handle single frame or list of frames
        frame_list = frames if isinstance(frames, list) else [frames]

        try:
            for frame in frame_list:
                # Convert bytes to numpy array if needed
                if isinstance(frame, bytes):
                    frame_array = np.frombuffer(frame, dtype=np.uint8)
                    frame = frame_array.reshape((self.height, self.width, 3))

                # Write frame
                writer.write(frame)
                metadata["frame_count"] += 1

            return True

        except Exception as e:
            print(f"Warning: Failed to write frames to recording {id}: {e}")
            return False

    def close(self):
        """Close all recordings and clean up resources."""
        # Stop all active recordings
        for id in list(self.recordings.keys()):
            self.stop(id)

    def prune(self, age: float) -> int:
        """Remove old recording files.

        Args:
            age: Maximum age in seconds

        Returns:
            int: Number of files removed
        """
        cutoff_time = time.time() - age
        removed_count = 0

        try:
            for file_path in self.output_dir.glob("recording_*.mp4"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    removed_count += 1
        except Exception as e:
            print(f"Warning: Failed to prune old recordings: {e}")

        return removed_count

    def delete(self, id: str) -> bool:
        """Delete a recording.

        Args:
            id: Recording identifier

        Returns:
            bool: True if recording was deleted successfully
        """
        # Stop recording if active
        if id in self.recordings:
            self.stop(id)

        # Find and delete file
        try:
            for file_path in self.output_dir.glob(f"recording_{id}_*.mp4"):
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Warning: Failed to delete recording {id}: {e}")
            return False

    def status(self, id: str) -> dict | None:
        """Get recording status.

        Args:
            id: Recording identifier

        Returns:
            dict: Recording status information, or None if not found
        """
        if id not in self.recordings:
            return None

        writer, metadata = self.recordings[id]

        status_info = metadata.copy()

        if metadata["status"] == "recording":
            status_info["duration"] = time.time() - metadata["start_time"]

        # Add writer stats if available
        if hasattr(writer, "queued") and hasattr(writer, "written"):
            status_info["queued"] = writer.queued
            status_info["written"] = writer.written

        return status_info

    def file(self, id: str) -> str | None:
        """Get recording file path.

        Args:
            id: Recording identifier

        Returns:
            str: File path, or None if not found
        """
        if id in self.recordings:
            _, metadata = self.recordings[id]
            return metadata["file_path"]

        # Check for completed recordings
        for file_path in self.output_dir.glob(f"recording_{id}_*.mp4"):
            return str(file_path)

        return None

    def list(self) -> dict[str, dict]:
        """List all active recordings.

        Returns:
            dict: Map of recording id to status information
        """
        result = {}

        for id, (writer, metadata) in self.recordings.items():
            status_info = metadata.copy()

            if metadata["status"] == "recording":
                status_info["duration"] = time.time() - metadata["start_time"]

            # Add writer stats if available
            if hasattr(writer, "queued") and hasattr(writer, "written"):
                status_info["queued"] = writer.queued
                status_info["written"] = writer.written

            result[id] = status_info

        return result
