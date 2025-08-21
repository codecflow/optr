from typing import Literal, TypedDict, Unpack
from gi.repository import Gst
from .base import create


Queue = TypedDict(
    "Queue",
    {
        "max_size_buffers": int,
        "max_size_time": int,
        "max_size_bytes": int,
        "leaky": Literal["no", "upstream", "downstream"],
    },
    total=False,
)


def queue(*, name: str | None = None, **props: Unpack[Queue]) -> Gst.Element:
    """Create queue with typed properties."""
    return create("queue", props, name)


CapsFilter = TypedDict("CapsFilter", {"caps": Gst.Caps}, total=False)


def capsfilter(*, name: str | None = None, **props: Unpack[CapsFilter]) -> Gst.Element:
    """Create capsfilter with typed properties."""
    return create("capsfilter", props, name)


VideoConvert = TypedDict("VideoConvert", {}, total=False)


def videoconvert(
    *, name: str | None = None, **props: Unpack[VideoConvert]
) -> Gst.Element:
    """Create videoconvert element."""
    return create("videoconvert", props, name=name)


VideoScale = TypedDict("VideoScale", {}, total=False)


def videoscale(*, name: str | None = None, **props: Unpack[VideoScale]) -> Gst.Element:
    """Create videoscale element."""
    return create("videoscale", props, name=name)


Tee = TypedDict("Tee", {}, total=False)


def tee(*, name: str | None = None, **props: Unpack[Tee]) -> Gst.Element:
    """Create tee element for splitting streams."""
    return create("tee", props, name=name)
