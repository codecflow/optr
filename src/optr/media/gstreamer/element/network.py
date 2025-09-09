from typing import Required, TypedDict, Unpack

from gi.repository import Gst

from .base import create

SHMSink = TypedDict(
    "SHMSink",
    {
        "socket_path": Required[str],
        "wait_for_connection": bool,
        "sync": bool,
        "async": bool,
        "buffer_time": int,
        "shm_size": int,
    },
    total=False,
)


def shmsink(*, name: str | None = None, **props: Unpack[SHMSink]) -> Gst.Element:
    """Create shmsink with typed properties."""

    props.setdefault("wait_for_connection", False)
    props.setdefault("sync", False)
    props.setdefault("async", False)
    return create("shmsink", props, name)


class SHMSource(TypedDict, total=False):
    socket_path: Required[str]
    is_live: bool
    do_timestamp: bool


def shmsrc(*, name: str | None = None, **props: Unpack[SHMSource]) -> Gst.Element:
    """Create shmsrc with typed properties."""
    props.setdefault("is_live", True)
    props.setdefault("do_timestamp", True)
    return create("shmsrc", props, name)


UDPSink = TypedDict(
    "UDPSink",
    {
        "host": Required[str],
        "port": Required[int],
        "sync": bool,
        "async": bool,
    },
    total=False,
)


def udpsink(*, name: str | None = None, **props: Unpack[UDPSink]) -> Gst.Element:
    """Create udpsink with typed properties."""
    props.setdefault("sync", False)
    props.setdefault("async", False)
    return create("udpsink", props, name)


class UDPSource(TypedDict, total=False):
    host: Required[str]
    port: Required[int]
    is_live: bool
    do_timestamp: bool


def udpsrc(*, name: str | None = None, **props: Unpack[UDPSource]) -> Gst.Element:
    """Create udpsrc with typed properties."""
    props.setdefault("is_live", True)
    props.setdefault("do_timestamp", True)
    return create("udpsrc", props, name)


class RTMPSink(TypedDict, total=False):
    location: Required[str]
    sync: bool


def rtmpsink(*, name: str | None = None, **props: Unpack[RTMPSink]) -> Gst.Element:
    """Create rtmpsink with typed properties."""
    return create("rtmpsink", props, name)


class RTPSource(TypedDict, total=False):
    location: Required[str]
    is_live: bool
    do_timestamp: bool


def rtmpsrc(*, name: str | None = None, **props: Unpack[RTPSource]) -> Gst.Element:
    """Create rtmpsrc with typed properties."""
    props.setdefault("is_live", True)
    props.setdefault("do_timestamp", True)
    return create("rtmpsrc", props, name)
