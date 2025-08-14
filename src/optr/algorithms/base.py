"""
Base class for all algorithms
"""

from abc import ABC, abstractmethod
from typing import Any

from ..operator.action import Action
from ..operator.types import State


class Algorithm(ABC):
    """
    Abstract base class for algorithms used in operators
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize algorithm

        Args:
            config: Algorithm configuration
        """
        self.config = config or {}
        self.is_trained = False
        self.metadata = {}

    @abstractmethod
    async def predict(
        self, state: State, context: dict[str, Any] | None = None
    ) -> Action:
        """
        Predict next action given current state

        Args:
            state: Current state
            context: Additional context

        Returns:
            Predicted action
        """
        pass

    @abstractmethod
    async def train(
        self,
        data: list[dict[str, Any]],
        validation_data: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Train the algorithm on data

        Args:
            data: Training data
            validation_data: Optional validation data

        Returns:
            Training metrics
        """
        pass

    @abstractmethod
    def save(self, path: str):
        """Save algorithm state to disk"""
        pass

    @abstractmethod
    def load(self, path: str):
        """Load algorithm state from disk"""
        pass

    def preprocess_state(self, state: State) -> Any:
        """
        Preprocess state for algorithm input

        Args:
            state: Raw state

        Returns:
            Preprocessed state
        """
        # Default: return state as-is
        return state

    def postprocess_action(self, action: Any) -> Action:
        """
        Postprocess algorithm output to action

        Args:
            action: Raw algorithm output

        Returns:
            Action object
        """
        # Default: assume action is already an Action object
        if isinstance(action, Action):
            return action

        # Try to convert dict to Action
        if isinstance(action, dict):
            return Action(**action)

        raise ValueError(f"Cannot convert {type(action)} to Action")

    def get_info(self) -> dict[str, Any]:
        """Get algorithm information"""
        return {
            "class": self.__class__.__name__,
            "config": self.config,
            "is_trained": self.is_trained,
            "metadata": self.metadata,
        }
