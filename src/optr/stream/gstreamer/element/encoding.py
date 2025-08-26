from typing import TypedDict, Unpack

from gi.repository import Gst

from .base import create


class X264Enc(TypedDict, total=False):
    bitrate: int
    tune: str
    speed_preset: str
    key_int_max: int
    bframes: int
    threads: int


def x264enc(*, name: str | None = None, **props: Unpack[X264Enc]) -> Gst.Element:
    """Create x264enc with typed properties."""
    props.setdefault("bitrate", 2000)
    props.setdefault("tune", "zerolatency")
    return create("x264enc", props, name)


class DecodeBin(TypedDict, total=False):
    connect_to_sink: bool
    use_dts: bool


def decodebin(*, name: str | None = None, **props: Unpack[DecodeBin]) -> Gst.Element:
    """Create decodebin with typed properties."""

    props.setdefault("connect_to_sink", True)
    props.setdefault("use_dts", False)
    return create("decodebin", props, name)


class AVDecH264(TypedDict, total=False):
    pass


def avdec_h264(*, name: str | None = None, **props: Unpack[AVDecH264]) -> Gst.Element:
    """Create AVDecH264 with typed properties."""
    return create("avdec_h264", props, name=name)


class X265Enc(TypedDict, total=False):
    bitrate: int
    speed_preset: str
    tune: str
    key_int_max: int


def x265enc(*, name: str | None = None, **props: Unpack[X265Enc]) -> Gst.Element:
    """Create x265enc with typed properties."""
    props.setdefault("bitrate", 2000)
    props.setdefault("speed_preset", "medium")
    return create("x265enc", props, name=name)


class VP8Enc(TypedDict, total=False):
    target_bitrate: int
    deadline: int
    cpu_used: int
    keyframe_max_dist: int


def vp8enc(*, name: str | None = None, **props: Unpack[VP8Enc]) -> Gst.Element:
    """Create vp8enc with typed properties."""
    props.setdefault("target_bitrate", 2000000)
    props.setdefault("deadline", 1)
    return create("vp8enc", props, name=name)


class VP9Enc(TypedDict, total=False):
    target_bitrate: int
    deadline: int
    cpu_used: int
    keyframe_max_dist: int


def vp9enc(*, name: str | None = None, **props: Unpack[VP9Enc]) -> Gst.Element:
    """Create vp9enc with typed properties."""
    props.setdefault("target_bitrate", 2000000)
    props.setdefault("deadline", 1)
    return create("vp9enc", props, name=name)


# Additional decoders
class AVDecH265(TypedDict, total=False):
    pass


def avdec_h265(*, name: str | None = None, **props: Unpack[AVDecH265]) -> Gst.Element:
    """Create avdec_h265 with typed properties."""
    return create("avdec_h265", props, name=name)


class AVDecVP8(TypedDict, total=False):
    pass


def avdec_vp8(*, name: str | None = None, **props: Unpack[AVDecVP8]) -> Gst.Element:
    """Create avdec_vp8 with typed properties."""
    return create("avdec_vp8", props, name=name)


class AVDecVP9(TypedDict, total=False):
    pass


def avdec_vp9(*, name: str | None = None, **props: Unpack[AVDecVP9]) -> Gst.Element:
    """Create avdec_vp9 with typed properties."""
    return create("avdec_vp9", props, name=name)


# Audio encoders
class AACEnc(TypedDict, total=False):
    bitrate: int
    compliance: str


def aacenc(*, name: str | None = None, **props: Unpack[AACEnc]) -> Gst.Element:
    """Create aacenc with typed properties."""
    props.setdefault("bitrate", 128000)
    return create("aacenc", props, name=name)


class OpusEnc(TypedDict, total=False):
    bitrate: int
    complexity: int
    frame_size: int


def opusenc(*, name: str | None = None, **props: Unpack[OpusEnc]) -> Gst.Element:
    """Create opusenc with typed properties."""
    props.setdefault("bitrate", 64000)
    return create("opusenc", props, name=name)


class VorbisEnc(TypedDict, total=False):
    bitrate: int
    quality: float


def vorbisenc(*, name: str | None = None, **props: Unpack[VorbisEnc]) -> Gst.Element:
    """Create vorbisenc with typed properties."""
    props.setdefault("bitrate", 128000)
    return create("vorbisenc", props, name=name)


# Audio decoders
class AACDec(TypedDict, total=False):
    pass


def aacdec(*, name: str | None = None, **props: Unpack[AACDec]) -> Gst.Element:
    """Create aacdec with typed properties."""
    return create("aacdec", props, name=name)


class OpusDec(TypedDict, total=False):
    pass


def opusdec(*, name: str | None = None, **props: Unpack[OpusDec]) -> Gst.Element:
    """Create opusdec with typed properties."""
    return create("opusdec", props, name=name)


class VorbisDec(TypedDict, total=False):
    pass


def vorbisdec(*, name: str | None = None, **props: Unpack[VorbisDec]) -> Gst.Element:
    """Create vorbisdec with typed properties."""
    return create("vorbisdec", props, name=name)
