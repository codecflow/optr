from enum import Enum

import numpy as np
from mujoco import MjData


class Layout(Enum):
    Render = ("qpos", "qvel", "mocap_pos", "mocap_quat", "time")


class Codec:
    """Serializes MuJoCo simulation state for efficient inter-process communication.

    Provides bidirectional conversion between MuJoCo's structured state data
    and flat numpy arrays suitable for shared memory or network transmission.
    Uses minimal layout-based encoding with (name, end) tuples for clean structure.
    """

    def __init__(self, slices: dict, length: int, dtype=np.float64):
        """Initialize codec with pre-computed slices.

        Args:
            slices: Dictionary mapping field names to slice objects
            length: Total buffer length
            dtype: Data type for the buffer
        """
        self.slices = slices
        self.length = length
        self.dtype = np.dtype(dtype)
        self.nbytes = length * self.dtype.itemsize

    @classmethod
    def create(cls, model, fields: Layout = Layout.Render, dtype=np.float64):
        """Create codec instance from model with specified fields.

        Args:
            model: MuJoCo model object
            fields: Layout enum or tuple of field names to include
            dtype: Data type for the buffer

        Returns:
            Codec instance with pre-computed slices
        """
        slices = {}
        start = 0

        for field in fields.value:
            size = 0
            if field == "qpos":
                size = model.nq
            elif field == "qvel":
                size = model.nv
            elif field == "mocap_pos" and model.nmocap > 0:
                size = model.nmocap * 3
            elif field == "mocap_quat" and model.nmocap > 0:
                size = model.nmocap * 4
            elif field == "time":
                size = 1

            if size > 0:
                slices[field] = slice(start, start + size)
                start += size

        return cls(slices, start, dtype)

    def empty(self) -> np.ndarray:
        """Create zero-initialized buffer with correct size and dtype for encoding."""
        return np.zeros(self.length, dtype=self.dtype)

    def encode(self, data: MjData, dst: np.ndarray) -> np.ndarray:
        """Serialize MuJoCo state into flat array for transmission.

        Args:
            data: MuJoCo simulation data containing state vectors
            dst: Pre-allocated buffer with correct size and dtype

        Returns:
            Flat array containing serialized state data
        """

        if "qpos" in self.slices:
            dst[self.slices["qpos"]] = data.qpos
        if "qvel" in self.slices:
            dst[self.slices["qvel"]] = data.qvel
        if "mocap_pos" in self.slices:
            dst[self.slices["mocap_pos"]] = data.mocap_pos.ravel()
        if "mocap_quat" in self.slices:
            dst[self.slices["mocap_quat"]] = data.mocap_quat.ravel()
        if "time" in self.slices:
            dst[self.slices["time"]] = data.time

        return dst

    def decode(self, src: np.ndarray, data: MjData) -> MjData:
        """Deserialize flat array back into MuJoCo state vectors.

        Args:
            src: Flat array containing serialized state data
            data: MuJoCo data object to populate with deserialized state

        Returns:
            The modified data object for method chaining
        """

        if "qpos" in self.slices:
            data.qpos[:] = src[self.slices["qpos"]]
        if "qvel" in self.slices:
            data.qvel[:] = src[self.slices["qvel"]]
        if "mocap_pos" in self.slices:
            data.mocap_pos[:] = src[self.slices["mocap_pos"]].reshape(-1, 3)
        if "mocap_quat" in self.slices:
            data.mocap_quat[:] = src[self.slices["mocap_quat"]].reshape(-1, 4)
        if "time" in self.slices:
            data.time = src[self.slices["time"]][0]

        return data
