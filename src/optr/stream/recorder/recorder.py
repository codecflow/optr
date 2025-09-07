"""Queue-based video recorder for improved I/O performance."""

import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import imageio
import numpy as np


class Recorder:
    """Video recorder with queue-based architecture for improved performance."""

    def __init__(
        self,
        output_dir: str = "/recordings",
        width: int = 1280,
        height: int = 720,
        fps: float = 24.0,
    ):
        """Initialize recorder.

        Args:
            output_dir: Directory to save recordings
            width: Frame width
            height: Frame height
            fps: Frames per second
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Video settings
        self.width = width
        self.height = height
        self.fps = fps

        # Queue-based architecture
        self.frame_queue: queue.Queue = queue.Queue(maxsize=0)  # Unlimited queue
        self.writer_thread = None
        self.writer_active = False
        self.shutdown_event = threading.Event()

        # Recording state
        self.is_recording = False
        self.current_action_id: str | None = None
        self.writer: imageio.core.Format.Writer | None = None
        self.recording_file_path: Path | None = None

        # Threading
        self.lock = threading.Lock()

        # Async finalization
        self.finalization_executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="recorder-finalize"
        )

        # Track active recordings
        self.active_recordings: dict[str, dict] = {}

        # Event callbacks
        self.on_recording_finalized = None

        # Frame tracking
        self.frames_queued = 0
        self.frames_written = 0

    def start_recording(self, action_id: str) -> str:
        """Start recording for an action.

        Args:
            action_id: Unique action identifier

        Returns:
            str: Path to recording file
        """
        start_time = time.time()
        with self.lock:
            # Check if we're already recording this same action
            if self.is_recording and self.current_action_id == action_id:
                print(
                    f"🔄 [{time.strftime('%H:%M:%S.%f')[:-3]}] Already recording action {action_id}, continuing..."
                )
                return str(self.recording_file_path) if self.recording_file_path else ""

            # Stop current recording only if it's a different action
            if self.is_recording and self.current_action_id != action_id:
                print(
                    f"🔄 [{time.strftime('%H:%M:%S.%f')[:-3]}] Stopping previous recording for {self.current_action_id} to start {action_id}"
                )
                self._stop_current_recording()

            # Generate filename
            timestamp = int(time.time() * 1000)
            filename = f"action_{action_id}_{timestamp}.mp4"
            self.recording_file_path = self.output_dir / filename

            # Initialize video writer
            self.writer = imageio.get_writer(
                str(self.recording_file_path),
                fps=self.fps,
                codec="libx264",
                quality=8,  # Good quality, reasonable file size
                pixelformat="yuv420p",  # Compatible with most players
                macro_block_size=1,  # Prevent resizing warnings for non-16-divisible resolutions
            )

            # Reset frame counters
            self.frames_queued = 0
            self.frames_written = 0

            # Set recording state
            self.is_recording = True
            self.current_action_id = action_id

            # Start writer thread if not active
            if not self.writer_active:
                self._start_writer_thread()

            # Track recording
            self.active_recordings[action_id] = {
                "file_path": str(self.recording_file_path),
                "start_time": start_time,
                "status": "recording",
                "frame_count": 0,
            }

            print(
                f"🎬 [{time.strftime('%H:%M:%S.%f')[:-3]}] Starting recording for action {action_id}"
            )
            return str(self.recording_file_path)

    def add_frame(self, frame_bytes: bytes):
        """Add a frame to the recording queue.

        Args:
            frame_bytes: Raw RGB frame bytes
        """
        if not self.is_recording:
            return

        try:
            # Convert bytes to numpy array
            frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = frame_array.reshape((self.height, self.width, 3))

            # Create frame data with metadata
            frame_data = {
                "frame": frame.copy(),
                "action_id": self.current_action_id,
                "timestamp": time.time(),
                "frame_number": self.frames_queued,
            }

            # Add to queue (non-blocking)
            self.frame_queue.put_nowait(frame_data)
            self.frames_queued += 1

            # Update frame count
            if (
                self.current_action_id
                and self.current_action_id in self.active_recordings
            ):
                self.active_recordings[self.current_action_id]["frame_count"] += 1
                frame_count = self.active_recordings[self.current_action_id][
                    "frame_count"
                ]
                if (
                    frame_count <= 5 or frame_count % 90 == 0
                ):  # Log first 5 frames, then every 3 seconds
                    print(
                        f"📹 Frame {frame_count} added to recording {self.current_action_id}"
                    )

        except queue.Full:
            print(
                f"Warning: Frame queue full, dropping frame for {self.current_action_id}"
            )
        except Exception as e:
            print(f"Warning: Failed to add frame to recording: {e}")

    def stop_recording(self, action_id: str) -> str | None:
        """Stop recording for an action (non-blocking).

        Args:
            action_id: Action identifier

        Returns:
            str: Path to recording file, or None if not found
        """
        with self.lock:
            if not self.is_recording or self.current_action_id != action_id:
                return None

            # Get frame count before stopping
            frame_count = 0
            if action_id in self.active_recordings:
                frame_count = self.active_recordings[action_id]["frame_count"]
                duration = time.time() - self.active_recordings[action_id]["start_time"]
                print(
                    f"⏹️ [{time.strftime('%H:%M:%S.%f')[:-3]}] Stopping recording for action {action_id} - {frame_count} frames in {duration:.3f}s"
                )
            else:
                print(
                    f"⏹️ [{time.strftime('%H:%M:%S.%f')[:-3]}] Stopping recording for action {action_id}"
                )

            return self._stop_current_recording_async()

    def _start_writer_thread(self):
        """Start the persistent writer thread."""
        if self.writer_active:
            return

        self.writer_active = True
        self.shutdown_event.clear()
        self.writer_thread = threading.Thread(
            target=self._writer_loop, daemon=False, name="queue-recorder-writer"
        )
        self.writer_thread.start()
        print(f"🚀 [{time.strftime('%H:%M:%S.%f')[:-3]}] Writer thread started")

    def _writer_loop(self):
        """Persistent writer thread that processes the frame queue."""
        print(f"📝 [{time.strftime('%H:%M:%S.%f')[:-3]}] Writer loop started")

        while self.writer_active and not self.shutdown_event.is_set():
            try:
                # Get frame from queue with timeout
                frame_data = self.frame_queue.get(timeout=0.1)

                # Check for EOS (End-Of-Stream) sentinel
                if frame_data.get("type") == "EOS":
                    action_id = frame_data.get("action_id")
                    print(f"📝 [{time.strftime('%H:%M:%S.%f')[:-3]}] EOS received for {action_id}")
                    
                    # Close writer for this action
                    with self.lock:
                        if self.writer and self.current_action_id == action_id:
                            try:
                                print(f"🔒 [{time.strftime('%H:%M:%S.%f')[:-3]}] Closing writer for {action_id}")
                                self.writer.close()
                                print(f"✅ [{time.strftime('%H:%M:%S.%f')[:-3]}] Writer closed for {action_id}")
                            except Exception as e:
                                print(f"❌ Error closing writer for {action_id}: {e}")
                            finally:
                                self.writer = None
                    
                    # Mark task as done
                    self.frame_queue.task_done()
                    continue

                # Process regular frame data
                with self.lock:  # Protect writer access
                    if (
                        self.writer
                        and frame_data.get("action_id") == self.current_action_id
                    ):
                        # Write frame to video
                        self.writer.append_data(frame_data["frame"])
                        self.frames_written += 1

                        # Log progress occasionally
                        if self.frames_written % 100 == 0:
                            print(f"📝 Written {self.frames_written} frames to video")

                # Mark task as done
                self.frame_queue.task_done()

            except queue.Empty:
                # No frames to process, continue loop
                continue
            except Exception as e:
                print(f"Warning: Error in writer loop: {e}")
                continue

        print(f"🛑 [{time.strftime('%H:%M:%S.%f')[:-3]}] Writer loop stopped")

    def _stop_current_recording_async(self) -> str | None:
        """Stop the current recording asynchronously (non-blocking)."""
        if not self.is_recording:
            return None

        # Capture current state
        action_id = self.current_action_id
        file_path = str(self.recording_file_path) if self.recording_file_path else None

        # Update recording status to "finalizing" immediately
        if action_id and action_id in self.active_recordings:
            recording = self.active_recordings[action_id]
            recording["status"] = "finalizing"
            recording["end_time"] = time.time()
            recording["duration"] = recording["end_time"] - recording["start_time"]

        # Send EOS sentinel to queue to signal end of recording
        if action_id:
            eos_sentinel = {
                "type": "EOS",
                "action_id": action_id,
                "timestamp": time.time(),
            }
            try:
                self.frame_queue.put_nowait(eos_sentinel)
                print(f"📤 [{time.strftime('%H:%M:%S.%f')[:-3]}] EOS sentinel sent for {action_id}")
            except queue.Full:
                print(f"⚠️ Queue full, could not send EOS sentinel for {action_id}")

        # Reset recording state immediately (non-blocking)
        self.is_recording = False
        self.current_action_id = None
        self.writer = None
        self.recording_file_path = None

        print(
            f"🔄 [{time.strftime('%H:%M:%S.%f')[:-3]}] Recording stop initiated for {action_id}"
        )
        return file_path

    def _finalize_recording_async(
        self,
        action_id: str,
        writer,
        file_path: str | None,
    ):
        """Finalize recording in background thread."""
        try:
            print(
                f"🔧 [{time.strftime('%H:%M:%S.%f')[:-3]}] Starting async finalization for {action_id}"
            )

            # Wait for queue to drain (all frames for this recording)
            print(
                f"⏳ [{time.strftime('%H:%M:%S.%f')[:-3]}] Waiting for queue to drain..."
            )

            # Wait for remaining frames to be processed
            max_wait = 30  # Maximum 30 seconds
            wait_start = time.time()
            while (
                not self.frame_queue.empty() and (time.time() - wait_start) < max_wait
            ):
                time.sleep(0.1)

            if not self.frame_queue.empty():
                print(
                    f"⚠️ Queue not fully drained after {max_wait}s, proceeding with finalization"
                )

            # Close video writer
            if writer:
                print(
                    f"🔒 [{time.strftime('%H:%M:%S.%f')[:-3]}] Finalizing video file..."
                )
                writer.close()
                print(
                    f"✅ [{time.strftime('%H:%M:%S.%f')[:-3]}] Video file finalized: {file_path}"
                )

            # Update recording status to completed
            recording_info = None
            with self.lock:
                if action_id in self.active_recordings:
                    self.active_recordings[action_id]["status"] = "completed"
                    recording_info = self.active_recordings[action_id].copy()

            # Emit recording finalized event
            if self.on_recording_finalized and recording_info:
                try:
                    # Get file size
                    file_size = 0
                    if file_path and Path(file_path).exists():
                        file_size = Path(file_path).stat().st_size

                    # Create recording info for callback
                    callback_recording_info = {
                        "file_path": recording_info["file_path"],
                        "duration": recording_info.get("duration", 0),
                        "frame_count": recording_info.get("frame_count", 0),
                        "file_size": file_size,
                        "status": "completed",
                    }

                    self.on_recording_finalized(action_id, callback_recording_info)
                except Exception as e:
                    print(f"Warning: Error emitting recording finalized event: {e}")

        except Exception as e:
            print(
                f"❌ [{time.strftime('%H:%M:%S.%f')[:-3]}] Error finalizing recording {action_id}: {e}"
            )
            # Update status to error
            with self.lock:
                if action_id in self.active_recordings:
                    self.active_recordings[action_id]["status"] = "error"
                    self.active_recordings[action_id]["error"] = str(e)

    def _stop_current_recording(self) -> str | None:
        """Stop the current recording and finalize the video file."""
        if not self.is_recording:
            return None

        # Wait for queue to drain
        print("⏳ Waiting for frame queue to drain...")
        max_wait = 15
        wait_start = time.time()
        while not self.frame_queue.empty() and (time.time() - wait_start) < max_wait:
            time.sleep(0.1)

        # Close video writer and ensure proper finalization
        if self.writer:
            try:
                print("🔒 Finalizing video file...")
                self.writer.close()
                print(f"✅ Video file finalized: {self.recording_file_path}")
            except Exception as e:
                print(f"Warning: Error closing video writer: {e}")
            finally:
                self.writer = None

        # Update recording status
        file_path = str(self.recording_file_path) if self.recording_file_path else None
        if self.current_action_id and self.current_action_id in self.active_recordings:
            recording = self.active_recordings[self.current_action_id]
            recording["status"] = "completed"
            recording["end_time"] = time.time()
            recording["duration"] = recording["end_time"] - recording["start_time"]

        # Reset state
        self.is_recording = False
        self.current_action_id = None
        self.recording_file_path = None

        return file_path

    def close(self):
        """Clean up resources."""
        print(f"🔄 [{time.strftime('%H:%M:%S.%f')[:-3]}] Starting recorder cleanup...")
        
        # Stop any active recording first
        with self.lock:
            if self.is_recording and self.current_action_id:
                print(f"🛑 [{time.strftime('%H:%M:%S.%f')[:-3]}] Stopping active recording: {self.current_action_id}")
                # Send EOS sentinel for current recording
                eos_sentinel = {
                    "type": "EOS",
                    "action_id": self.current_action_id,
                    "timestamp": time.time(),
                }
                try:
                    self.frame_queue.put_nowait(eos_sentinel)
                except queue.Full:
                    print("⚠️ Queue full during cleanup, forcing writer close")
                    if self.writer:
                        try:
                            self.writer.close()
                        except Exception as e:
                            print(f"Warning: Error closing writer during cleanup: {e}")
                        finally:
                            self.writer = None
                
                self.is_recording = False
                self.current_action_id = None
                self.recording_file_path = None

        # Signal shutdown to writer thread
        self.writer_active = False
        self.shutdown_event.set()

        # Wait for writer thread to finish processing
        if self.writer_thread and self.writer_thread.is_alive():
            print(f"⏳ [{time.strftime('%H:%M:%S.%f')[:-3]}] Waiting for writer thread to finish...")
            self.writer_thread.join(timeout=10)
            
            if self.writer_thread.is_alive():
                print("⚠️ Writer thread did not stop gracefully within timeout")

        # Clear any remaining items in queue
        try:
            while not self.frame_queue.empty():
                try:
                    self.frame_queue.get_nowait()
                    self.frame_queue.task_done()
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Warning: Error clearing frame queue: {e}")

        # Shutdown finalization executor
        print(f"🔄 [{time.strftime('%H:%M:%S.%f')[:-3]}] Shutting down finalization executor...")
        try:
            self.finalization_executor.shutdown(wait=False)  # Don't wait to avoid hanging
        except Exception as e:
            print(f"Warning: Error shutting down finalization executor: {e}")

        print(f"✅ [{time.strftime('%H:%M:%S.%f')[:-3]}] Recorder cleanup completed")

    # Compatibility methods for existing ActionRecorder interface
    def get_recording_file(self, action_id: str) -> str | None:
        """Get recording file path for an action."""
        if action_id in self.active_recordings:
            recording = self.active_recordings[action_id]
            # Return path for any active recording
            return recording["file_path"]
        return None

    def get_recording_status(self, action_id: str) -> dict | None:
        """Get recording status for an action."""
        if action_id in self.active_recordings:
            return self.active_recordings[action_id].copy()
        return None

    def list_recordings(self) -> dict[str, dict]:
        """List all tracked recordings."""
        return {k: v.copy() for k, v in self.active_recordings.items()}

    def delete_recording(self, action_id: str) -> bool:
        """Delete a specific recording."""
        if action_id not in self.active_recordings:
            return False

        recording = self.active_recordings[action_id]
        file_path = Path(recording["file_path"])

        # Remove from tracking
        del self.active_recordings[action_id]

        # Delete file if it exists
        try:
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            print(f"Warning: Failed to delete recording file {file_path}: {e}")
            return False

    def cleanup_old_recordings(self, max_age_hours: int = 24):
        """Clean up old recording files."""
        cutoff_time = time.time() - (max_age_hours * 3600)

        # Clean up tracking dict
        to_remove = []
        for action_id, recording in self.active_recordings.items():
            if recording.get("end_time", 0) < cutoff_time:
                to_remove.append(action_id)

        for action_id in to_remove:
            del self.active_recordings[action_id]

        # Clean up files
        try:
            for file_path in self.output_dir.glob("action_*.mp4"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
        except Exception as e:
            print(f"Warning: Failed to clean up old recordings: {e}")
