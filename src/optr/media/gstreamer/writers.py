from gi.repository import Gst

from optr.core.io.protocols import Closer, Writer
from optr.media.fps import FPS, ConvertibleToFPS

from . import buffer, caps, control, element, pipeline


class VideoWriter(Writer[bytes], Closer):
    """Base video writer implementing Writer and Closer protocols."""

    def __init__(
        self,
        pipe: Gst.Pipeline,
        appsrc: Gst.Element,
        fps: ConvertibleToFPS = 30,
        eos_timeout: float = 5.0,
    ):
        self.pipe = pipe
        self.appsrc = appsrc
        self.frame_count = 0
        [num, den] = FPS(fps)
        # Calculate fps_ns from ConvertibleToFPS
        self.fps_ns = (Gst.SECOND * den) // num
        self.eos_timeout = eos_timeout
        self.started = False

    def _start_pipeline(self) -> None:
        """Start the pipeline if not already started."""
        if not self.started:
            control.play(self.pipe)
            self.started = True

    def write(self, frame: bytes) -> None:
        """Write a frame to the output."""
        # Start pipeline on first write if not already started
        if not self.started:
            # Push the frame first, then start the pipeline
            timestamp = self.frame_count * self.fps_ns
            buffer.push(self.appsrc, frame, timestamp, self.fps_ns)
            self.frame_count += 1
            self._start_pipeline()
        else:
            # Normal operation - pipeline already started
            timestamp = self.frame_count * self.fps_ns
            buffer.push(self.appsrc, frame, timestamp, self.fps_ns)
            self.frame_count += 1

    def close(self) -> None:
        """Close and cleanup resources."""
        try:
            if self.started:
                self.appsrc.emit("end-of-stream")
                control.wait_for_eos(self.pipe, timeout_seconds=self.eos_timeout)
        finally:
            if self.started:
                control.stop(self.pipe)


class SHMWriter(VideoWriter):
    """Shared memory writer."""

    def __init__(
        self,
        socket_path: str,
        width: int,
        height: int,
        fps: ConvertibleToFPS = 30,
        format: str = "RGB",
        is_live: bool = True,
        do_timestamp: bool = True,
    ):
        video_caps = caps.raw(width=width, height=height, fps=FPS(fps), format=format)
        src = element.appsrc(
            caps=video_caps, is_live=is_live, do_timestamp=do_timestamp
        )
        sink = element.shmsink(socket_path=socket_path)

        pipe = pipeline.chain(src, sink, name="shm-writer")

        super().__init__(pipe, src, fps)


class RTMPWriter(VideoWriter):
    """RTMP streaming writer."""

    def __init__(
        self,
        url: str,
        width: int,
        height: int,
        fps: ConvertibleToFPS = 30,
        format: str = "RGB",
        bitrate: int = 2000,
        is_live: bool = True,
        do_timestamp: bool = True,
    ):
        video_caps = caps.raw(width=width, height=height, fps=FPS(fps), format=format)
        src = element.appsrc(
            caps=video_caps, is_live=is_live, do_timestamp=do_timestamp
        )
        convert = element.videoconvert()
        encoder = element.x264enc(bitrate=bitrate)

        muxer = element.flvmux()
        sink = element.rtmpsink(location=url)

        pipe = pipeline.chain(src, convert, encoder, muxer, sink, name="rtmp-writer")

        super().__init__(pipe, src, fps)


class UDPWriter(VideoWriter):
    """UDP streaming writer."""

    def __init__(
        self,
        host: str,
        port: int,
        width: int,
        height: int,
        fps: ConvertibleToFPS = 30,
        format: str = "RGB",
        bitrate: int = 2000,
        is_live: bool = True,
        do_timestamp: bool = True,
    ):
        video_caps = caps.raw(width=width, height=height, fps=FPS(fps), format=format)
        src = element.appsrc(
            caps=video_caps, is_live=is_live, do_timestamp=do_timestamp
        )
        convert = element.videoconvert()
        encoder = element.x264enc(
            bitrate=bitrate, tune="zerolatency", speed_preset="ultrafast"
        )
        payloader = element.create("rtph264pay", {"config-interval": 1, "pt": 96}, None)
        sink = element.udpsink(host=host, port=port)

        pipe = pipeline.chain(src, convert, encoder, payloader, sink, name="udp-writer")

        super().__init__(pipe, src, fps)


class FileWriter(VideoWriter):
    """File writer with encoding."""

    def __init__(
        self,
        filepath: str,
        width: int,
        height: int,
        fps: ConvertibleToFPS = 30,
        format: str = "RGB",
        bitrate: int = 2000,
        is_live: bool = True,
        do_timestamp: bool = True,
    ):
        video_caps = caps.raw(width=width, height=height, fps=FPS(fps), format=format)
        src = element.appsrc(
            caps=video_caps, is_live=is_live, do_timestamp=do_timestamp
        )
        convert = element.videoconvert()
        encoder = element.x264enc(bitrate=bitrate)
        muxer = element.create("mp4mux", None, None)
        sink = element.create("filesink", {"location": filepath}, None)

        pipe = pipeline.chain(src, convert, encoder, muxer, sink, name="file-writer")

        super().__init__(pipe, src, fps)
