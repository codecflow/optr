"""
Base operator class
"""

from typing import Any

from ..connector.base import BaseConnector
from .types import State


class Operator:
    """Generic operator that can work with any connector(s)"""

    def __init__(self, connectors: dict[str, BaseConnector]):
        """
        Initialize operator with one or more connectors

        Args:
            connectors: Dictionary of named connectors
                       e.g. {"desktop": DesktopConnector(), "robot": RobotConnector()}
        """
        self.connectors = connectors
        self._states = {}

    async def get_state(self, connector_name: str = None) -> State:
        """Get state from specific connector or first available"""
        if connector_name:
            if connector_name not in self.connectors:
                raise ValueError(f"Connector '{connector_name}' not found")
            connector = self.connectors[connector_name]
        else:
            # Use first connector if not specified
            connector_name = next(iter(self.connectors))
            connector = self.connectors[connector_name]

        state = await connector.get_state()
        self._states[connector_name] = state
        return state

    async def execute_action(
        self, action_type: str, connector_name: str = None, **params
    ) -> bool:
        """Execute action on specific connector"""
        if connector_name:
            if connector_name not in self.connectors:
                raise ValueError(f"Connector '{connector_name}' not found")
            connector = self.connectors[connector_name]
        else:
            # Use first connector if not specified
            connector = next(iter(self.connectors.values()))

        return await connector.execute_action(action_type, **params)

    async def run(self, task: dict[str, Any]) -> Any:
        """
        Run a task across connectors

        Task format:
        {
            "connector": "desktop",  # optional, defaults to first
            "action": "click",
            "params": {"x": 100, "y": 200}
        }
        """
        connector_name = task.get("connector")
        action = task.get("action")
        params = task.get("params", {})

        return await self.execute_action(action, connector_name, **params)

    def add_connector(self, name: str, connector: BaseConnector):
        """Add a new connector"""
        self.connectors[name] = connector

    def remove_connector(self, name: str):
        """Remove a connector"""
        if name in self.connectors:
            del self.connectors[name]
            if name in self._states:
                del self._states[name]
