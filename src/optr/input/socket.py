"""Base socket input class."""

import json
import os
import socket
import threading
import time
from typing import Any


class BaseSocketInput:
    """Base class for all socket-based input sources."""

    def __init__(
        self, path: str, max_conn: int = 5, timeout: float = 1.0, buffer: int = 1024
    ):
        self.path = path
        self.max_conn = max_conn
        self.timeout = timeout
        self.buffer = buffer

        self.running = False
        self.socket = None
        self.thread = None
        self.lock = threading.Lock()

        # Statistics
        self.stats = {"commands": 0, "errors": 0, "connections": 0, "start": None}

    def _cleanup(self):
        """Remove existing socket file if it exists."""
        if os.path.exists(self.path):
            os.unlink(self.path)

        # Ensure socket directory exists
        dir = os.path.dirname(self.path)
        if dir and not os.path.exists(dir):
            os.makedirs(dir, exist_ok=True)

    def start(self):
        """Start the socket server."""
        if self.running:
            return

        self._cleanup()

        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(self.path)
        self.socket.listen(self.max_conn)
        self.socket.settimeout(self.timeout)

        self.running = True
        self.stats["start"] = time.time()

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

        print(f"{self.__class__.__name__} started on {self.path}")

    def stop(self):
        """Stop the socket server."""
        print(f"Stopping {self.__class__.__name__}...")
        self.running = False

        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass

        self._cleanup()
        print(f"{self.__class__.__name__} stopped.")

    def _run(self):
        """Run the socket server in a separate thread."""
        while self.running:
            try:
                conn, _ = self.socket.accept()
                conn.settimeout(self.timeout)
                self.stats["connections"] += 1
                self._handle(conn)
            except TimeoutError:
                continue
            except Exception as e:
                if self.running:
                    print(f"{self.__class__.__name__} server error: {e}")
                    self.stats["errors"] += 1

    def _handle(self, conn):
        """Handle a client connection."""
        buf = ""
        try:
            while self.running:
                try:
                    data = conn.recv(self.buffer).decode("utf-8")
                    if not data:
                        break

                    buf += data

                    # Process complete lines
                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        if line.strip():
                            self._process(conn, line.strip())

                except TimeoutError:
                    continue
                except Exception as e:
                    print(f"{self.__class__.__name__} connection error: {e}")
                    self.stats["errors"] += 1
                    break
        finally:
            conn.close()

    def _process(self, conn, line):
        """Process a command and send response."""
        try:
            parts = line.split(":")
            if not parts:
                self._send(conn, "ERR", ["INVALID_FORMAT", "Empty command"])
                return

            cmd = parts[0].upper()
            params = parts[1:] if len(parts) > 1 else []

            self.stats["commands"] += 1

            # Handle common commands
            if cmd == "STATUS":
                self._status(conn)
            else:
                # Delegate to subclass
                success, response = self.handle(cmd, params)
                if success:
                    self._send(conn, "OK", [response] if response else [])
                else:
                    self._send(
                        conn,
                        "ERR",
                        response.split(":") if response else ["UNKNOWN_ERROR"],
                    )

        except Exception as e:
            self.stats["errors"] += 1
            self._send(conn, "ERR", ["INTERNAL_ERROR", str(e)])

    def _status(self, conn):
        """Handle STATUS command."""
        status = self.status()
        self._send(conn, "STATUS", [json.dumps(status)])

    def _send(self, conn, type: str, params: list):
        """Send a response to the client."""
        response = f"{type}:{':'.join(str(p) for p in params)}\n"
        try:
            conn.send(response.encode("utf-8"))
        except Exception:
            pass

    def handle(self, cmd: str, params: list) -> tuple[bool, str]:
        """Handle a command. Override in subclasses."""
        return False, "NOT_IMPLEMENTED"

    def status(self) -> dict[str, Any]:
        """Get status. Override in subclasses for additional info."""
        uptime = time.time() - self.stats["start"] if self.stats["start"] else 0
        return {
            "controller": self.__class__.__name__,
            "socket": self.path,
            "running": self.running,
            "uptime": uptime,
            "stats": self.stats,
        }
