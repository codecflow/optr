from gi.repository import Gst

from optr.core.io.protocols import Closer, Reader
from optr.stream.fps import FPS

from . import buffer, caps, control, element, pipeline


class VideoReader(Reader[bytes], Closer):
    """Base video reader implementing Reader and Closer protocols."""

    def __init__(self, pipe: Gst.Pipeline, appsink: Gst.Element):
        self.pipe = pipe
        self.appsink = appsink
        self.eos = False

    def read(self) -> bytes | None:
        """Read next frame, returns None when no more data."""
        if self.eos:
            return None

        frame = buffer.pull(self.appsink, timeout_ns=Gst.CLOCK_TIME_NONE)
        if frame is None:
            self.eos = True
        return frame

    def close(self) -> None:
        """Close and cleanup resources."""
        control.play(self.pipe)


class SHMReader(VideoReader):
    """Shared memory reader."""

    def __init__(self, socket_path: str):
        src = element.shmsrc(socket_path=socket_path)
        sink = element.appsink()

        pipe = pipeline.chain(src, sink, name="shm-reader")
        control.play(pipe)

        super().__init__(pipe, sink)


class FileReader(VideoReader):
    """File reader with decoding."""

    def __init__(self, filepath: str):
        src = element.filesrc(location=filepath)
        decoder = element.decodebin()
        convert = element.videoconvert()
        sink = element.appsink()

        pipe = pipeline.pipeline(src, decoder, convert, sink, name="file-reader")

        # Dynamic linking for decodebin
        def on_pad_added(decodebin, pad):
            caps = pad.get_current_caps()
            if caps and caps.get_structure(0).get_name().startswith("video/"):
                convert_sink = convert.get_static_pad("sink")
                if convert_sink and not convert_sink.is_linked():
                    pad.link(convert_sink)

        decoder.connect("pad-added", on_pad_added)

        pipeline.link(src, decoder)
        pipeline.link(convert, sink)
        control.play(pipe)

        super().__init__(pipe, sink)


class RTMPReader(VideoReader):
    """RTMP stream reader."""

    def __init__(self, url: str):
        src = element.rtmpsrc(location=url)
        decoder = element.decodebin()
        convert = element.videoconvert()
        sink = element.appsink()

        pipe = pipeline.pipeline(src, decoder, convert, sink, name="rtmp-reader")

        # Dynamic linking for decodebin
        def on_pad_added(decodebin, pad):
            caps = pad.get_current_caps()
            if caps and caps.get_structure(0).get_name().startswith("video/"):
                convert_sink = convert.get_static_pad("sink")
                if convert_sink and not convert_sink.is_linked():
                    pad.link(convert_sink)

        decoder.connect("pad-added", on_pad_added)

        pipeline.link(src, decoder)
        pipeline.link(convert, sink)
        control.play(pipe)

        super().__init__(pipe, sink)


class UDPReader(VideoReader):
    """UDP stream reader."""

    def __init__(self, host: str, port: int):
        src = element.udpsrc(host=host, port=port)
        depayloader = element.rtph264depay()
        decoder = element.avdec_h264()
        convert = element.videoconvert()
        sink = element.appsink()

        pipe = pipeline.chain(
            src, depayloader, decoder, convert, sink, name="udp-reader"
        )
        control.play(pipe)

        super().__init__(pipe, sink)


class TestPatternReader(VideoReader):
    """Test pattern generator for testing."""

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
        pattern: str = "smpte",
        format: str = "RGB",
    ):
        src = element.videotestsrc(pattern=pattern)
        capsfilter = element.capsfilter(
            caps=caps.raw(width=width, height=height, fps=FPS(fps), format=format)
        )
        convert = element.videoconvert()
        sink = element.appsink(
            caps=caps.raw(width=width, height=height, fps=FPS(fps), format=format)
        )

        pipe = pipeline.chain(
            src, capsfilter, convert, sink, name="test-pattern-reader"
        )
        control.play(pipe)

        super().__init__(pipe, sink)
