from collections.abc import Mapping
from gi.repository import Gst


def create(
    type: str, /, props: Mapping[str, object] | None = None, name: str | None = None
) -> Gst.Element:
    """Generic element creator with property management."""
    element = Gst.ElementFactory.make(type, name)

    if not element:
        raise RuntimeError(f"Failed to create {type} element")

    if not props:
        return element

    for prop, value in props.items():
        element.set_property(prop.replace("_", "-"), value)

    return element
