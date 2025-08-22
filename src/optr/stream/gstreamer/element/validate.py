"""Element validation and compatibility utilities."""

from typing import Dict, Any, Tuple
from gi.repository import Gst


def caps(element: Gst.Element, pad_name: str = "src") -> Dict[str, Any]:
    """Inspect capabilities of an element's pad."""
    pad = element.get_static_pad(pad_name)
    if not pad:
        pad = element.get_request_pad(pad_name)
    if not pad:
        return {"error": f"Pad '{pad_name}' not found"}
    
    caps = pad.get_current_caps()
    if not caps:
        caps = pad.query_caps(None)
    
    if not caps:
        return {"error": "No caps available"}
    
    caps_info = {
        "num_structures": caps.get_size(),
        "structures": []
    }
    
    for i in range(caps.get_size()):
        structure = caps.get_structure(i)
        struct_info = {
            "name": structure.get_name(),
            "fields": {}
        }
        
        # Get all field names
        for j in range(structure.n_fields()):
            field_name = structure.nth_field_name(j)
            value = structure.get_value(field_name)
            struct_info["fields"][field_name] = str(value)
        
        caps_info["structures"].append(struct_info)
    
    return caps_info


def compatibility(src_element: Gst.Element, sink_element: Gst.Element,
                 src_pad: str = "src", sink_pad: str = "sink") -> Tuple[bool, str]:
    """Check if two elements can be linked together."""
    src_pad_obj = src_element.get_static_pad(src_pad)
    if not src_pad_obj:
        src_pad_obj = src_element.get_request_pad(src_pad)
    if not src_pad_obj:
        return False, f"Source pad '{src_pad}' not found"
    
    sink_pad_obj = sink_element.get_static_pad(sink_pad)
    if not sink_pad_obj:
        return False, f"Sink pad '{sink_pad}' not found"
    
    # Get pad templates
    src_template = src_pad_obj.get_pad_template()
    sink_template = sink_pad_obj.get_pad_template()
    
    if not src_template or not sink_template:
        return False, "Missing pad templates"
    
    # Check caps compatibility
    src_caps = src_template.get_caps()
    sink_caps = sink_template.get_caps()
    
    if not src_caps.can_intersect(sink_caps):
        return False, f"Incompatible caps: {src_caps.to_string()} vs {sink_caps.to_string()}"
    
    return True, "Compatible"
