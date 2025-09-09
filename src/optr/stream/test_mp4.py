"""Focused test suite for MP4Writer."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

from .mp4 import MP4Writer


class TestMP4Writer:
    """Test MP4Writer wrapper functionality."""

    @patch("optr.stream.mp4.imageio.get_writer")
    def test_init_delegates_to_imageio(self, mock_get_writer):
        """Test initialization passes correct parameters to imageio."""
        mock_writer = MagicMock()
        mock_get_writer.return_value = mock_writer

        path = Path("test.mp4")
        writer = MP4Writer(
            path, width=640, height=480, fps=24.0, codec="h264", quality=5
        )

        mock_get_writer.assert_called_once_with(
            str(path),
            fps=24.0,
            codec="h264",
            quality=5,
            pixelformat="yuv420p",
            macro_block_size=1,
        )
        assert writer.path == path
        assert writer.width == 640
        assert writer.height == 480
        assert not writer._closed
        assert writer.writer is mock_writer

    @patch("optr.stream.mp4.imageio.get_writer")
    def test_write_delegates_to_imageio(self, mock_get_writer):
        """Test write method delegates to imageio writer."""
        mock_writer = MagicMock()
        mock_get_writer.return_value = mock_writer

        writer = MP4Writer(Path("test.mp4"), width=640, height=480)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        writer.write(frame)

        mock_writer.append_data.assert_called_once_with(frame)

    @patch("optr.stream.mp4.imageio.get_writer")
    def test_write_after_close_ignored(self, mock_get_writer):
        """Test write after close is ignored."""
        mock_writer = MagicMock()
        mock_get_writer.return_value = mock_writer

        writer = MP4Writer(Path("test.mp4"), width=640, height=480)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        writer.close()
        writer.write(frame)

        mock_writer.append_data.assert_not_called()

    @patch("optr.stream.mp4.imageio.get_writer")
    def test_close_delegates_to_imageio(self, mock_get_writer):
        """Test close method delegates to imageio writer."""
        mock_writer = MagicMock()
        mock_get_writer.return_value = mock_writer

        writer = MP4Writer(Path("test.mp4"), width=640, height=480)
        writer.close()

        mock_writer.close.assert_called_once()
        assert writer._closed

    @patch("optr.stream.mp4.imageio.get_writer")
    def test_multiple_close_safe(self, mock_get_writer):
        """Test multiple close calls are safe."""
        mock_writer = MagicMock()
        mock_get_writer.return_value = mock_writer

        writer = MP4Writer(Path("test.mp4"), width=640, height=480)

        writer.close()
        writer.close()
        writer.close()

        mock_writer.close.assert_called_once()
        assert writer._closed

    @patch("optr.stream.mp4.imageio.get_writer")
    def test_write_when_writer_none_ignored(self, mock_get_writer):
        """Test write when writer is None is ignored."""
        mock_get_writer.return_value = None

        writer = MP4Writer(Path("test.mp4"), width=640, height=480)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Should not raise exception
        writer.write(frame)
        writer.close()

    @patch("optr.stream.mp4.imageio.get_writer")
    def test_close_when_writer_none_safe(self, mock_get_writer):
        """Test close when writer is None is safe."""
        mock_get_writer.return_value = None

        writer = MP4Writer(Path("test.mp4"), width=640, height=480)

        # Should not raise exception
        writer.close()
        # When writer is None, _closed doesn't get set - that's the actual behavior
        assert not writer._closed
