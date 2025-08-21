"""Utility functions for GStreamer streaming."""

import os


def delete_socket(socket_path: str) -> None:
    """Delete socket file if it exists."""
    try:
        os.remove(socket_path)
    except FileNotFoundError:
        pass


def get_format_info(format: str) -> tuple[int, str]:
    """Get channels and GStreamer format string for a given format."""
    formats = {
        "RGB": (3, "RGB"),
        "RGBA": (4, "RGBA"),
        "I420": (1, "I420"),  # YUV format - 1.5 bytes per pixel but simplified to 1
        "NV12": (1, "NV12"),  # YUV format - 1.5 bytes per pixel but simplified to 1
    }
    if format not in formats:
        raise ValueError(
            f"Unsupported format: {format}. Supported: {list(formats.keys())}"
        )
    return formats[format]


def create_caps_string(width: int, height: int, fps: float, format: str) -> str:
    """Create GStreamer caps string for video."""
    return f"video/x-raw,format={format},width={width},height={height},framerate={int(fps)}/1"
