"""
Base desktop connector
"""

from abc import abstractmethod

from ...operator.types import State
from ..base import BaseConnector


class Desktop(BaseConnector):
    """Abstract base class for desktop connectors"""

    @abstractmethod
    async def screenshot(self) -> bytes:
        """Take screenshot"""
        pass

    @abstractmethod
    async def click(self, x: int, y: int) -> bool:
        """Click at coordinates"""
        pass

    @abstractmethod
    async def type_text(self, text: str) -> bool:
        """Type text"""
        pass

    @abstractmethod
    async def key(self, key: str) -> bool:
        """Press key"""
        pass

    async def get_state(self) -> State:
        """Get current desktop state"""
        screenshot = await self.screenshot()
        return State.create(visual=screenshot)

    async def execute_action(self, action_type: str, **params) -> bool:
        """Execute desktop-specific action"""
        if action_type == "click":
            return await self.click(params["x"], params["y"])
        elif action_type == "type":
            return await self.type_text(params["text"])
        elif action_type == "key":
            return await self.key(params["key"])
        else:
            raise ValueError(f"Unknown desktop action: {action_type}")
