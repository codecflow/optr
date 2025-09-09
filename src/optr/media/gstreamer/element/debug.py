"""Element debugging utilities."""

from collections.abc import Mapping
from typing import Any, TypedDict

from gi.repository import Gst


def properties(element: Gst.Element) -> dict[str, Any]:
    """Get all properties of an element for debugging."""
    props = {}

    if not element.get_factory():
        return {"error": "Element has no factory"}

    # Get all property specs
    pspecs = element.list_properties()

    for pspec in pspecs:
        prop_name = pspec.name
        try:
            value = element.get_property(prop_name)
            props[prop_name] = {
                "value": str(value),
                "type": pspec.value_type.name,
                "default": (
                    str(pspec.default_value)
                    if hasattr(pspec, "default_value")
                    else "N/A"
                ),
                "description": pspec.blurb or "No description",
            }
        except Exception as e:
            props[prop_name] = {"error": str(e)}

    return props


def info(element: Gst.Element) -> dict[str, Any]:
    """Get general information about an element."""
    factory = element.get_factory()
    if not factory:
        return {"error": "Element has no factory"}

    return {
        "name": element.get_name(),
        "factory_name": factory.get_name(),
        "description": factory.get_description(),
        "author": factory.get_author(),
        "version": factory.get_version(),
        "license": factory.get_license(),
        "package": factory.get_package(),
        "origin": factory.get_origin(),
        "rank": factory.get_rank(),
        "num_pad_templates": factory.get_num_pad_templates(),
    }


class Template(TypedDict):
    name: str
    direction: str
    presence: str
    caps: str


class Pad(TypedDict):
    static_pads: list[Template]
    request_pads: list[Template]
    sometimes_pads: list[Template]


def pads(element: Gst.Element) -> Mapping[str, Any]:
    """Get information about element's pads."""
    pad_info: Pad = {"static_pads": [], "request_pads": [], "sometimes_pads": []}

    factory = element.get_factory()
    if not factory:
        return {"error": "Element has no factory"}

    # Get pad templates
    templates = factory.get_static_pad_templates()
    for template in templates:
        template_info: Template = {
            "name": template.name_template,
            "direction": template.direction.value_nick,
            "presence": template.presence.value_nick,
            "caps": template.get_caps().to_string() if template.get_caps() else "ANY",
        }

        if template.presence == Gst.PadPresence.ALWAYS:
            pad_info["static_pads"].append(template_info)
        elif template.presence == Gst.PadPresence.REQUEST:
            pad_info["request_pads"].append(template_info)
        elif template.presence == Gst.PadPresence.SOMETIMES:
            pad_info["sometimes_pads"].append(template_info)

    return pad_info


def state(element: Gst.Element) -> dict[str, Any]:
    """Get element state information."""
    ret, current, pending = element.get_state(0)

    return {
        "current": (
            current.value_nick if ret == Gst.StateChangeReturn.SUCCESS else "unknown"
        ),
        "pending": pending.value_nick if ret == Gst.StateChangeReturn.ASYNC else "none",
        "return": ret.value_nick,
        "is_locked": element.is_locked_state(),
    }
