"""Dynamic pipeline modification utilities."""

from gi.repository import Gst


def hot_add(pipeline: Gst.Pipeline, *elements: Gst.Element) -> bool:
    """Add elements to a running pipeline and sync their state."""
    if not elements:
        return True

    # Add elements to pipeline
    for element in elements:
        if element.get_parent():
            raise RuntimeError(
                f"Element {element.get_name() or element} already has a parent"
            )
        pipeline.add(element)
        if element.get_parent() is not pipeline:
            raise RuntimeError(
                f"Failed to add {element.get_name() or element} to pipeline"
            )

    # Sync state with pipeline
    for element in elements:
        if not element.sync_state_with_parent():
            return False

    return True


def hot_remove(pipeline: Gst.Pipeline, *elements: Gst.Element) -> bool:
    """Remove elements from a running pipeline after unlinking."""
    if not elements:
        return True

    # Set elements to NULL state first
    for element in elements:
        if element.get_parent() is not pipeline:
            continue
        element.set_state(Gst.State.NULL)

    # Unlink all pads
    for element in elements:
        # Unlink all src pads
        src_pads = element.iterate_src_pads()
        while True:
            result, pad = src_pads.next()
            if result == Gst.IteratorResult.OK:
                peer = pad.get_peer()
                if peer:
                    pad.unlink(peer)
            elif result == Gst.IteratorResult.DONE:
                break
            elif result == Gst.IteratorResult.ERROR:
                return False

        # Unlink all sink pads
        sink_pads = element.iterate_sink_pads()
        while True:
            result, pad = sink_pads.next()
            if result == Gst.IteratorResult.OK:
                peer = pad.get_peer()
                if peer:
                    peer.unlink(pad)
            elif result == Gst.IteratorResult.DONE:
                break
            elif result == Gst.IteratorResult.ERROR:
                return False

    # Remove from pipeline
    for element in elements:
        if element.get_parent() is pipeline:
            pipeline.remove(element)

    return True


def reconnect(
    src_element: Gst.Element,
    sink_element: Gst.Element,
    src_pad: str = "src",
    sink_pad: str = "sink",
) -> bool:
    """Reconnect elements by unlinking existing connections and creating new ones."""
    src_pad_obj = src_element.get_static_pad(src_pad)
    if not src_pad_obj:
        # Try request pad
        src_pad_obj = src_element.get_request_pad(src_pad)
    if not src_pad_obj:
        raise RuntimeError(
            f"Source pad '{src_pad}' not found on {src_element.get_name() or src_element}"
        )

    sink_pad_obj = sink_element.get_static_pad(sink_pad)
    if not sink_pad_obj:
        raise RuntimeError(
            f"Sink pad '{sink_pad}' not found on {sink_element.get_name() or sink_element}"
        )

    # Unlink existing connections
    peer = src_pad_obj.get_peer()
    if peer:
        src_pad_obj.unlink(peer)

    peer = sink_pad_obj.get_peer()
    if peer:
        peer.unlink(sink_pad_obj)

    # Create new connection
    return src_pad_obj.link(sink_pad_obj) == Gst.PadLinkReturn.OK


def replace_element(
    pipeline: Gst.Pipeline, old_element: Gst.Element, new_element: Gst.Element
) -> bool:
    """Replace an element in a running pipeline while preserving connections."""
    if old_element.get_parent() is not pipeline:
        raise RuntimeError("Old element is not in the specified pipeline")

    # Store connection information
    src_connections = []
    sink_connections = []

    # Get all src pad connections
    src_pads = old_element.iterate_src_pads()
    while True:
        result, pad = src_pads.next()
        if result == Gst.IteratorResult.OK:
            peer = pad.get_peer()
            if peer:
                src_connections.append(
                    (pad.get_name(), peer.get_parent_element(), peer.get_name())
                )
        elif result == Gst.IteratorResult.DONE:
            break
        elif result == Gst.IteratorResult.ERROR:
            return False

    # Get all sink pad connections
    sink_pads = old_element.iterate_sink_pads()
    while True:
        result, pad = sink_pads.next()
        if result == Gst.IteratorResult.OK:
            peer = pad.get_peer()
            if peer:
                sink_connections.append(
                    (peer.get_parent_element(), peer.get_name(), pad.get_name())
                )
        elif result == Gst.IteratorResult.DONE:
            break
        elif result == Gst.IteratorResult.ERROR:
            return False

    # Remove old element
    if not hot_remove(pipeline, old_element):
        return False

    # Add new element
    if not hot_add(pipeline, new_element):
        return False

    # Restore src connections
    for src_pad_name, peer_element, peer_pad_name in src_connections:
        if not reconnect(new_element, peer_element, src_pad_name, peer_pad_name):
            return False

    # Restore sink connections
    for peer_element, peer_pad_name, sink_pad_name in sink_connections:
        if not reconnect(peer_element, new_element, peer_pad_name, sink_pad_name):
            return False

    return True


