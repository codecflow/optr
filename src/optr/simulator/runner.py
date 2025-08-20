"""Base simulation runner."""

from collections.abc import Generator

from .clock import Clock, Null
from .simulation import Simulation, State


def run(
    sim: Simulation[State], /, steps: int = None, clock: Clock = None
) -> Generator[State, None, None]:
    """Run simulation with optional timing control.

    Args:
        sim: Simulator implementing the Simulation protocol
        steps: Number of steps to run (None for infinite)
        clock: Clock for timing control (None for no timing)

    Yields:
        Simulation state after each step
    """

    clock = clock or Null()
    iterator = range(steps) if steps is not None else iter(int, 1)
    for _ in iterator:
        clock.tick()
        state = sim.step()
        yield state
        clock.sync()
