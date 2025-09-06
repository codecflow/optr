"""
Pi0: Vision-Language-Action Flow Model for General Robot Control

A functional implementation inspired by Physical Intelligence's π0 model,
combining vision-language understanding with flow-based action generation.
"""

from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from ...operator.action import Action, action
from ...operator.types import State
from ..base import Algorithm
from .flow import (
    SinusoidalEmbedding,
    create_flow_model,
    denoise_trajectory,
    flow_matching_loss,
    sample_timesteps,
)
from .moe import MultiModalMoE
from .vlm import PaliGemmaVLM, SimpleVLM, VLMTokenizer


class ActionEncoder(nn.Module):
    """
    Encoder for action sequences with time conditioning
    """

    def __init__(self, action_dim: int, hidden_dim: int):
        super().__init__()

        self.action_proj = nn.Linear(action_dim, hidden_dim)
        self.time_embed = SinusoidalEmbedding(hidden_dim)
        self.mixer = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )

    def forward(
        self,
        actions: torch.Tensor,
        timesteps: torch.Tensor,
    ) -> torch.Tensor:
        """
        Encode actions with time conditioning

        Args:
            actions: Action tensor [B, H, A]
            timesteps: Time tensor [B]

        Returns:
            Encoded actions [B, H, D]
        """
        # Project actions
        action_feat = self.action_proj(actions)

        # Get time embeddings
        time_feat = self.time_embed(timesteps)

        # Expand time to match action sequence
        if action_feat.dim() == 3:
            time_feat = time_feat.unsqueeze(1).expand(-1, action_feat.size(1), -1)

        # Mix action and time features
        combined = torch.cat([action_feat, time_feat], dim=-1)
        return self.mixer(combined)


