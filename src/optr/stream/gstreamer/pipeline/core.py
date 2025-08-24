"""Core pipeline creation and composition utilities."""

from gi.repository import Gst


def pipeline(*elements: Gst.Element, name: str | None = None) -> Gst.Pipeline:
    """Create pipeline and add elements."""
    pipe = Gst.Pipeline.new(name)
    for e in elements:
        pipe.add(e)
        if e.get_parent() is not pipe:
            raise RuntimeError(
                f"Failed to add {e.get_name() or e} to pipeline {name or '<unnamed>'}"
            )
    return pipe


def link(*elements: Gst.Element) -> bool:
    """Link elements in sequence."""
    for a, b in zip(elements, elements[1:], strict=False):
        if not a.link(b):
            return False
    return True


def chain(*elements: Gst.Element, name: str | None = None) -> Gst.Pipeline:
    """Create pipeline, add elements, and link them."""
    pipe = pipeline(*elements, name=name)
    if not link(*elements):
        raise RuntimeError(f"Failed to link elements in pipeline {name or '<unnamed>'}")
    return pipe


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
                raise RuntimeError(
                    f"Failed to add {el.get_name() or el} to composed pipeline"
                )

    return main


def validate(pipeline: Gst.Pipeline) -> tuple[bool, list[str]]:
    """Validate pipeline configuration before running."""
    errors = []

    # Check if pipeline has elements
    elements = []
    it = pipeline.iterate_elements()
    while True:
        result, element = it.next()
        if result == Gst.IteratorResult.OK:
            elements.append(element)
        elif result == Gst.IteratorResult.DONE:
            break
        elif result == Gst.IteratorResult.ERROR:
            errors.append("Failed to iterate pipeline elements")
            break

    if not elements:
        errors.append("Pipeline contains no elements")
        return False, errors

    # Check for unlinked pads
    for element in elements:
        # Check src pads
        src_pads = element.iterate_src_pads()
        while True:
            result, pad = src_pads.next()
            if result == Gst.IteratorResult.OK:
                if (
                    not pad.get_peer()
                    and not pad.get_pad_template().presence == Gst.PadPresence.REQUEST
                ):
                    errors.append(
                        f"Unlinked src pad '{pad.get_name()}' on element '{element.get_name() or element}'"
                    )
            elif result == Gst.IteratorResult.DONE:
                break
            elif result == Gst.IteratorResult.ERROR:
                errors.append(
                    f"Error iterating src pads on element '{element.get_name() or element}'"
                )
                break

        # Check sink pads
        sink_pads = element.iterate_sink_pads()
        while True:
            result, pad = sink_pads.next()
            match result:
                case Gst.IteratorResult.OK:
                    if (
                        not pad.get_peer()
                        and not pad.get_pad_template().presence
                        == Gst.PadPresence.REQUEST
                    ):
                        errors.append(
                            f"Unlinked sink pad '{pad.get_name()}' on element '{element.get_name() or element}'"
                        )
                case Gst.IteratorResult.DONE:
                    break
                case Gst.IteratorResult.ERROR:
                    errors.append(
                        f"Error iterating sink pads on element '{element.get_name() or element}'"
                    )
                    break

    return len(errors) == 0, errors
