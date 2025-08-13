"""
Base interface for Vision-Language Models
"""

from abc import ABC, abstractmethod

import torch


class VLMInterface(ABC):
    """
    Abstract interface for Vision-Language Models
    """

    @abstractmethod
    def encode_image(self, image: torch.Tensor) -> torch.Tensor:
        """
        Encode image to features

        Args:
            image: Image tensor

        Returns:
            Image features
        """
        pass

    @abstractmethod
    def encode_text(self, text: str | list[str]) -> torch.Tensor:
        """
        Encode text to features

        Args:
            text: Text string or list of strings

        Returns:
            Text features
        """
        pass

    @abstractmethod
    def get_multimodal_embedding(
        self,
        image: torch.Tensor | None = None,
        text: str | list[str] | None = None,
    ) -> torch.Tensor:
        """
        Get combined vision-language embedding

        Args:
            image: Optional image tensor
            text: Optional text

        Returns:
            Multimodal embedding
        """
        pass

    @property
    def device(self) -> torch.device:
        """Get device the model is on"""
        return torch.device('cpu')

    @property
    def embedding_dim(self) -> int:
        """Get embedding dimension"""
        return 512
