from typing import Literal, Required, TypedDict, Unpack

from gi.repository import Gst

from .base import create


class AppSrc(TypedDict, total=False):
    caps: Required[Gst.Caps]
    format: Literal["time", "bytes", "buffers"] | Gst.Format
    max_buffers: int
    block: bool
    emit_signals: bool
    is_live: bool
    do_timestamp: bool


def appsrc(*, name: str | None = None, **props: Unpack[AppSrc]) -> Gst.Element:
    """Create appsrc with typed properties."""

    props.setdefault("format", "time")
    props.setdefault("max_buffers", 1)
    props.setdefault("block", True)

    return create("appsrc", props, name)


class AppSink(TypedDict, total=False):
    caps: Gst.Caps
    max_buffers: int
    emit_signals: bool
    drop: bool
    sync: bool


def appsink(*, name: str | None = None, **props: Unpack[AppSink]) -> Gst.Element:
    """Create appsink with typed properties."""
    props.setdefault("max_buffers", 1)
    props.setdefault("emit_signals", True)
    return create("appsink", props, name)
