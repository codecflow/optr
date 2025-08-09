"""
Desktop connector module
"""

import platform

from .base import Desktop
from .linux import LinuxDesktop
from .macos import MacOSDesktop


def create_desktop() -> Desktop:
    """Create platform-specific desktop connector"""
    system = platform.system().lower()

    if system == "darwin":
        return MacOSDesktop()
    elif system == "linux":
        return LinuxDesktop()
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


__all__ = ["Desktop", "MacOSDesktop", "LinuxDesktop", "create_desktop"]
