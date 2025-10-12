"""
Base robot connector interface
"""

from abc import abstractmethod
from typing import Any

from ...operator.types import State
from ..base import BaseConnector


class Robot(BaseConnector):
    """Abstract base class for robot connectors"""

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to robot"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to robot"""
        pass

    @abstractmethod
    async def get_joint_positions(self) -> dict[int, float]:
        """
        Get current joint positions
        
        Returns:
            Dictionary mapping joint IDs to their positions
        """
        pass

    @abstractmethod
    async def set_joint_positions(
        self, positions: dict[int, float], duration: float = 1.0
    ) -> bool:
        """
        Set target joint positions
        
        Args:
            positions: Dictionary mapping joint IDs to target positions
            duration: Time in seconds to reach target positions
            
        Returns:
            True if command was sent successfully
        """
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if robot is connected"""
        pass

    async def get_state(self) -> State:
        """Get current robot state with joint positions"""
        positions = await self.get_joint_positions()
        return State.create(joint_positions=positions)

    async def execute_action(self, action_type: str, **params) -> bool:
        """
        Execute robot-specific action
        
        Supported actions:
            - "move": Set joint positions
            - "get_positions": Get current joint positions
            - "connect": Establish connection
            - "disconnect": Close connection
        """
        if action_type == "move":
            positions = params.get("positions", {})
            duration = params.get("duration", 1.0)
            return await self.set_joint_positions(positions, duration)
        elif action_type == "get_positions":
            await self.get_joint_positions()
            return True
        elif action_type == "connect":
            return await self.connect()
        elif action_type == "disconnect":
            await self.disconnect()
            return True
        else:
            raise ValueError(f"Unknown robot action: {action_type}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

