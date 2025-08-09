"""
Linux desktop connector
"""

from .base import Desktop


class LinuxDesktop(Desktop):
    """Linux-specific desktop connector"""

    def __init__(self):
        try:
            import pyautogui

            self.gui = pyautogui
            self.gui.FAILSAFE = False
        except ImportError as e:
            raise RuntimeError("pyautogui required for Linux desktop control") from e

    async def screenshot(self) -> bytes:
        """Take screenshot on Linux"""
        screenshot = self.gui.screenshot()
        import io

        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        return buffer.getvalue()

    async def click(self, x: int, y: int) -> bool:
        """Click at coordinates on Linux"""
        try:
            self.gui.click(x, y)
            return True
        except Exception:
            return False

    async def type_text(self, text: str) -> bool:
        """Type text on Linux"""
        try:
            self.gui.write(text)
            return True
        except Exception:
            return False

    async def key(self, key: str) -> bool:
        """Press key on Linux"""
        try:
            self.gui.press(key)
            return True
        except Exception:
            return False
