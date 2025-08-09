"""
PI0 (Pi-Zero) - Vision-Language-Action Flow Model
Basic implementation inspired by Physical Intelligence's π0 model
"""

import json
from pathlib import Path
from typing import Any

import numpy as np

from ...types import Action, State
from ..base import Algorithm


class PI0(Algorithm):
    """
    PI0 algorithm - combines vision, language, and action through flow matching

    This is a simplified implementation that demonstrates the core concepts:
    - Vision-language understanding for context
    - Flow matching for action generation
    - Multi-modal fusion of inputs
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize PI0 algorithm

        Args:
            config: Configuration including:
                - action_dim: Dimension of action space
                - action_horizon: Number of future actions to predict
                - num_inference_steps: Number of flow matching steps
                - flow_sigma_min: Minimum noise level for flow
                - use_vision: Whether to use visual input
                - use_language: Whether to use language input
        """
        super().__init__(config)

        # Core parameters
        self.action_dim = config.get("action_dim", 7)  # Default 7-DOF
        self.action_horizon = config.get("action_horizon", 10)
        self.num_inference_steps = config.get("num_inference_steps", 10)
        self.flow_sigma_min = config.get("flow_sigma_min", 0.001)

        # Modality flags
        self.use_vision = config.get("use_vision", True)
        self.use_language = config.get("use_language", True)

        # Storage for learned patterns
        self.vision_patterns = {}
        self.language_patterns = {}
        self.action_flows = {}
        self.context_embeddings = {}

    async def predict(
        self, state: State, context: dict[str, Any] | None = None
    ) -> Action:
        """
        Predict action using flow matching approach

        Args:
            state: Current state with visual and proprioceptive data
            context: Additional context (e.g., language instructions)

        Returns:
            Predicted action
        """
        # Extract multi-modal features
        features = self._extract_features(state, context)

        # Initialize action with noise
        action_sequence = self._initialize_action_sequence()

        # Flow matching: iteratively denoise the action
        for step in range(self.num_inference_steps):
            t = step / self.num_inference_steps

            # Predict velocity field
            velocity = self._predict_velocity(action_sequence, features, t)

            # Update action sequence
            dt = 1.0 / self.num_inference_steps
            action_sequence = action_sequence + dt * velocity

        # Extract first action from sequence
        action_params = {
            "values": action_sequence[0].tolist() if len(action_sequence) > 0 else [],
            "horizon": self.action_horizon,
        }

        return Action(type="flow_action", params=action_params)

    async def train(
        self,
        data: list[dict[str, Any]],
        validation_data: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Train PI0 on demonstration data

        Args:
            data: Training data with states, actions, and contexts
            validation_data: Optional validation data

        Returns:
            Training metrics
        """
        metrics = {
            "samples_processed": len(data),
            "vision_patterns_learned": 0,
            "language_patterns_learned": 0,
            "action_flows_learned": 0,
        }

        for sample in data:
            state = sample.get("state")
            action = sample.get("action")
            context = sample.get("context", {})

            # Learn vision patterns
            if self.use_vision and state and state.visual:
                vision_key = self._encode_visual(state.visual)
                self.vision_patterns[vision_key] = {
                    "features": self._extract_visual_features(state.visual),
                    "action": action,
                }
                metrics["vision_patterns_learned"] += 1

            # Learn language patterns
            if self.use_language and "instruction" in context:
                lang_key = self._encode_language(context["instruction"])
                self.language_patterns[lang_key] = {
                    "embedding": self._embed_language(context["instruction"]),
                    "action": action,
                }
                metrics["language_patterns_learned"] += 1

            # Learn action flows
            if action:
                flow_key = self._create_flow_key(state, context)
                self.action_flows[flow_key] = {
                    "trajectory": self._create_action_trajectory(action),
                    "context": self._extract_features(state, context),
                }
                metrics["action_flows_learned"] += 1

        self.is_trained = True

        # Validation
        if validation_data:
            correct_predictions = 0
            for val_sample in validation_data:
                predicted = await self.predict(
                    val_sample["state"], val_sample.get("context")
                )
                if self._actions_similar(predicted, val_sample["action"]):
                    correct_predictions += 1

            metrics["validation_accuracy"] = correct_predictions / len(validation_data)

        return metrics

    def save(self, path: str):
        """Save PI0 model to disk"""
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "config": self.config,
            "metadata": self.metadata,
            "vision_patterns": self._serialize_patterns(self.vision_patterns),
            "language_patterns": self._serialize_patterns(self.language_patterns),
            "action_flows": self._serialize_flows(self.action_flows),
        }

        with open(save_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, path: str):
        """Load PI0 model from disk"""
        with open(path) as f:
            data = json.load(f)

        self.config = data.get("config", {})
        self.metadata = data.get("metadata", {})
        self.vision_patterns = self._deserialize_patterns(
            data.get("vision_patterns", {})
        )
        self.language_patterns = self._deserialize_patterns(
            data.get("language_patterns", {})
        )
        self.action_flows = self._deserialize_flows(data.get("action_flows", {}))

        self.is_trained = bool(self.action_flows)

    # Private helper methods

    def _extract_features(
        self, state: State, context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Extract multi-modal features from state and context"""
        features = {}

        # Visual features
        if self.use_vision and state.visual:
            features["vision"] = self._extract_visual_features(state.visual)

        # Language features
        if self.use_language and context and "instruction" in context:
            features["language"] = self._embed_language(context["instruction"])

        # Proprioceptive features
        if state.metadata:
            features["proprio"] = state.metadata

        return features

    def _initialize_action_sequence(self) -> np.ndarray:
        """Initialize action sequence with noise"""
        return np.random.randn(self.action_horizon, self.action_dim) * 0.1

    def _predict_velocity(
        self, action_sequence: np.ndarray, features: dict[str, Any], t: float
    ) -> np.ndarray:
        """
        Predict velocity field for flow matching

        This is a simplified version - in production would use neural network
        """
        velocity = np.zeros_like(action_sequence)

        # Find similar patterns in learned data
        feature_key = self._create_flow_key_from_features(features)

        if feature_key in self.action_flows:
            target = self.action_flows[feature_key]["trajectory"]
            if isinstance(target, np.ndarray):
                # Simple linear interpolation towards target
                velocity = (target - action_sequence) * (1 - t)

        return velocity

    def _extract_visual_features(self, visual_data: Any) -> dict[str, Any]:
        """Extract features from visual data"""
        # Simplified: just return metadata about visual data
        return {
            "has_visual": visual_data is not None,
            "visual_hash": hash(str(visual_data)) if visual_data else None,
        }

    def _embed_language(self, instruction: str) -> dict[str, Any]:
        """Create embedding for language instruction"""
        # Simplified: use basic features
        return {
            "instruction": instruction,
            "length": len(instruction.split()),
            "hash": hash(instruction),
        }

    def _encode_visual(self, visual_data: Any) -> str:
        """Create key for visual data"""
        return f"visual_{hash(str(visual_data))}"

    def _encode_language(self, instruction: str) -> str:
        """Create key for language instruction"""
        return f"lang_{hash(instruction)}"

    def _create_flow_key(self, state: State, context: dict[str, Any] | None) -> str:
        """Create unique key for flow storage"""
        parts = []

        if state.visual:
            parts.append(f"v{hash(str(state.visual))}")

        if context and "instruction" in context:
            parts.append(f"l{hash(context['instruction'])}")

        if state.metadata:
            parts.append(f"m{hash(str(state.metadata))}")

        return "_".join(parts) if parts else "default"

    def _create_flow_key_from_features(self, features: dict[str, Any]) -> str:
        """Create flow key from extracted features"""
        parts = []

        if "vision" in features:
            parts.append(f"v{features['vision'].get('visual_hash', 0)}")

        if "language" in features:
            parts.append(f"l{features['language'].get('hash', 0)}")

        if "proprio" in features:
            parts.append(f"m{hash(str(features['proprio']))}")

        return "_".join(parts) if parts else "default"

    def _create_action_trajectory(self, action: Action) -> np.ndarray:
        """Convert action to trajectory representation"""
        if isinstance(action.params.get("values"), list):
            values = np.array(action.params["values"])

            # Extend to full horizon if needed
            if len(values.shape) == 1:
                trajectory = np.tile(values, (self.action_horizon, 1))
            else:
                trajectory = values

            return trajectory[: self.action_horizon]

        return np.zeros((self.action_horizon, self.action_dim))

    def _actions_similar(
        self, action1: Action, action2: Action, threshold: float = 0.1
    ) -> bool:
        """Check if two actions are similar"""
        if action1.type != action2.type:
            return False

        values1 = action1.params.get("values", [])
        values2 = action2.params.get("values", [])

        if len(values1) != len(values2):
            return False

        if values1 and values2:
            diff = np.mean(np.abs(np.array(values1) - np.array(values2)))
            return diff < threshold

        return True

    def _serialize_patterns(self, patterns: dict) -> dict:
        """Serialize patterns for saving"""
        serialized = {}
        for key, value in patterns.items():
            serialized[key] = {
                k: v.tolist() if isinstance(v, np.ndarray) else v
                for k, v in value.items()
            }
        return serialized

    def _deserialize_patterns(self, patterns: dict) -> dict:
        """Deserialize patterns from saved data"""
        deserialized = {}
        for key, value in patterns.items():
            deserialized[key] = value
        return deserialized

    def _serialize_flows(self, flows: dict) -> dict:
        """Serialize action flows for saving"""
        serialized = {}
        for key, value in flows.items():
            serialized[key] = {
                "trajectory": value["trajectory"].tolist()
                if isinstance(value["trajectory"], np.ndarray)
                else value["trajectory"],
                "context": value.get("context", {}),
            }
        return serialized

    def _deserialize_flows(self, flows: dict) -> dict:
        """Deserialize action flows from saved data"""
        deserialized = {}
        for key, value in flows.items():
            deserialized[key] = {
                "trajectory": np.array(value["trajectory"])
                if "trajectory" in value
                else None,
                "context": value.get("context", {}),
            }
        return deserialized
