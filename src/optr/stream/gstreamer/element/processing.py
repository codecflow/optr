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


VideoRate = TypedDict(
    "VideoRate",
    {
        "drop_only": bool,
        "max_rate": int,
        "new_pref": float,
    },
    total=False,
)


def videorate(*, name: str | None = None, **props: Unpack[VideoRate]) -> Gst.Element:
    """Create videorate element for framerate conversion."""
    return create("videorate", props, name=name)


AudioConvert = TypedDict("AudioConvert", {}, total=False)


def audioconvert(*, name: str | None = None, **props: Unpack[AudioConvert]) -> Gst.Element:
    """Create audioconvert element."""
    return create("audioconvert", props, name=name)


AudioResample = TypedDict("AudioResample", {}, total=False)


def audioresample(*, name: str | None = None, **props: Unpack[AudioResample]) -> Gst.Element:
    """Create audioresample element."""
    return create("audioresample", props, name=name)


Identity = TypedDict(
    "Identity",
    {
        "dump": bool,
        "sync": bool,
        "silent": bool,
        "single_segment": bool,
    },
    total=False,
)


def identity(*, name: str | None = None, **props: Unpack[Identity]) -> Gst.Element:
    """Create identity element for debugging/passthrough."""
    props.setdefault("silent", True)
    return create("identity", props, name=name)


Valve = TypedDict(
    "Valve",
    {
        "drop": bool,
    },
    total=False,
)


def valve(*, name: str | None = None, **props: Unpack[Valve]) -> Gst.Element:
    """Create valve element for stream control."""
    props.setdefault("drop", False)
    return create("valve", props, name=name)


VideoFlip = TypedDict(
    "VideoFlip",
    {
        "method": int,  # 0=none, 1=clockwise, 2=rotate-180, 3=counterclockwise, 4=horizontal-flip, 5=vertical-flip, 6=upper-left-diagonal, 7=upper-right-diagonal
    },
    total=False,
)


def videoflip(*, name: str | None = None, **props: Unpack[VideoFlip]) -> Gst.Element:
    """Create videoflip element for video rotation/flipping."""
    return create("videoflip", props, name=name)


VideoCrop = TypedDict(
    "VideoCrop",
    {
        "top": int,
        "bottom": int,
        "left": int,
        "right": int,
    },
    total=False,
)


def videocrop(*, name: str | None = None, **props: Unpack[VideoCrop]) -> Gst.Element:
    """Create videocrop element for cropping video."""
    return create("videocrop", props, name=name)


VideoBox = TypedDict(
    "VideoBox",
    {
        "top": int,
        "bottom": int,
        "left": int,
        "right": int,
        "fill": int,  # 0=black, 1=green, 2=blue, 3=red, 4=yellow, 5=magenta, 6=cyan, 7=white
    },
    total=False,
)


def videobox(*, name: str | None = None, **props: Unpack[VideoBox]) -> Gst.Element:
    """Create videobox element for adding borders/padding."""
    return create("videobox", props, name=name)


AudioPanorama = TypedDict(
    "AudioPanorama",
    {
        "panorama": float,  # -1.0 (left) to 1.0 (right)
        "method": int,  # 0=psychoacoustic, 1=simple
    },
    total=False,
)


def audiopanorama(*, name: str | None = None, **props: Unpack[AudioPanorama]) -> Gst.Element:
    """Create audiopanorama element for stereo positioning."""
    props.setdefault("panorama", 0.0)
    return create("audiopanorama", props, name=name)


Volume = TypedDict(
    "Volume",
    {
        "volume": float,
        "mute": bool,
    },
    total=False,
)


def volume(*, name: str | None = None, **props: Unpack[Volume]) -> Gst.Element:
    """Create volume element for audio volume control."""
    props.setdefault("volume", 1.0)
    props.setdefault("mute", False)
    return create("volume", props, name=name)


Level = TypedDict(
    "Level",
    {
        "message": bool,
        "interval": int,  # nanoseconds
    },
    total=False,
)


def level(*, name: str | None = None, **props: Unpack[Level]) -> Gst.Element:
    """Create level element for audio level monitoring."""
    props.setdefault("message", True)
    props.setdefault("interval", 100000000)  # 100ms
    return create("level", props, name=name)


Compositor = TypedDict(
    "Compositor",
    {
        "background": int,  # 0=checker, 1=black, 2=white, 3=transparent
    },
    total=False,
)


def compositor(*, name: str | None = None, **props: Unpack[Compositor]) -> Gst.Element:
    """Create compositor element for video mixing."""
    props.setdefault("background", 1)  # black
    return create("compositor", props, name=name)


AudioMixer = TypedDict("AudioMixer", {}, total=False)


def audiomixer(*, name: str | None = None, **props: Unpack[AudioMixer]) -> Gst.Element:
    """Create audiomixer element for audio mixing."""
    return create("audiomixer", props, name=name)
