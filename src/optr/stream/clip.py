"""Simple clip recorder for streaming."""

import os
import time
from typing import Optional
import numpy as np
import cv2
from optr.core.io import Writer


class ClipRecorder(Writer[np.ndarray]):
    """Record video clips from a stream."""
    
    def __init__(self, output_dir: str = "./clips", fps: float = 30.0):
        """Initialize clip recorder.
        
        Args:
            output_dir: Directory to save clips
            fps: Frames per second for recorded clips
        """
        self.output_dir = output_dir
        self.fps = fps
        self.recording = False
        self.current_writer: Optional[cv2.VideoWriter] = None
        self.current_filename: Optional[str] = None
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def start_recording(self, filename: Optional[str] = None) -> str:
        """Start recording a new clip.
        
        Args:
            filename: Optional filename. If None, auto-generates based on timestamp
            
        Returns:
            The filename being recorded to
        """
        if self.recording:
            self.stop_recording()
        
        if filename is None:
            timestamp = int(time.time())
            filename = f"clip_{timestamp}.mp4"
        
        self.current_filename = filename
        filepath = os.path.join(self.output_dir, filename)
        
        # VideoWriter will be created when first frame is written
        # (we need frame dimensions)
        self.current_writer = None
        self.recording = True
        
        print(f"Started recording clip: {filepath}")
        return filename
    
    def stop_recording(self) -> str | None:
        """Stop recording current clip.
        
        Returns:
            Filename of the recorded clip, or None if not recording
        """
        if not self.recording:
            return None
        
        filename = self.current_filename
        
        if self.current_writer:
            self.current_writer.release()
            self.current_writer = None
        
        self.recording = False
        self.current_filename = None
        
        if filename:
            filepath = os.path.join(self.output_dir, filename)
            print(f"Stopped recording clip: {filepath}")
        
        return filename
    
    def write(self, frame: np.ndarray) -> None:
        """Write frame if currently recording.
        
        Args:
            frame: Frame data as numpy array (BGR format for OpenCV)
        """
        if not self.recording:
            return
        
        # Create VideoWriter on first frame (need dimensions)
        if self.current_writer is None:
            height, width = frame.shape[:2]
            filepath = os.path.join(self.output_dir, self.current_filename)
            
            # Define codec and create VideoWriter
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.current_writer = cv2.VideoWriter(
                filepath, fourcc, self.fps, (width, height)
            )
            
            if not self.current_writer.isOpened():
                print(f"Failed to open video writer for {filepath}")
                self.recording = False
                return
        
        # Write frame
        self.current_writer.write(frame)
    
    def close(self) -> None:
        """Close the clip recorder and stop any active recording."""
        if self.recording:
            self.stop_recording()
    
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self.recording