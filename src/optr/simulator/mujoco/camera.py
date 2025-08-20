from typing import NamedTuple

import mujoco


class Camera(NamedTuple):
    id: int
    name: str


def list(model: mujoco.MjModel) -> list[Camera]:
    """Get list of available cameras in the model.

    Args:
        model: MuJoCo model instance

    Returns:
        List of Camera objects containing camera id and name
    """

    return [Camera(id=i, name=model.cam(i).name) for i in range(model.ncam)]


def find(model: mujoco.MjModel, name: str) -> int | None:
    """Find camera ID by name.

    Args:
        model: MuJoCo model instance
        name: Camera name to search for (case-sensitive)

    Returns:
        Camera ID if found, None otherwise
    """

    return next((i for i in range(model.ncam) if model.cam(i).name == name), None)


def resolve(model: mujoco.MjModel, identifier: int | str | None) -> int | None:
    """Resolve camera identifier (name or ID) to numeric ID.

    Args:
        model: MuJoCo model instance
        identifier: Camera ID (int), name (str), or None

    Returns:
        Camera ID if found, None otherwise
    """
    return find(model, identifier) if isinstance(identifier, str) else identifier
