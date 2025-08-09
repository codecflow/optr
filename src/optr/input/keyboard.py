"""Keyboard input receiver for real-time input management."""

import time
from dataclasses import dataclass
from typing import Any

from .socket import BaseSocketInput


@dataclass
class KeyboardInputConfig:
    """Keyboard input system configuration."""

    socket_path: str = "/tmp/robot/keyboard.sock"
    max_connections: int = 5
    timeout: float = 1.0


class KeyboardInput(BaseSocketInput):
    """Receives and manages keyboard-style input state via socket."""

    # Supported keys
    SUPPORTED_KEYS = {
        # Movement keys
        "w",
        "s",
        "a",
        "d",
        "q",
        "e",
        # Recording
        "r",
        # Number keys for motion switching
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "0",
        # Modifiers
        "shift",
        "ctrl",
        "alt",
        # Function keys
        "f1",
        "f2",
        "f3",
        "f4",
        # Special keys
        "space",
        "enter",
        "tab",
        "esc",
        "escape",
    }

    def __init__(self, path: str = "/tmp/robot/keyboard.sock"):
        super().__init__(path=path, max_conn=5, timeout=1.0, buffer=1024)

        # Key state tracking
        self._pressed: set[str] = set()
        self._press_times: dict[str, float] = {}
        self._release_times: dict[str, float] = {}

        # Performance metrics
        self.metrics = {"presses": 0, "releases": 0, "invalid": 0, "updated": None}

    def handle(self, cmd: str, params: list) -> tuple[bool, str]:
        """Handle input-specific commands."""
        if cmd == "PRESS":
            return self._press(params)
        elif cmd == "RELEASE":
            return self._release(params)
        else:
            return False, f"1002:INVALID_COMMAND_FORMAT:Unknown command {cmd}"

    def _press(self, params: list) -> tuple[bool, str]:
        """Handle PRESS command."""
        if not params:
            return False, "1002:INVALID_COMMAND_FORMAT:No keys specified"

        invalid = []
        pressed = []

        with self.lock:
            for key in params:
                k = key.lower()
                if k not in self.SUPPORTED_KEYS:
                    invalid.append(key)
                    self.metrics["invalid"] += 1
                else:
                    if k not in self._pressed:
                        self._pressed.add(k)
                        self._press_times[k] = time.time()
                        pressed.append(k)
                        self.metrics["presses"] += 1

            self.metrics["updated"] = time.time()

        if invalid:
            return False, f"1001:INVALID_KEY:Unsupported keys: {','.join(invalid)}"

        return True, f"Pressed: {','.join(pressed)}"

    def _release(self, params: list) -> tuple[bool, str]:
        """Handle RELEASE command."""
        if not params:
            return False, "1002:INVALID_COMMAND_FORMAT:No keys specified"

        released = []

        with self.lock:
            if len(params) == 1 and params[0].lower() == "all":
                # Release all keys
                released = list(self._pressed)
                for key in released:
                    self._release_times[key] = time.time()
                    self.metrics["releases"] += 1
                self._pressed.clear()
            else:
                # Release specific keys
                for key in params:
                    k = key.lower()
                    if k in self._pressed:
                        self._pressed.remove(k)
                        self._release_times[k] = time.time()
                        released.append(k)
                        self.metrics["releases"] += 1

            self.metrics["updated"] = time.time()

        return True, f"Released: {','.join(released)}"

    def pressed(self) -> set[str]:
        """Get currently pressed keys."""
        with self.lock:
            return self._pressed.copy()

    def duration(self, key: str) -> float | None:
        """Get how long a key has been pressed."""
        k = key.lower()
        with self.lock:
            if k in self._pressed and k in self._press_times:
                return time.time() - self._press_times[k]
        return None

    def status(self) -> dict[str, Any]:
        """Get status."""
        base = super().status()

        with self.lock:
            keys = list(self._pressed)
            durations = {}
            for key in keys:
                if key in self._press_times:
                    durations[key] = time.time() - self._press_times[key]

        base.update(
            {
                "pressed": keys,
                "durations": durations,
                "metrics": self.metrics,
                "supported": list(self.SUPPORTED_KEYS),
            }
        )

        return base

    def stop(self):
        """Stop the input receiver and cleanup."""
        # Clear key states
        with self.lock:
            self._pressed.clear()

        super().stop()
