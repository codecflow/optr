from typing import Sequence
from gi.repository import Gst

def pipeline(*elements: Gst.Element, name: str | None = None) -> Gst.Pipeline:
    """Create pipeline and add elements."""
    pipe = Gst.Pipeline.new(name)
    for e in elements:
        pipe.add(e)
        if e.get_parent() is not pipe:
            raise RuntimeError(f"Failed to add {e.get_name() or e} to pipeline {name or '<unnamed>'}")
    return pipe

def link(*elements: Gst.Element) -> bool:
    """Link elements in sequence."""
    for a, b in zip(elements, elements[1:]):
        if not a.link(b):
            return False
    return True

def chain(*elements: Gst.Element, name: str | None = None) -> Gst.Pipeline:
    """Create pipeline, add elements, and link them."""
    pipe = pipeline(*elements, name=name)
    if not link(*elements):
        raise RuntimeError(f"Failed to link elements in pipeline {name or '<unnamed>'}")
    return pipe

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
        raise ValueError("Provided element does not have 'src_%u' request pad template (not a tee?)")

    from .element import queue  # your queue() factory

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

def compose(*pipes: Gst.Pipeline, name: str | None = None) -> Gst.Pipeline:
    """Merge multiple pipelines into one by moving their elements."""
    main = Gst.Pipeline.new(name)
    for p in pipes:
        p.set_state(Gst.State.NULL)

        it = p.iterate_elements()
        elems: list[Gst.Element] = []
        while True:
            res, el = it.next()
            if res == Gst.IteratorResult.OK:
                elems.append(el)
            elif res == Gst.IteratorResult.DONE:
                break
            elif res == Gst.IteratorResult.ERROR:
                raise RuntimeError("Error iterating pipeline elements")

        for el in elems:
            p.remove(el)
            main.add(el)
            if el.get_parent() is not main:
                raise RuntimeError(f"Failed to add {el.get_name() or el} to composed pipeline")

    return main