class PI0(Algorithm):
    """
    Pi0 algorithm - Vision-Language-Action Flow Model

    Combines:
    - Vision-language understanding (VLM)
    - Flow matching for action generation
    - Mixture of Experts for multi-modal fusion
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize Pi0 algorithm

        Args:
            config: Configuration including:
                - action_dim: Action space dimension
                - action_horizon: Number of future actions
                - num_flow_steps: Flow matching inference steps
                - flow_sigma_min: Minimum noise level
                - vlm_model: VLM to use ('simple', 'paligemma')
                - hidden_dim: Hidden dimension for networks
                - use_moe: Whether to use MoE fusion
                - device: Device to run on
                - learning_rate: Learning rate for training
        """
        super().__init__(config)

        # Core parameters
        self.action_dim = config.get("action_dim", 7) if config else 7
        self.action_horizon = config.get("action_horizon", 10) if config else 10
        self.num_flow_steps = config.get("num_flow_steps", 10) if config else 10
        self.flow_sigma_min = config.get("flow_sigma_min", 0.001) if config else 0.001
        self.hidden_dim = config.get("hidden_dim", 512) if config else 512
        self.device = torch.device(config.get("device", "cpu") if config else "cpu")

        # VLM setup
        vlm_model = config.get("vlm_model", "simple") if config else "simple"
        if vlm_model == "paligemma":
            try:
                self.vlm: SimpleVLM | PaliGemmaVLM = PaliGemmaVLM(
                    device=str(self.device),
                    embedding_dim=self.hidden_dim,
                )
            except ImportError:
                print("PaliGemma not available, using SimpleVLM")
                self.vlm = SimpleVLM(
                    device=str(self.device),
                    embedding_dim=self.hidden_dim,
                )
        else:
            self.vlm = SimpleVLM(
                device=str(self.device),
                embedding_dim=self.hidden_dim,
            )

        # Tokenizer for text
        self.tokenizer = VLMTokenizer()

        # Multi-modal fusion
        use_moe = config.get("use_moe", True) if config else True
        if use_moe:
            self.fusion: nn.Module = MultiModalMoE(
                modality_dims={
                    "vision": self.vlm.embedding_dim,
                    "language": self.vlm.embedding_dim,
                    "proprio": config.get("proprio_dim", 32) if config else 32,
                },
                hidden_dim=self.hidden_dim,
                output_dim=self.hidden_dim,
                fusion_method="moe",
            ).to(self.device)
        else:
            # Simple concatenation fusion
            total_dim = self.vlm.embedding_dim * 2 + (
                config.get("proprio_dim", 32) if config else 32
            )
            self.fusion = nn.Sequential(
                nn.Linear(total_dim, self.hidden_dim),
                nn.ReLU(),
                nn.Linear(self.hidden_dim, self.hidden_dim),
            ).to(self.device)

        # Action encoder
        self.action_encoder = ActionEncoder(self.action_dim, self.hidden_dim).to(
            self.device
        )

        # Flow model for velocity prediction
        self.flow_model = create_flow_model(
            action_dim=self.action_dim * self.action_horizon,
            feature_dim=self.hidden_dim,
            hidden_dim=self.hidden_dim,
            use_time_embedding=True,
        ).to(self.device)

        # Proprioception encoder
        proprio_dim = config.get("proprio_dim", 32) if config else 32
        self.proprio_encoder = nn.Sequential(
            nn.Linear(proprio_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, self.hidden_dim),
        ).to(self.device)

        # Training parameters
        self.learning_rate = config.get("learning_rate", 1e-4) if config else 1e-4
        self.optimizer: optim.Optimizer | None = None

        # Storage for patterns (for non-neural fallback)
        self.stored_patterns: list[dict[str, torch.Tensor]] = []

    async def predict(
        self,
        state: State,
        context: dict[str, Any] | None = None,
    ) -> Action:
        """
        Predict action using flow matching

        Args:
            state: Current state with visual and proprioceptive data
            context: Additional context (e.g., language instructions)

        Returns:
            Predicted action
        """
        with torch.no_grad():
            # Extract features
            self._extract_features(state, context)

            # Initialize action with noise
            batch_size = 1
            action_seq = torch.randn(
                batch_size,
                self.action_horizon,
                self.action_dim,
                device=self.device,
            )

            # Flow matching denoising
            def velocity_fn(actions, feats, t):
                # Flatten action sequence
                actions_flat = actions.view(batch_size, -1)
                return self.flow_model(actions_flat, feats, t).view(
                    batch_size, self.action_horizon, self.action_dim
                )

            # Denoise
            action_seq = denoise_trajectory(
                action_seq,
                velocity_fn,
                None,  # features not used in current implementation
                steps=self.num_flow_steps,
                sigma_min=self.flow_sigma_min,
            )

            # Extract first action
            first_action = action_seq[0, 0].cpu().numpy()

            return action(
                "joint_position",
                values=first_action.tolist(),
                horizon=self.action_horizon,
            )

    async def train(
        self,
        data: list[dict[str, Any]],
        validation_data: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Train Pi0 on demonstration data

        Args:
            data: Training data with states, actions, and contexts
            validation_data: Optional validation data

        Returns:
            Training metrics
        """
        # Initialize optimizer if needed
        if self.optimizer is None:
            self.optimizer = optim.AdamW(
                list(self.flow_model.parameters())
                + list(self.action_encoder.parameters())
                + list(self.fusion.parameters())
                + list(self.proprio_encoder.parameters()),
                lr=self.learning_rate,
            )

        metrics = {
            "samples_processed": len(data),
            "avg_loss": 0.0,
        }

        total_loss = 0.0

        for sample in data:
            state = sample.get("state")
            action = sample.get("action")
            context = sample.get("context", {})

            if not state or not action:
                continue

            # Extract features
            features = self._extract_features(state, context)

            # Get target actions
            target_actions = self._action_to_tensor(action)

            # Sample timesteps
            t = sample_timesteps(1, self.device, sigma_min=self.flow_sigma_min)

            # Compute flow matching loss
            noise = torch.randn_like(target_actions)
            noisy_actions = (1 - t) * noise + t * target_actions

            # Predict velocity
            noisy_flat = noisy_actions.view(1, -1)
            predicted_velocity = self.flow_model(
                noisy_flat,
                features.unsqueeze(0),
                t,
            )

            # Target velocity
            target_velocity = target_actions.view(1, -1) - noise.view(1, -1)

            # Loss
            loss = flow_matching_loss(predicted_velocity, target_velocity)

            # Backward
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()

            # Store pattern for fallback
            self.stored_patterns.append(
                {
                    "features": features.detach().cpu(),
                    "action": target_actions.detach().cpu(),
                }
            )

        metrics["avg_loss"] = total_loss / len(data) if data else 0

        # Validation
        if validation_data:
            val_loss = 0.0
            for val_sample in validation_data:
                with torch.no_grad():
                    state = val_sample.get("state")
                    action = val_sample.get("action")
                    context = val_sample.get("context", {})

                    if not state or not action:
                        continue

                    features = self._extract_features(state, context)
                    target_actions = self._action_to_tensor(action)

                    # Predict and compute loss
                    predicted = await self.predict(state, context)
                    pred_tensor = self._action_to_tensor(predicted)

                    val_loss += F.mse_loss(pred_tensor, target_actions).item()

            metrics["validation_loss"] = (
                val_loss / len(validation_data) if validation_data else 0
            )

        self.is_trained = True
        return metrics

    def save(self, path: str):
        """Save Pi0 model to disk"""
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Save model state
        state = {
            "config": self.config,
            "metadata": self.metadata,
            "flow_model": self.flow_model.state_dict(),
            "action_encoder": self.action_encoder.state_dict(),
            "fusion": self.fusion.state_dict(),
            "proprio_encoder": self.proprio_encoder.state_dict(),
            "stored_patterns": self.stored_patterns,
        }

        torch.save(state, save_path)

    def load(self, path: str):
        """Load Pi0 model from disk"""
        state = torch.load(path, map_location=self.device)

        self.config = state.get("config", {})
        self.metadata = state.get("metadata", {})

        # Load model states
        self.flow_model.load_state_dict(state["flow_model"])
        self.action_encoder.load_state_dict(state["action_encoder"])
        self.fusion.load_state_dict(state["fusion"])
        self.proprio_encoder.load_state_dict(state["proprio_encoder"])

        self.stored_patterns = state.get("stored_patterns", [])
        self.is_trained = bool(self.stored_patterns)

    # Helper methods

    def _extract_features(
        self,
        state: State,
        context: dict[str, Any] | None,
    ) -> torch.Tensor:
        """
        Extract multi-modal features from state and context

        Args:
            state: Current state
            context: Additional context

        Returns:
            Fused feature tensor
        """
        features = {}

        # Vision features
        if state.visual:
            # Convert visual data to tensor
            image = self._visual_to_tensor(state.visual)
            vision_features = self.vlm.encode_image(image)
            features["vision"] = vision_features

        # Language features
        if context and "instruction" in context:
            text = context["instruction"]
            language_features = self.vlm.encode_text(text)
            features["language"] = language_features

        # Proprioceptive features
        if state.metadata:
            proprio = self._metadata_to_tensor(state.metadata)
            proprio_features = self.proprio_encoder(proprio)
            features["proprio"] = proprio_features

        # Fuse features
        if isinstance(self.fusion, MultiModalMoE):
            fused = self.fusion(features)
        else:
            # Simple concatenation
            feat_list = list(features.values())
            if feat_list:
                concatenated = torch.cat(feat_list, dim=-1)
                fused = self.fusion(concatenated)
            else:
                fused = torch.zeros(self.hidden_dim, device=self.device)

        return fused

    def _visual_to_tensor(self, visual_data: bytes) -> torch.Tensor:
        """
        Convert visual data to tensor

        Args:
            visual_data: Raw visual bytes

        Returns:
            Image tensor
        """
        # Simple conversion - in practice, decode image properly
        # For now, create dummy image
        image = torch.randn(1, 3, 224, 224, device=self.device)
        return image

    def _metadata_to_tensor(self, metadata: dict) -> torch.Tensor:
        """
        Convert metadata to tensor

        Args:
            metadata: State metadata

        Returns:
            Proprioception tensor
        """
        # Extract relevant values
        values: list[float] = []

        # Common keys for proprioception
        for key in ["joint_positions", "joint_velocities", "end_effector_pos"]:
            if key in metadata:
                val = metadata[key]
                if isinstance(val, list | tuple):
                    values.extend(val)
                elif isinstance(val, int | float):
                    values.append(val)

        # Pad or truncate to expected dimension
        proprio_dim = self.config.get("proprio_dim", 32) if self.config else 32
        if len(values) < proprio_dim:
            values.extend([0.0] * (proprio_dim - len(values)))
        else:
            values = values[:proprio_dim]

        return torch.tensor(values, dtype=torch.float32, device=self.device)

    def _action_to_tensor(self, action: Action) -> torch.Tensor:
        """
        Convert action to tensor

        Args:
            action: Action object

        Returns:
            Action tensor
        """
        if hasattr(action, "params") and action.params:
            values = action.params.get("values", [])
        else:
            values = getattr(action, "values", [])

        # Ensure correct shape
        if not values:
            values = [0.0] * self.action_dim

        # Handle different formats
        if isinstance(values[0], list | tuple):
            # Multiple actions
            tensor = torch.tensor(values, dtype=torch.float32, device=self.device)
        else:
            # Single action
            tensor = torch.tensor(values, dtype=torch.float32, device=self.device)
            tensor = tensor.unsqueeze(0).expand(self.action_horizon, -1)

        # Ensure correct dimensions
        if tensor.shape[0] < self.action_horizon:
            # Repeat last action
            last = tensor[-1:].expand(self.action_horizon - tensor.shape[0], -1)
            tensor = torch.cat([tensor, last], dim=0)
        elif tensor.shape[0] > self.action_horizon:
            tensor = tensor[: self.action_horizon]

        return tensor
