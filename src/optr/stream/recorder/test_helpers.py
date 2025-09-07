"""Shared test utilities for recorder tests and benchmarks."""

import tempfile
from pathlib import Path

import numpy as np

from .recorder import Recorder


def create_test_frame(frame_num=0, width=640, height=480):
    """Create a test frame with specific pattern.
    
    Args:
        frame_num: Frame number for pattern variation
        width: Frame width
        height: Frame height
        
    Returns:
        bytes: Frame data as bytes
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    # Create a gradient pattern with frame counter
    for i in range(height):
        intensity = int(255 * i / height)
        frame[i, :] = (intensity, (intensity + frame_num) % 256, 255 - intensity)
    return frame.tobytes()


def setup_temp_recorder(temp_dir=None, **kwargs):
    """Set up a temporary recorder with default settings.
    
    Args:
        temp_dir: Temporary directory path (creates one if None)
        **kwargs: Additional recorder parameters
        
    Returns:
        tuple: (recorder, temp_dir)
    """
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()
    
    default_kwargs = {
        'output_dir': temp_dir,
        'width': 640,
        'height': 480,
        'fps': 30.0
    }
    default_kwargs.update(kwargs)
    
    recorder = Recorder(**default_kwargs)
    return recorder, temp_dir


def create_gradient_frame(width=640, height=480):
    """Create gradient frame using vectorized operations."""
    y_gradient = np.linspace(0, 255, height, dtype=np.uint8)
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:, :, 0] = y_gradient[:, np.newaxis]
    frame[:, :, 1] = 255 - y_gradient[:, np.newaxis]
    frame[:, :, 2] = y_gradient[:, np.newaxis] // 2
    return frame.tobytes()


def create_random_frame(width=640, height=480):
    """Create random frame data."""
    frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    return frame.tobytes()


def create_solid_frame(color=(128, 64, 192), width=640, height=480):
    """Create solid color frame."""
    frame = np.full((height, width, 3), color, dtype=np.uint8)
    return frame.tobytes()
