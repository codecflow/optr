from typing import TypedDict

from gi.repository import Gst


class Element(TypedDict):
    name: str
    factory: str
    state: str


Connection = TypedDict(
    "Connection", {"from": str, "from_pad": str, "to": str, "to_pad": str}
)


class Topology(TypedDict):
    elements: list[Element]
    connections: list[Connection]


def topology(pipeline: Gst.Pipeline) -> Topology:
    """Get pipeline topology information."""
    topology: Topology = {"elements": [], "connections": []}

    # Get all elements
    elements = {}
    it = pipeline.iterate_elements()
    while True:
        result, element = it.next()
        if result == Gst.IteratorResult.OK:
            element_info: Element = {
                "name": element.get_name() or f"unnamed_{id(element)}",
                "factory": (
                    element.get_factory().get_name()
                    if element.get_factory()
                    else "unknown"
                ),
                "state": (
                    element.get_state(0)[1].value_nick
                    if element.get_state(0)[0] == Gst.StateChangeReturn.SUCCESS
                    else "unknown"
                ),
            }
            elements[element] = element_info
            topology["elements"].append(element_info)
        elif result == Gst.IteratorResult.DONE:
            break
        elif result == Gst.IteratorResult.ERROR:
            break

    # Get connections
    for element in elements:
        src_pads = element.iterate_src_pads()
        while True:
            result, pad = src_pads.next()
            if result == Gst.IteratorResult.OK:
                peer = pad.get_peer()
                if peer:
                    peer_element = peer.get_parent_element()
                    if peer_element in elements:
                        connection: Connection = {
                            "from": elements[element]["name"],
                            "from_pad": pad.get_name(),
                            "to": elements[peer_element]["name"],
                            "to_pad": peer.get_name(),
                        }
                        topology["connections"].append(connection)
            elif result == Gst.IteratorResult.DONE:
                break
            elif result == Gst.IteratorResult.ERROR:
                break

    return topology


def dotgraph(pipeline: Gst.Pipeline, filename: str = "pipeline") -> str:
    """Generate DOT graph file for pipeline visualization."""
    import os

    # Set GST_DEBUG_DUMP_DOT_DIR if not set
    dot_dir = os.environ.get("GST_DEBUG_DUMP_DOT_DIR", "/tmp")
    os.environ["GST_DEBUG_DUMP_DOT_DIR"] = dot_dir

    # Generate DOT file
    Gst.debug_bin_to_dot_file(pipeline, Gst.DebugGraphDetails.ALL, filename)

    dot_file = os.path.join(dot_dir, f"{filename}.dot")
    return dot_file if os.path.exists(dot_file) else ""
