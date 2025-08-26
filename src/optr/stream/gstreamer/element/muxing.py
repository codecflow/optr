from typing import TypedDict, Unpack

from gi.repository import Gst

from .base import create


class FLVMux(TypedDict, total=False):
    streamable: bool
    latency: int


def flvmux(*, name: str | None = None, **props: Unpack[FLVMux]) -> Gst.Element:
    """Create flvmux element."""
    props.setdefault("streamable", True)
    return create("flvmux", props, name=name)


class MP4Mux(TypedDict, total=False):
    pass


def mp4mux(*, name: str | None = None, **props: Unpack[MP4Mux]) -> Gst.Element:
    """Create MP4Mux with typed properties."""
    return create("mp4mux", props, name=name)


class RTPH264Pay(TypedDict, total=False):
    pass


def payloader(*, name: str | None = None, **props: Unpack[RTPH264Pay]) -> Gst.Element:
    """Create a payloader element with typed properties."""
    return create("rtph264pay", props, name)


class RTPH264Depay(TypedDict, total=False):
    pass


def rtph264depay(
    *, name: str | None = None, **props: Unpack[RTPH264Depay]
) -> Gst.Element:
    """Create RTPH264Depay with typed properties."""
    return create("rtph264depay", props, name=name)


class QtMux(TypedDict, total=False):
    movie_timescale: int
    trak_timescale: int
    fast_start: bool
    streamable: bool


def qtmux(*, name: str | None = None, **props: Unpack[QtMux]) -> Gst.Element:
    """Create qtmux element with typed properties."""
    props.setdefault("fast_start", False)
    props.setdefault("streamable", False)
    return create("qtmux", props, name=name)


class MatroskaMux(TypedDict, total=False):
    writing_app: str
    streamable: bool
    min_index_interval: int


def matroskamux(
    *, name: str | None = None, **props: Unpack[MatroskaMux]
) -> Gst.Element:
    """Create matroskamux element with typed properties."""
    props.setdefault("streamable", False)
    return create("matroskamux", props, name=name)


class MPEGTSMux(TypedDict, total=False):
    prog_map: str
    pat_interval: int
    pmt_interval: int


def mpegtsmux(*, name: str | None = None, **props: Unpack[MPEGTSMux]) -> Gst.Element:
    """Create mpegtsmux element with typed properties."""
    props.setdefault("pat_interval", 0)
    props.setdefault("pmt_interval", 0)
    return create("mpegtsmux", props, name=name)


class AVIMux(TypedDict, total=False):
    pass


def avimux(*, name: str | None = None, **props: Unpack[AVIMux]) -> Gst.Element:
    """Create avimux element with typed properties."""
    return create("avimux", props, name=name)


class WebMMux(TypedDict, total=False):
    writing_app: str
    streamable: bool


def webmmux(*, name: str | None = None, **props: Unpack[WebMMux]) -> Gst.Element:
    """Create webmmux element with typed properties."""
    props.setdefault("streamable", False)
    return create("webmmux", props, name=name)


class OggMux(TypedDict, total=False):
    pass


def oggmux(*, name: str | None = None, **props: Unpack[OggMux]) -> Gst.Element:
    """Create oggmux element with typed properties."""
    return create("oggmux", props, name=name)


# Additional RTP payloaders
class RTPH265Pay(TypedDict, total=False):
    pass


def rtph265pay(*, name: str | None = None, **props: Unpack[RTPH265Pay]) -> Gst.Element:
    """Create rtph265pay element with typed properties."""
    return create("rtph265pay", props, name=name)


class RTPVP8Pay(TypedDict, total=False):
    pass


def rtpvp8pay(*, name: str | None = None, **props: Unpack[RTPVP8Pay]) -> Gst.Element:
    """Create rtpvp8pay element with typed properties."""
    return create("rtpvp8pay", props, name=name)


class RTPVP9Pay(TypedDict, total=False):
    pass


def rtpvp9pay(*, name: str | None = None, **props: Unpack[RTPVP9Pay]) -> Gst.Element:
    """Create rtpvp9pay element with typed properties."""
    return create("rtpvp9pay", props, name=name)


# Additional RTP depayloaders
class RTPH265Depay(TypedDict, total=False):
    pass


def rtph265depay(
    *, name: str | None = None, **props: Unpack[RTPH265Depay]
) -> Gst.Element:
    """Create rtph265depay element with typed properties."""
    return create("rtph265depay", props, name=name)


class RTPVP8Depay(TypedDict, total=False):
    pass


def rtpvp8depay(
    *, name: str | None = None, **props: Unpack[RTPVP8Depay]
) -> Gst.Element:
    """Create rtpvp8depay element with typed properties."""
    return create("rtpvp8depay", props, name=name)


class RTPVP9Depay(TypedDict, total=False):
    pass


def rtpvp9depay(
    *, name: str | None = None, **props: Unpack[RTPVP9Depay]
) -> Gst.Element:
    """Create rtpvp9depay element with typed properties."""
    return create("rtpvp9depay", props, name=name)


class SplitMuxSink(TypedDict, total=False):
    location: str
    max_size_time: int
    max_size_bytes: int
    max_files: int
    muxer: Gst.Element
    async_finalize: bool
    send_keyframe_requests: bool
    alignment_threshold: int
    use_robust_muxing: bool


def splitmuxsink(
    *, name: str | None = None, **props: Unpack[SplitMuxSink]
) -> Gst.Element:
    """Create splitmuxsink element with typed properties."""
    return create("splitmuxsink", props, name=name)
