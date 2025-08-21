from typing import TypedDict, Unpack
from gi.repository import Gst
from .base import create


X264Enc = TypedDict(
    "X264Enc",
    {
        "bitrate": int,
        "tune": str,
        "speed_preset": str,
        "key_int_max": int,
    },
    total=False,
)


def x264enc(*, name: str | None = None, **props: Unpack[X264Enc]) -> Gst.Element:
    """Create x264enc with typed properties."""
    props.setdefault("bitrate", 2000)
    props.setdefault("tune", "zerolatency")
    return create("x264enc", props, name)


DecodeBin = TypedDict(
    "DecodeBin", {"connect_to_sink": bool, "use_dts": bool}, total=False
)


def decodebin(*, name: str | None = None, **props: Unpack[DecodeBin]) -> Gst.Element:
    """Create decodebin with typed properties."""

    props.setdefault("connect_to_sink", True)
    props.setdefault("use_dts", False)
    return create("decodebin", props, name)


AVDecH264 = TypedDict("AVDecH264", {}, total=False)


def avdec_h264(*, name: str | None = None, **props: Unpack[AVDecH264]) -> Gst.Element:
    """Create AVDecH264 with typed properties."""
    return create("avdec_h264", props, name=name)
