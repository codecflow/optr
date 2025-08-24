"""Pipeline branching utilities for tee elements."""

from collections.abc import Sequence

from gi.repository import Gst


def branch(tee: Gst.Element, *branches: Sequence[Gst.Element]) -> list[Gst.Element]:
    """
    Connect multiple branches to a tee element.
    For each branch: creates an intermediate queue, requests a tee src pad, and links.
    Returns the created queue elements (so you can reference them or unbranch later).
    """
    # ensure tee has a parent bin (must be in a pipeline/bin before linking)
    parent = tee.get_parent()
    if not isinstance(parent, Gst.Bin):
        raise RuntimeError("tee must be added to a bin/pipeline before branching")
    # validate it actually is a tee-like elem with request pads
    if tee.get_pad_template("src_%u") is None:
        raise ValueError(
            "Provided element does not have 'src_%u' request pad template (not a tee?)"
        )

    from ..element.processing import queue  # your queue() factory

    created_queues: list[Gst.Element] = []
    for branch_elems in branches:
        q = queue()
        parent.add(q)
        if q.get_parent() is not parent:
            raise RuntimeError("Failed to add queue to tee's parent bin")

        # request a src pad from tee and link to queue.sink
        tee_src = tee.get_request_pad("src_%u")
        if tee_src is None:
            raise RuntimeError("Failed to request pad 'src_%u' from tee")
        q_sink = q.get_static_pad("sink")
        if q_sink is None:
            tee.release_request_pad(tee_src)
            raise RuntimeError("Queue has no static 'sink' pad")

        if tee_src.link(q_sink) != Gst.PadLinkReturn.OK:
            tee.release_request_pad(tee_src)
            raise RuntimeError("Failed to link tee:src_%u -> queue:sink")

        # add remaining branch elems to the same bin, then link
        for e in branch_elems:
            if e.get_parent() is not parent:
                parent.add(e)

        # Link queue to branch elements
        from .core import link

        if branch_elems and not link(q, *branch_elems):
            raise RuntimeError("Failed to link downstream branch after queue")

        # propagate state if pipeline is already running (hot-branching)
        q.sync_state_with_parent()
        for e in branch_elems:
            e.sync_state_with_parent()

        created_queues.append(q)

    return created_queues


def unbranch(tee: Gst.Element, *queues: Gst.Element) -> None:
    """
    Detach queues from tee and release request pads.
    Call when removing a branch created by `branch()`.
    """
    for q in queues:
        sink = q.get_static_pad("sink")
        if not sink:
            continue
        src = sink.get_peer()
        if src:
            sink.unlink(src)
            try:
                tee.release_request_pad(src)
            except Exception:
                pass  # already released / different tee


def create_tee_branch(tee: Gst.Element, *elements: Gst.Element) -> Gst.Element:
    """
    Create a single branch from a tee element.
    Returns the intermediate queue element for later reference.
    """
    queues = branch(tee, elements)
    return queues[0] if queues else None


def remove_tee_branch(tee: Gst.Element, queue: Gst.Element) -> bool:
    """
    Remove a single branch from a tee element.
    Returns True if successful, False otherwise.
    """
    try:
        unbranch(tee, queue)
        return True
    except Exception:
        return False


def get_tee_branches(tee: Gst.Element) -> list[Gst.Element]:
    """
    Get all branch queue elements connected to a tee.
    Returns list of queue elements that are direct children of the tee.
    """
    branches = []

    # Iterate through all src pads of the tee
    src_pads = tee.iterate_src_pads()
    while True:
        result, pad = src_pads.next()
        if result == Gst.IteratorResult.OK:
            peer = pad.get_peer()
            if peer:
                peer_element = peer.get_parent_element()
                # Check if it's a queue (typical intermediate element)
                if peer_element and peer_element.get_factory():
                    factory_name = peer_element.get_factory().get_name()
                    if factory_name == "queue":
                        branches.append(peer_element)
        elif result == Gst.IteratorResult.DONE:
            break
        elif result == Gst.IteratorResult.ERROR:
            break

    return branches


def count_tee_branches(tee: Gst.Element) -> int:
    """Count the number of active branches on a tee element."""
    return len(get_tee_branches(tee))


def is_tee_element(element: Gst.Element) -> bool:
    """Check if an element is a tee-like element with request pads."""
    if not element.get_factory():
        return False

    factory_name = element.get_factory().get_name()
    if factory_name == "tee":
        return True

    # Check for request pad template
    return element.get_pad_template("src_%u") is not None
