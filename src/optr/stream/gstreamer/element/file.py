from typing import Required, TypedDict, Unpack

from gi.repository import Gst

from .base import create


class FileSource(TypedDict, total=False):
    location: Required[str]
    is_live: bool
    do_timestamp: bool


def filesrc(*, name: str | None = None, **props: Unpack[FileSource]) -> Gst.Element:
    """Create filesrc with typed properties."""
    props.setdefault("is_live", False)
    props.setdefault("do_timestamp", False)
    return create("filesrc", props, name)


class FileSink(TypedDict, total=False):
    location: Required[str]


def filesink(*, name: str | None = None, **props: Unpack[FileSink]) -> Gst.Element:
    """Create filesink with typed properties."""
    return create("filesink", props, name=name)
