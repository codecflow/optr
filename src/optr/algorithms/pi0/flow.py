"""
Flow matching utilities for continuous action generation
"""

from collections.abc import Callable

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def sample_timesteps(
    batch_size: int,
    device: torch.device = None,
    alpha: float = 1.5,
    beta: float = 1.0,
    sigma_min: float = 0.001,
) -> torch.Tensor:
    """
    Sample timesteps for flow matching using Beta distribution

    Args:
        batch_size: Number of timesteps to sample
        device: Device to place tensors on
        alpha: Alpha parameter for Beta distribution
        beta: Beta parameter for Beta distribution
        sigma_min: Minimum noise level

    Returns:
        Sampled timesteps in [0, 1]
    """
    beta_dist = torch.distributions.Beta(alpha, beta)
    z = beta_dist.sample((batch_size,))
    t = (1 - sigma_min) * (1 - z)

    if device:
        t = t.to(device)

    return t


def compute_flow_velocity(
    current: torch.Tensor,
    target: torch.Tensor,
    t: torch.Tensor,
    sigma_min: float = 0.001,
) -> torch.Tensor:
    """
    Compute velocity field for flow matching

    Args:
        current: Current state/action
        target: Target state/action
        t: Current timestep(s)
        sigma_min: Minimum noise level

    Returns:
        Velocity vector
    """
    # Reshape t for broadcasting
    while t.dim() < current.dim():
        t = t.unsqueeze(-1)

    # Linear interpolation velocity
    noise = torch.randn_like(target)
    x0 = noise
    x1 = target

    # Conditional flow
    (1 - (1 - sigma_min) * t) * x0 + t * x1
    d_psi = x1 - (1 - sigma_min) * x0

    return d_psi


def denoise_trajectory(
    initial: torch.Tensor,
    velocity_fn: Callable,
    features: dict | None = None,
    steps: int = 10,
    sigma_min: float = 0.001,
) -> torch.Tensor:
    """
    Denoise trajectory using flow matching

    Args:
        initial: Initial noisy trajectory
        velocity_fn: Function to compute velocity (trajectory, features, t) -> velocity
        features: Optional features for conditioning
        steps: Number of denoising steps
        sigma_min: Minimum noise level

    Returns:
        Denoised trajectory
    """
    trajectory = initial.clone()
    dt = 1.0 / steps

    for step in range(steps):
        t = torch.full(
            (trajectory.shape[0],),
            step / steps,
            device=trajectory.device,
            dtype=trajectory.dtype,
        )

        velocity = velocity_fn(trajectory, features, t)
        trajectory = trajectory + dt * velocity

    return trajectory


def flow_matching_loss(
    predicted: torch.Tensor,
    target: torch.Tensor,
    mask: torch.Tensor | None = None,
) -> torch.Tensor:
    """
    Compute flow matching loss

    Args:
        predicted: Predicted velocity/flow
        target: Target velocity/flow
        mask: Optional mask for valid positions

    Returns:
        Flow matching loss
    """
    loss = F.mse_loss(predicted, target, reduction="none")

    if mask is not None:
        loss = loss * mask
        return loss.sum() / mask.sum()

    return loss.mean()


class SinusoidalEmbedding(nn.Module):
    """
    Sinusoidal positional/time embeddings
    """

    def __init__(self, dim: int, max_period: float = 10000.0):
        super().__init__()
        self.dim = dim
        self.max_period = max_period

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Create sinusoidal embeddings

        Args:
            x: Input positions/timesteps

        Returns:
            Sinusoidal embeddings
        """
        half_dim = self.dim // 2
        emb = np.log(self.max_period) / (half_dim - 1)
        emb = torch.exp(torch.arange(half_dim, device=x.device) * -emb)

        # Ensure x is at least 2D
        if x.dim() == 1:
            x = x.unsqueeze(-1)

        emb = x * emb.unsqueeze(0)
        emb = torch.cat([emb.sin(), emb.cos()], dim=-1)

        return emb


class FlowPredictor(nn.Module):
    """
    Simple neural network for predicting flow velocities
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 256,
        output_dim: int | None = None,
        num_layers: int = 3,
    ):
        super().__init__()

        if output_dim is None:
            output_dim = input_dim

        layers = []
        for i in range(num_layers):
            in_d = input_dim if i == 0 else hidden_dim
            out_d = output_dim if i == num_layers - 1 else hidden_dim

            layers.append(nn.Linear(in_d, out_d))
            if i < num_layers - 1:
                layers.append(nn.SiLU())

        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def create_flow_model(
    action_dim: int,
    feature_dim: int,
    hidden_dim: int = 256,
    use_time_embedding: bool = True,
) -> nn.Module:
    """
    Create a flow prediction model

    Args:
        action_dim: Dimension of actions
        feature_dim: Dimension of conditioning features
        hidden_dim: Hidden layer dimension
        use_time_embedding: Whether to use time embeddings

    Returns:
        Flow prediction model
    """

    class FlowModel(nn.Module):
        def __init__(self):
            super().__init__()

            # Time embedding
            self.time_emb = None
            time_dim = 0
            if use_time_embedding:
                time_dim = 64
                self.time_emb = SinusoidalEmbedding(time_dim)

            # Main predictor
            input_dim = action_dim + feature_dim + time_dim
            self.predictor = FlowPredictor(
                input_dim=input_dim,
                hidden_dim=hidden_dim,
                output_dim=action_dim,
            )

        def forward(
            self,
            action: torch.Tensor,
            features: torch.Tensor,
            t: torch.Tensor,
        ) -> torch.Tensor:
            # Prepare inputs
            inputs = [action, features]

            if self.time_emb is not None:
                t_emb = self.time_emb(t)
                # Expand time embedding to match action sequence length
                if action.dim() == 3 and t_emb.dim() == 2:
                    t_emb = t_emb.unsqueeze(1).expand(-1, action.size(1), -1)
                inputs.append(t_emb)

            # Concatenate and predict
            x = torch.cat(inputs, dim=-1)
            return self.predictor(x)

    return FlowModel()
