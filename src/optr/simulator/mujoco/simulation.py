"""MuJoCo simulation implementation."""

from typing import NamedTuple, Protocol

import mujoco

from ..simulation import Simulation as BaseSimulation


class State(NamedTuple):
    """MuJoCo state with model and data."""

    model: mujoco.MjModel
    data: mujoco.MjData


class Simulation(BaseSimulation[State], Protocol):
    """MuJoCo simulation protocol."""

    ...