def insert_element(
    pipeline: Gst.Pipeline,
    element: Gst.Element,
    after: Gst.Element,
    before: Gst.Element,
    after_pad: str = "src",
    before_pad: str = "sink",
    element_src: str = "src",
    element_sink: str = "sink",
) -> bool:
    """Insert an element between two existing connected elements."""
    # Verify the connection exists
    after_pad_obj = after.get_static_pad(after_pad)
    if not after_pad_obj:
        after_pad_obj = after.get_request_pad(after_pad)
    if not after_pad_obj:
        return False

    before_pad_obj = before.get_static_pad(before_pad)
    if not before_pad_obj:
        return False

    peer = after_pad_obj.get_peer()
    if not peer or peer != before_pad_obj:
        raise RuntimeError("Elements are not directly connected")

    # Add new element to pipeline
    if not hot_add(pipeline, element):
        return False

    # Break existing connection
    after_pad_obj.unlink(before_pad_obj)

    # Create new connections: after -> element -> before
    if not reconnect(after, element, after_pad, element_sink):
        return False

    if not reconnect(element, before, element_src, before_pad):
        return False

    return True


def branch_insert(
    tee: Gst.Element, *branch_elements: Gst.Element
) -> Gst.Element | None:
    """Insert a new branch into an existing tee element."""
    parent = tee.get_parent()
    if not isinstance(parent, Gst.Bin):
        raise RuntimeError("Tee must be in a bin/pipeline")

    if not branch_elements:
        return None

    # Import queue from element module
    from ..element.processing import queue

    # Create intermediate queue
    q = queue()
    if not hot_add(parent, q):
        return None

    # Add branch elements
    if not hot_add(parent, *branch_elements):
        return None

    # Request src pad from tee
    tee_src = tee.get_request_pad("src_%u")
    if not tee_src:
        return None

    # Connect tee -> queue
    q_sink = q.get_static_pad("sink")
    if tee_src.link(q_sink) != Gst.PadLinkReturn.OK:
        tee.release_request_pad(tee_src)
        return None

    # Link queue to branch elements
    from ..pipeline import link

    if not link(q, *branch_elements):
        return None

    return q


def branch_remove(tee: Gst.Element, queue: Gst.Element) -> bool:
    """Remove a branch from a tee element (queue should be the intermediate queue)."""
    parent = tee.get_parent()
    if not isinstance(parent, Gst.Bin):
        return False

    # Find all elements downstream from queue
    downstream = []
    current = queue

    while current:
        downstream.append(current)
        # Find next element
        next_element = None
        src_pads = current.iterate_src_pads()
        while True:
            result, pad = src_pads.next()
            if result == Gst.IteratorResult.OK:
                peer = pad.get_peer()
                if peer:
                    next_element = peer.get_parent_element()
                    break
            elif result == Gst.IteratorResult.DONE:
                break
            elif result == Gst.IteratorResult.ERROR:
                return False
        current = next_element

    # Find and release tee src pad
    queue_sink = queue.get_static_pad("sink")
    if queue_sink:
        tee_src = queue_sink.get_peer()
        if tee_src:
            tee_src.unlink(queue_sink)
            tee.release_request_pad(tee_src)

    # Remove all downstream elements
    return hot_remove(parent, *downstream)
