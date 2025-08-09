"""
Base connector interface
"""

from abc import ABC, abstractmethod

from ..types import State


class BaseConnector(ABC):
    """Abstract base class for all connectors"""

    @abstractmethod
    async def get_state(self) -> State:
        """Get current state"""
        pass

    @abstractmethod
    async def execute_action(self, action_type: str, **params) -> bool:
        """Execute environment-specific action"""
        pass
