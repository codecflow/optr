"""Generic protocols for interactive, hookable simulations with type safety."""

from collections.abc import Callable, Hashable
from typing import Protocol


class Hookable[E: Hashable, **P, R, S](Protocol):
    """Protocol for extension points, events, and transformation hooks.

    Enables objects to expose hookable points for:
    - Event observation (observer pattern)
    - Data transformation (middleware pattern)
    - Plugin extensions (plugin pattern)

    Type Parameters:
        E: Event type (must be Hashable)
        P: Handler parameters
        R: Handler return type
        S: Subscription handle type

    Examples:
        button.on("click", handle_click)
        processor.on("text:transform", str.upper)
        sim.on("step:after", update_display)
    """

    def on(self, event: E, handler: Callable[P, R]) -> S:
        """Register handler for event or extension point.

        Returns subscription handle for unregistering.
        """
        ...


class Triggerable[**P, R](Protocol):
    """Protocol for objects controlled via external triggers.

    Provides inbound control interface for external commands.

    Type Parameters:
        P: Trigger parameters
        R: Return type

    Examples:
        robot.trigger("move", x=10, y=20)
        sim.trigger("step", dt=0.01)
        sensor.trigger("read", samples=10)

    Relationship with Hookable:
        - Triggerable: External → Object (inbound)
        - Hookable: Object → External (outbound)
    """

    def trigger(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Trigger operation or command on the object."""
        ...
