"""Parser element wrappers for stream parsing."""

from typing import TypedDict, Unpack
from gi.repository import Gst
from .base import create


H264Parse = TypedDict(
    "H264Parse",
    {
        "config_interval": int,
        "disable_passthrough": bool,
    },
    total=False,
)


def h264parse(*, name: str | None = None, **props: Unpack[H264Parse]) -> Gst.Element:
    """Create h264parse element with typed properties."""
    props.setdefault("config_interval", -1)
    props.setdefault("disable_passthrough", False)
    return create("h264parse", props, name=name)


H265Parse = TypedDict(
    "H265Parse",
    {
        "config_interval": int,
        "disable_passthrough": bool,
    },
    total=False,
)


def h265parse(*, name: str | None = None, **props: Unpack[H265Parse]) -> Gst.Element:
    """Create h265parse element with typed properties."""
    props.setdefault("config_interval", -1)
    props.setdefault("disable_passthrough", False)
    return create("h265parse", props, name=name)


AACParse = TypedDict("AACParse", {}, total=False)


def aacparse(*, name: str | None = None, **props: Unpack[AACParse]) -> Gst.Element:
    """Create aacparse element with typed properties."""
    return create("aacparse", props, name=name)


VP8Parse = TypedDict("VP8Parse", {}, total=False)


def vp8parse(*, name: str | None = None, **props: Unpack[VP8Parse]) -> Gst.Element:
    """Create vp8parse element with typed properties."""
    return create("vp8parse", props, name=name)


VP9Parse = TypedDict("VP9Parse", {}, total=False)


def vp9parse(*, name: str | None = None, **props: Unpack[VP9Parse]) -> Gst.Element:
    """Create vp9parse element with typed properties."""
    return create("vp9parse", props, name=name)


AC3Parse = TypedDict("AC3Parse", {}, total=False)


def ac3parse(*, name: str | None = None, **props: Unpack[AC3Parse]) -> Gst.Element:
    """Create ac3parse element with typed properties."""
    return create("ac3parse", props, name=name)


MPEGAudioParse = TypedDict("MPEGAudioParse", {}, total=False)


def mpegaudioparse(*, name: str | None = None, **props: Unpack[MPEGAudioParse]) -> Gst.Element:
    """Create mpegaudioparse element with typed properties."""
    return create("mpegaudioparse", props, name=name)


RawAudioParse = TypedDict(
    "RawAudioParse",
    {
        "use_sink_caps": bool,
        "format": str,
        "rate": int,
        "channels": int,
    },
    total=False,
)


def rawaudioparse(*, name: str | None = None, **props: Unpack[RawAudioParse]) -> Gst.Element:
    """Create rawaudioparse element with typed properties."""
    props.setdefault("use_sink_caps", False)
    return create("rawaudioparse", props, name=name)


RawVideoParse = TypedDict(
    "RawVideoParse",
    {
        "use_sink_caps": bool,
        "format": str,
        "width": int,
        "height": int,
        "framerate": str,
    },
    total=False,
)


def rawvideoparse(*, name: str | None = None, **props: Unpack[RawVideoParse]) -> Gst.Element:
    """Create rawvideoparse element with typed properties."""
    props.setdefault("use_sink_caps", False)
    return create("rawvideoparse", props, name=name)
