from typing import TypedDict, Unpack
from gi.repository import Gst
from .base import create


FLVMux = TypedDict("FLVMux", {"streamable": bool}, total=False)


def flvmux(*, name: str | None = None, **props: Unpack[FLVMux]) -> Gst.Element:
    """Create flvmux element."""
    props.setdefault("streamable", True)
    return create("flvmux", props, name=name)


MP4Mux = TypedDict("MP4Mux", {}, total=False)


def mp4mux(*, name: str | None = None, **props: Unpack[MP4Mux]) -> Gst.Element:
    """Create MP4Mux with typed properties."""
    return create("mp4mux", props, name=name)


RTPH264Pay = TypedDict("RTPH264Pay", {}, total=False)


def payloader(*, name: str | None = None, **props: Unpack[RTPH264Pay]) -> Gst.Element:
    """Create a payloader element with typed properties."""
    return create("rtph264pay", props, name)


RTPH264Depay = TypedDict("RTPH264Depay", {}, total=False)


def rtph264depay(
    *, name: str | None = None, **props: Unpack[RTPH264Depay]
) -> Gst.Element:
    """Create RTPH264Depay with typed properties."""
    return create("rtph264depay", props, name=name)


QtMux = TypedDict(
    "QtMux",
    {
        "movie_timescale": int,
        "trak_timescale": int,
        "fast_start": bool,
        "streamable": bool,
    },
    total=False,
)


def qtmux(*, name: str | None = None, **props: Unpack[QtMux]) -> Gst.Element:
    """Create qtmux element with typed properties."""
    props.setdefault("fast_start", False)
    props.setdefault("streamable", False)
    return create("qtmux", props, name=name)


MatroskaMux = TypedDict(
    "MatroskaMux",
    {
        "writing_app": str,
        "streamable": bool,
        "min_index_interval": int,
    },
    total=False,
)


def matroskamux(*, name: str | None = None, **props: Unpack[MatroskaMux]) -> Gst.Element:
    """Create matroskamux element with typed properties."""
    props.setdefault("streamable", False)
    return create("matroskamux", props, name=name)


MPEGTSMux = TypedDict(
    "MPEGTSMux",
    {
        "prog_map": str,
        "pat_interval": int,
        "pmt_interval": int,
    },
    total=False,
)


def mpegtsmux(*, name: str | None = None, **props: Unpack[MPEGTSMux]) -> Gst.Element:
    """Create mpegtsmux element with typed properties."""
    props.setdefault("pat_interval", 0)
    props.setdefault("pmt_interval", 0)
    return create("mpegtsmux", props, name=name)


AVIMux = TypedDict("AVIMux", {}, total=False)


def avimux(*, name: str | None = None, **props: Unpack[AVIMux]) -> Gst.Element:
    """Create avimux element with typed properties."""
    return create("avimux", props, name=name)


WebMMux = TypedDict(
    "WebMMux",
    {
        "writing_app": str,
        "streamable": bool,
    },
    total=False,
)


def webmmux(*, name: str | None = None, **props: Unpack[WebMMux]) -> Gst.Element:
    """Create webmmux element with typed properties."""
    props.setdefault("streamable", False)
    return create("webmmux", props, name=name)


OggMux = TypedDict("OggMux", {}, total=False)


def oggmux(*, name: str | None = None, **props: Unpack[OggMux]) -> Gst.Element:
    """Create oggmux element with typed properties."""
    return create("oggmux", props, name=name)


# Additional RTP payloaders
RTPH265Pay = TypedDict("RTPH265Pay", {}, total=False)


def rtph265pay(*, name: str | None = None, **props: Unpack[RTPH265Pay]) -> Gst.Element:
    """Create rtph265pay element with typed properties."""
    return create("rtph265pay", props, name=name)


RTPVP8Pay = TypedDict("RTPVP8Pay", {}, total=False)


def rtpvp8pay(*, name: str | None = None, **props: Unpack[RTPVP8Pay]) -> Gst.Element:
    """Create rtpvp8pay element with typed properties."""
    return create("rtpvp8pay", props, name=name)


RTPVP9Pay = TypedDict("RTPVP9Pay", {}, total=False)


def rtpvp9pay(*, name: str | None = None, **props: Unpack[RTPVP9Pay]) -> Gst.Element:
    """Create rtpvp9pay element with typed properties."""
    return create("rtpvp9pay", props, name=name)


# Additional RTP depayloaders
RTPH265Depay = TypedDict("RTPH265Depay", {}, total=False)


def rtph265depay(*, name: str | None = None, **props: Unpack[RTPH265Depay]) -> Gst.Element:
    """Create rtph265depay element with typed properties."""
    return create("rtph265depay", props, name=name)


RTPVP8Depay = TypedDict("RTPVP8Depay", {}, total=False)


def rtpvp8depay(*, name: str | None = None, **props: Unpack[RTPVP8Depay]) -> Gst.Element:
    """Create rtpvp8depay element with typed properties."""
    return create("rtpvp8depay", props, name=name)


RTPVP9Depay = TypedDict("RTPVP9Depay", {}, total=False)


def rtpvp9depay(*, name: str | None = None, **props: Unpack[RTPVP9Depay]) -> Gst.Element:
    """Create rtpvp9depay element with typed properties."""
    return create("rtpvp9depay", props, name=name)
