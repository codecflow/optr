"""Parser element wrappers for stream parsing."""

from typing import TypedDict, Unpack

from gi.repository import Gst

from .base import create


class H264Parse(TypedDict, total=False):
    config_interval: int
    disable_passthrough: bool


def h264parse(*, name: str | None = None, **props: Unpack[H264Parse]) -> Gst.Element:
    """Create h264parse element with typed properties."""
    props.setdefault("config_interval", -1)
    props.setdefault("disable_passthrough", False)
    return create("h264parse", props, name=name)


class H265Parse(TypedDict, total=False):
    config_interval: int
    disable_passthrough: bool


def h265parse(*, name: str | None = None, **props: Unpack[H265Parse]) -> Gst.Element:
    """Create h265parse element with typed properties."""
    props.setdefault("config_interval", -1)
    props.setdefault("disable_passthrough", False)
    return create("h265parse", props, name=name)


class AACParse(TypedDict, total=False):
    pass


def aacparse(*, name: str | None = None, **props: Unpack[AACParse]) -> Gst.Element:
    """Create aacparse element with typed properties."""
    return create("aacparse", props, name=name)


class VP8Parse(TypedDict, total=False):
    pass


def vp8parse(*, name: str | None = None, **props: Unpack[VP8Parse]) -> Gst.Element:
    """Create vp8parse element with typed properties."""
    return create("vp8parse", props, name=name)


class VP9Parse(TypedDict, total=False):
    pass


def vp9parse(*, name: str | None = None, **props: Unpack[VP9Parse]) -> Gst.Element:
    """Create vp9parse element with typed properties."""
    return create("vp9parse", props, name=name)


class AC3Parse(TypedDict, total=False):
    pass


def ac3parse(*, name: str | None = None, **props: Unpack[AC3Parse]) -> Gst.Element:
    """Create ac3parse element with typed properties."""
    return create("ac3parse", props, name=name)


class MPEGAudioParse(TypedDict, total=False):
    pass


def mpegaudioparse(
    *, name: str | None = None, **props: Unpack[MPEGAudioParse]
) -> Gst.Element:
    """Create mpegaudioparse element with typed properties."""
    return create("mpegaudioparse", props, name=name)


class RawAudioParse(TypedDict, total=False):
    use_sink_caps: bool
    format: str
    rate: int
    channels: int


def rawaudioparse(
    *, name: str | None = None, **props: Unpack[RawAudioParse]
) -> Gst.Element:
    """Create rawaudioparse element with typed properties."""
    props.setdefault("use_sink_caps", False)
    return create("rawaudioparse", props, name=name)


class RawVideoParse(TypedDict, total=False):
    use_sink_caps: bool
    format: str
    width: int
    height: int
    framerate: str


def rawvideoparse(
    *, name: str | None = None, **props: Unpack[RawVideoParse]
) -> Gst.Element:
    """Create rawvideoparse element with typed properties."""
    props.setdefault("use_sink_caps", False)
    return create("rawvideoparse", props, name=name)
