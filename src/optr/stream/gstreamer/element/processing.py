from typing import Literal, TypedDict, Unpack

from gi.repository import Gst

from .base import create


class Queue(TypedDict, total=False):
    max_size_buffers: int
    max_size_time: int
    max_size_bytes: int
    leaky: Literal["no", "upstream", "downstream"]


def queue(*, name: str | None = None, **props: Unpack[Queue]) -> Gst.Element:
    """Create queue with typed properties."""
    return create("queue", props, name)


class CapsFilter(TypedDict, total=False):
    caps: Gst.Caps


def capsfilter(*, name: str | None = None, **props: Unpack[CapsFilter]) -> Gst.Element:
    """Create capsfilter with typed properties."""
    return create("capsfilter", props, name)


class VideoConvert(TypedDict, total=False):
    pass


def videoconvert(
    *, name: str | None = None, **props: Unpack[VideoConvert]
) -> Gst.Element:
    """Create videoconvert element."""
    return create("videoconvert", props, name=name)


class VideoScale(TypedDict, total=False):
    pass


def videoscale(*, name: str | None = None, **props: Unpack[VideoScale]) -> Gst.Element:
    """Create videoscale element."""
    return create("videoscale", props, name=name)


class Tee(TypedDict, total=False):
    pass


def tee(*, name: str | None = None, **props: Unpack[Tee]) -> Gst.Element:
    """Create tee element for splitting streams."""
    return create("tee", props, name=name)


class VideoRate(TypedDict, total=False):
    drop_only: bool
    max_rate: int
    new_pref: float


def videorate(*, name: str | None = None, **props: Unpack[VideoRate]) -> Gst.Element:
    """Create videorate element for framerate conversion."""
    return create("videorate", props, name=name)


class AudioConvert(TypedDict, total=False):
    pass


def audioconvert(
    *, name: str | None = None, **props: Unpack[AudioConvert]
) -> Gst.Element:
    """Create audioconvert element."""
    return create("audioconvert", props, name=name)


class AudioResample(TypedDict, total=False):
    pass


def audioresample(
    *, name: str | None = None, **props: Unpack[AudioResample]
) -> Gst.Element:
    """Create audioresample element."""
    return create("audioresample", props, name=name)


class Identity(TypedDict, total=False):
    dump: bool
    sync: bool
    silent: bool
    single_segment: bool


def identity(*, name: str | None = None, **props: Unpack[Identity]) -> Gst.Element:
    """Create identity element for debugging/passthrough."""
    props.setdefault("silent", True)
    return create("identity", props, name=name)


class Valve(TypedDict, total=False):
    drop: bool


def valve(*, name: str | None = None, **props: Unpack[Valve]) -> Gst.Element:
    """Create valve element for stream control."""
    props.setdefault("drop", False)
    return create("valve", props, name=name)


class VideoFlip(TypedDict, total=False):
    method: int


def videoflip(*, name: str | None = None, **props: Unpack[VideoFlip]) -> Gst.Element:
    """Create videoflip element for video rotation/flipping."""
    return create("videoflip", props, name=name)


class VideoCrop(TypedDict, total=False):
    top: int
    bottom: int
    left: int
    right: int


def videocrop(*, name: str | None = None, **props: Unpack[VideoCrop]) -> Gst.Element:
    """Create videocrop element for cropping video."""
    return create("videocrop", props, name=name)


class VideoBox(TypedDict, total=False):
    top: int
    bottom: int
    left: int
    right: int
    fill: int


def videobox(*, name: str | None = None, **props: Unpack[VideoBox]) -> Gst.Element:
    """Create videobox element for adding borders/padding."""
    return create("videobox", props, name=name)


class AudioPanorama(TypedDict, total=False):
    panorama: float
    method: int


def audiopanorama(
    *, name: str | None = None, **props: Unpack[AudioPanorama]
) -> Gst.Element:
    """Create audiopanorama element for stereo positioning."""
    props.setdefault("panorama", 0.0)
    return create("audiopanorama", props, name=name)


class Volume(TypedDict, total=False):
    volume: float
    mute: bool


def volume(*, name: str | None = None, **props: Unpack[Volume]) -> Gst.Element:
    """Create volume element for audio volume control."""
    props.setdefault("volume", 1.0)
    props.setdefault("mute", False)
    return create("volume", props, name=name)


class Level(TypedDict, total=False):
    message: bool
    interval: int


def level(*, name: str | None = None, **props: Unpack[Level]) -> Gst.Element:
    """Create level element for audio level monitoring."""
    props.setdefault("message", True)
    props.setdefault("interval", 100000000)  # 100ms
    return create("level", props, name=name)


class Compositor(TypedDict, total=False):
    background: int


def compositor(*, name: str | None = None, **props: Unpack[Compositor]) -> Gst.Element:
    """Create compositor element for video mixing."""
    props.setdefault("background", 1)  # black
    return create("compositor", props, name=name)


class AudioMixer(TypedDict, total=False):
    pass


def audiomixer(*, name: str | None = None, **props: Unpack[AudioMixer]) -> Gst.Element:
    """Create audiomixer element for audio mixing."""
    return create("audiomixer", props, name=name)
