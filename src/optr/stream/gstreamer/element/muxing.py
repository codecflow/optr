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
