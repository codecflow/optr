from typing import NamedTuple

import mujoco


class Keyframe(NamedTuple):
    id: int
    name: str


ID = int | str | None


def all(model: mujoco.MjModel) -> list[Keyframe]:
    """Get all available keyframes in the model.

    Args:
        model: MuJoCo model instance

    Returns:
        List of Key objects containing keyframe id and name
    """
    return [Keyframe(id=i, name=model.key(i).name) for i in range(model.nkey)]


def find(model: mujoco.MjModel, name: str) -> int | None:
    """Find keyframe ID by name.

    Args:
        model: MuJoCo model instance
        name: Keyframe name to search for

    Returns:
        Keyframe ID if found, None otherwise
    """
    return next((i for i in range(model.nkey) if model.key(i).name == name), None)


def resolve(model: mujoco.MjModel, identifier: ID) -> int | None:
    """Resolve keyframe identifier (name or ID) to numeric ID.

    Args:
        model: MuJoCo model instance
        identifier: Keyframe ID (int), name (str), or None

    Returns:
        Keyframe ID if found, None otherwise
    """

    return find(model, identifier) if isinstance(identifier, str) else identifier


def reset(model: mujoco.MjModel, data: mujoco.MjData, identifier: ID) -> None:
    """Reset simulation data to specified keyframe state.

    Args:
        model: MuJoCo model instance
        data: MuJoCo data instance
        identifier: Keyframe ID (int), name (str), or None
    """
    keyframe = resolve(model, identifier)
    if keyframe is not None:
        mujoco.mj_resetDataKeyframe(model, data, keyframe)
