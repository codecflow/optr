from typing import TypedDict, Unpack
from gi.repository import Gst
from .base import create


VideoTestSource = TypedDict(
    "VideoTestSource",
    {
        "pattern": str,
        "width": int,
        "height": int,
        "framerate": str,
    },
    total=False,
)


def videotestsrc(
    *, name: str | None = None, **props: Unpack[VideoTestSource]
) -> Gst.Element:
    """Create videotestsrc with typed properties."""
    return create("videotestsrc", props, name)
