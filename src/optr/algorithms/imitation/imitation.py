"""
Imitation learning algorithm for learning from demonstrations
"""

import json
from pathlib import Path
from typing import Any

from ...operator.action import Action
from ...operator.types import State
from ..base import Algorithm


class Imitation(Algorithm):
    """
    Simple imitation learning algorithm that learns from demonstrations
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.demonstrations = []
        self.policy = {}

    async def predict(
        self, state: State, context: dict[str, Any] | None = None
    ) -> Action:
        """
        Predict action based on learned demonstrations

        Args:
            state: Current state
            context: Additional context

        Returns:
            Predicted action
        """
        # Simple nearest neighbor approach
        # In production, use more sophisticated matching

        state_key = self._state_to_key(state)

        if state_key in self.policy:
            return self.policy[state_key]

        # Find most similar demonstration
        best_match = self._find_similar_state(state)
        if best_match:
            return best_match["action"]

        # Default action if no match found
        return Action(type="wait", params={})

    async def train(
        self,
        data: list[dict[str, Any]],
        validation_data: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Train on demonstration data

        Args:
            data: List of (state, action) pairs
            validation_data: Optional validation data

        Returns:
            Training metrics
        """
        self.demonstrations = data

        # Build policy mapping
        for demo in data:
            state = demo.get("state")
            action = demo.get("action")

            if state and action:
                state_key = self._state_to_key(state)
                self.policy[state_key] = action

        self.is_trained = True

        metrics = {"demonstrations_count": len(data), "policy_size": len(self.policy)}

        # Validate if data provided
        if validation_data:
            correct = 0
            for val in validation_data:
                predicted = await self.predict(val["state"])
                if predicted == val["action"]:
                    correct += 1

            metrics["validation_accuracy"] = correct / len(validation_data)

        return metrics

    def save(self, path: str):
        """Save learned policy to disk"""
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "policy": {k: v.__dict__ for k, v in self.policy.items()},
            "config": self.config,
            "metadata": self.metadata,
        }

        with open(save_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, path: str):
        """Load learned policy from disk"""
        with open(path) as f:
            data = json.load(f)

        self.config = data.get("config", {})
        self.metadata = data.get("metadata", {})

        # Reconstruct policy
        self.policy = {}
        for k, v in data.get("policy", {}).items():
            self.policy[k] = Action(**v)

        self.is_trained = len(self.policy) > 0

    def _state_to_key(self, state: State) -> str:
        """Convert state to hashable key"""
        # Simple implementation - in production use better state representation
        if state.metadata:
            return str(state.metadata)
        return str(state.timestamp)

    def _find_similar_state(self, state: State) -> dict[str, Any] | None:
        """Find most similar state in demonstrations"""
        # Simple implementation - in production use similarity metrics
        target_key = self._state_to_key(state)

        for demo in self.demonstrations:
            demo_key = self._state_to_key(demo.get("state"))
            if demo_key == target_key:
                return demo

        return None
