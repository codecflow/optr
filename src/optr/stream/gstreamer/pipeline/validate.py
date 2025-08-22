"""Pipeline debugging, monitoring, and utility functions."""

from gi.repository import Gst


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
            if result == Gst.IteratorResult.OK:
                if (
                    not pad.get_peer()
                    and not pad.get_pad_template().presence == Gst.PadPresence.REQUEST
                ):
                    errors.append(
                        f"Unlinked sink pad '{pad.get_name()}' on element '{element.get_name() or element}'"
                    )
            elif result == Gst.IteratorResult.DONE:
                break
            elif result == Gst.IteratorResult.ERROR:
                errors.append(
                    f"Error iterating sink pads on element '{element.get_name() or element}'"
                )
                break

    return len(errors) == 0, errors
