from typing import TypedDict, Unpack

from gi.repository import Gst

from .base import create


class VideoTestSource(TypedDict, total=False):
    pattern: str
    width: int
    height: int
    framerate: str


def videotestsrc(
    *, name: str | None = None, **props: Unpack[VideoTestSource]
) -> Gst.Element:
    """Create videotestsrc with typed properties."""
    return create("videotestsrc", props, name)


class AudioTestSource(TypedDict, total=False):
    wave: str
    freq: float
    volume: float
    samplesperbuffer: int


def audiotestsrc(
    *, name: str | None = None, **props: Unpack[AudioTestSource]
) -> Gst.Element:
    """Create audiotestsrc with typed properties."""
    return create("audiotestsrc", props, name)
