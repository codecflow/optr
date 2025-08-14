"""
Mixture of Experts implementation for Pi0
"""

import math

import torch
import torch.nn as nn
import torch.nn.functional as F


class Expert(nn.Module):
    """
    Single expert in the MoE
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int | None = None,
        activation: str = "gelu",
    ):
        super().__init__()

        if output_dim is None:
            output_dim = input_dim

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim

        # Simple FFN expert
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, output_dim)

        # Activation
        if activation == "gelu":
            self.activation = nn.GELU()
        elif activation == "relu":
            self.activation = nn.ReLU()
        elif activation == "silu":
            self.activation = nn.SiLU()
        else:
            self.activation = nn.GELU()

        # Layer norm
        self.norm = nn.LayerNorm(output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through expert

        Args:
            x: Input tensor [B, ..., D]

        Returns:
            Output tensor [B, ..., D_out]
        """
        residual = x if x.shape[-1] == self.output_dim else None

        x = self.fc1(x)
        x = self.activation(x)
        x = self.fc2(x)

        if residual is not None:
            x = x + residual

        x = self.norm(x)

        return x


class Router(nn.Module):
    """
    Router for selecting experts
    """

    def __init__(
        self,
        input_dim: int,
        num_experts: int,
        top_k: int = 2,
        noise_std: float = 0.1,
    ):
        super().__init__()

        self.input_dim = input_dim
        self.num_experts = num_experts
        self.top_k = min(top_k, num_experts)
        self.noise_std = noise_std

        # Router network
        self.gate = nn.Linear(input_dim, num_experts)

    def forward(
        self,
        x: torch.Tensor,
        training: bool = False,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Route inputs to experts

        Args:
            x: Input tensor [B, ..., D]
            training: Whether in training mode

        Returns:
            Expert weights [B, ..., K] and indices [B, ..., K]
        """
        # Flatten for routing
        original_shape = x.shape
        x_flat = x.view(-1, self.input_dim)

        # Compute gates
        gates = self.gate(x_flat)

        # Add noise during training
        if training and self.noise_std > 0:
            noise = torch.randn_like(gates) * self.noise_std
            gates = gates + noise

        # Top-k selection
        weights, indices = torch.topk(gates, self.top_k, dim=-1)
        weights = F.softmax(weights, dim=-1)

        # Reshape back
        weights = weights.view(*original_shape[:-1], self.top_k)
        indices = indices.view(*original_shape[:-1], self.top_k)

        return weights, indices


class MixtureOfExperts(nn.Module):
    """
    Mixture of Experts module
    """

    def __init__(
        self,
        input_dim: int,
        num_experts: int = 4,
        expert_dim: int = 512,
        output_dim: int | None = None,
        top_k: int = 2,
        routing_method: str = "learned",  # 'learned', 'random', 'uniform'
    ):
        super().__init__()

        self.input_dim = input_dim
        self.num_experts = num_experts
        self.expert_dim = expert_dim
        self.output_dim = output_dim or input_dim
        self.top_k = min(top_k, num_experts)
        self.routing_method = routing_method

        # Create experts
        self.experts = nn.ModuleList(
            [Expert(input_dim, expert_dim, self.output_dim) for _ in range(num_experts)]
        )

        # Create router
        if routing_method == "learned":
            self.router = Router(input_dim, num_experts, top_k)
        else:
            self.router = None

    def forward(
        self,
        x: torch.Tensor,
        expert_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """
        Forward pass through MoE

        Args:
            x: Input tensor [B, ..., D]
            expert_mask: Optional mask for experts [B, ..., num_experts]

        Returns:
            Output tensor [B, ..., D_out]
        """
        if self.routing_method == "learned" and self.router is not None:
            # Learned routing
            weights, indices = self.router(x, self.training)
            output = self._apply_experts(x, weights, indices)
        elif self.routing_method == "random":
            # Random routing
            output = self._random_routing(x)
        else:
            # Uniform routing (average all experts)
            output = self._uniform_routing(x)

        return output

    def _apply_experts(
        self,
        x: torch.Tensor,
        weights: torch.Tensor,
        indices: torch.Tensor,
    ) -> torch.Tensor:
        """
        Apply selected experts with weights

        Args:
            x: Input tensor [B, ..., D]
            weights: Expert weights [B, ..., K]
            indices: Expert indices [B, ..., K]

        Returns:
            Weighted expert outputs [B, ..., D_out]
        """
        output = torch.zeros(
            *x.shape[:-1], self.output_dim, device=x.device, dtype=x.dtype
        )

        # Apply each selected expert
        for k in range(self.top_k):
            for expert_idx in range(self.num_experts):
                # Find where this expert is selected
                mask = indices[..., k] == expert_idx

                if mask.any():
                    # Get inputs for this expert
                    expert_input = x[mask]

                    # Apply expert
                    expert_output = self.experts[expert_idx](expert_input)

                    # Weight and accumulate
                    weight = weights[..., k][mask].unsqueeze(-1)
                    output[mask] += expert_output * weight

        return output

    def _random_routing(self, x: torch.Tensor) -> torch.Tensor:
        """
        Random routing to experts

        Args:
            x: Input tensor

        Returns:
            Output tensor
        """
        # Randomly select top-k experts
        x.shape[0]
        indices = torch.randperm(self.num_experts)[: self.top_k]
        weights = torch.ones(self.top_k) / self.top_k

        output = torch.zeros(
            *x.shape[:-1], self.output_dim, device=x.device, dtype=x.dtype
        )

        for i, idx in enumerate(indices):
            expert_output = self.experts[idx](x)
            output += expert_output * weights[i]

        return output

    def _uniform_routing(self, x: torch.Tensor) -> torch.Tensor:
        """
        Uniform routing (average all experts)

        Args:
            x: Input tensor

        Returns:
            Output tensor
        """
        output = torch.zeros(
            *x.shape[:-1], self.output_dim, device=x.device, dtype=x.dtype
        )

        for expert in self.experts:
            output += expert(x)

        return output / self.num_experts


class MultiModalMoE(nn.Module):
    """
    Multi-modal Mixture of Experts for combining different modalities
    """

    def __init__(
        self,
        modality_dims: dict[str, int],
        hidden_dim: int = 512,
        output_dim: int | None = None,
        fusion_method: str = "moe",  # 'moe', 'concat', 'attention'
    ):
        super().__init__()

        self.modality_dims = modality_dims
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim or hidden_dim
        self.fusion_method = fusion_method

        # Create modality-specific encoders
        self.encoders = nn.ModuleDict(
            {name: nn.Linear(dim, hidden_dim) for name, dim in modality_dims.items()}
        )

        # Create fusion mechanism
        if fusion_method == "moe":
            # MoE for fusion
            self.fusion = MixtureOfExperts(
                input_dim=hidden_dim,
                num_experts=len(modality_dims),
                expert_dim=hidden_dim * 2,
                output_dim=self.output_dim,
            )
        elif fusion_method == "concat":
            # Simple concatenation + projection
            total_dim = hidden_dim * len(modality_dims)
            self.fusion = nn.Sequential(
                nn.Linear(total_dim, hidden_dim),
                nn.GELU(),
                nn.Linear(hidden_dim, self.output_dim),
            )
        elif fusion_method == "attention":
            # Cross-attention fusion
            self.fusion = CrossModalAttention(hidden_dim, self.output_dim)
        else:
            raise ValueError(f"Unknown fusion method: {fusion_method}")

    def forward(
        self,
        inputs: dict[str, torch.Tensor],
        masks: dict[str, torch.Tensor] | None = None,
    ) -> torch.Tensor:
        """
        Forward pass through multi-modal MoE

        Args:
            inputs: Dictionary of modality inputs
            masks: Optional dictionary of modality masks

        Returns:
            Fused output tensor
        """
        # Encode each modality
        encoded = {}
        for name, x in inputs.items():
            if name in self.encoders:
                encoded[name] = self.encoders[name](x)

        # Apply fusion
        if self.fusion_method == "moe":
            # Stack and apply MoE
            stacked = torch.stack(list(encoded.values()), dim=1)
            output = self.fusion(stacked).mean(dim=1)
        elif self.fusion_method == "concat":
            # Concatenate and project
            concatenated = torch.cat(list(encoded.values()), dim=-1)
            output = self.fusion(concatenated)
        else:
            # Attention fusion
            output = self.fusion(encoded, masks)

        return output


class CrossModalAttention(nn.Module):
    """
    Cross-modal attention for fusion
    """

    def __init__(self, hidden_dim: int, output_dim: int):
        super().__init__()

        self.hidden_dim = hidden_dim
        self.output_dim = output_dim

        # Attention layers
        self.q_proj = nn.Linear(hidden_dim, hidden_dim)
        self.k_proj = nn.Linear(hidden_dim, hidden_dim)
        self.v_proj = nn.Linear(hidden_dim, hidden_dim)
        self.out_proj = nn.Linear(hidden_dim, output_dim)

        self.scale = 1.0 / math.sqrt(hidden_dim)

    def forward(
        self,
        inputs: dict[str, torch.Tensor],
        masks: dict[str, torch.Tensor] | None = None,
    ) -> torch.Tensor:
        """
        Forward pass with cross-modal attention

        Args:
            inputs: Dictionary of modality inputs
            masks: Optional dictionary of modality masks

        Returns:
            Fused output tensor
        """
        # Stack all modalities
        values = list(inputs.values())
        stacked = torch.stack(values, dim=1)  # [B, M, D]

        # Self-attention across modalities
        q = self.q_proj(stacked)
        k = self.k_proj(stacked)
        v = self.v_proj(stacked)

        # Compute attention scores
        scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale

        # Apply masks if provided
        if masks is not None:
            # Create attention mask from modality masks
            mask_values = list(masks.values())
            if mask_values:
                attn_mask = torch.stack(mask_values, dim=1)
                scores = scores.masked_fill(~attn_mask.unsqueeze(-1), -1e9)

        # Apply softmax
        attn_weights = F.softmax(scores, dim=-1)

        # Apply attention
        attended = torch.matmul(attn_weights, v)

        # Pool across modalities and project
        pooled = attended.mean(dim=1)
        output = self.out_proj(pooled)

        return output
