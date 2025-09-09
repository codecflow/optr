from collections.abc import Mapping

from gi.repository import Gst

from ..errors import ElementCreationError, PropertyError


def create(
    type: str, /, props: Mapping[str, object] | None = None, name: str | None = None
) -> Gst.Element:
    """Generic element creator with property management."""
    element = Gst.ElementFactory.make(type, name)

    if not element:
        raise ElementCreationError(type, name)

    if not props:
        return element

    for prop, value in props.items():
        prop_name = prop.replace("_", "-")
        try:
            element.set_property(prop_name, value)
        except Exception as e:
            raise PropertyError(type, prop_name, value, e) from e

    return element
