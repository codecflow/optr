"""
Simple VLM implementation using basic encoders
"""


import torch
import torch.nn as nn
import torchvision.transforms as T

from .base import VLMInterface


class SimpleVLM(VLMInterface):
    """
    Simple VLM implementation using basic CNN and LSTM encoders
    """

    def __init__(
        self,
        image_size: int = 224,
        image_channels: int = 3,
        text_vocab_size: int = 10000,
        embedding_dim: int = 512,
        device: str = 'cpu',
    ):
        self._device = torch.device(device)
        self._embedding_dim = embedding_dim

        # Simple CNN for images
        self.image_encoder = nn.Sequential(
            nn.Conv2d(image_channels, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(128, embedding_dim),
        ).to(self._device)

        # Simple embedding for text
        self.text_embedding = nn.Embedding(text_vocab_size, embedding_dim).to(self._device)
        self.text_encoder = nn.LSTM(
            embedding_dim, embedding_dim // 2, bidirectional=True, batch_first=True
        ).to(self._device)

        # Fusion layer for multimodal
        self.fusion = nn.Sequential(
            nn.Linear(embedding_dim * 2, embedding_dim),
            nn.ReLU(),
            nn.Linear(embedding_dim, embedding_dim),
        ).to(self._device)

        # Image preprocessing
        self.image_transform = T.Compose([
            T.Resize((image_size, image_size)),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    @property
    def device(self) -> torch.device:
        return self._device

    @property
    def embedding_dim(self) -> int:
        return self._embedding_dim

    def encode_image(self, image: torch.Tensor) -> torch.Tensor:
        """
        Encode image to features

        Args:
            image: Image tensor [B, C, H, W] or [B, N, C, H, W] for multiple views

        Returns:
            Image features [B, D] or [B, N, D]
        """
        if image.dim() == 5:  # Multiple views
            B, N, C, H, W = image.shape
            image = image.view(B * N, C, H, W)
            image = self.image_transform(image)
            features = self.image_encoder(image)
            return features.view(B, N, -1)
        else:
            image = self.image_transform(image)
            return self.image_encoder(image)

    def encode_text(self, text: str | list[str]) -> torch.Tensor:
        """
        Encode text to features

        Args:
            text: Text string or list of strings

        Returns:
            Text features [B, D]
        """
        if isinstance(text, str):
            text = [text]

        # Simple word-level tokenization
        batch_size = len(text)
        max_len = 128

        # Mock tokenization - in practice, use proper tokenizer
        tokens = []
        for t in text:
            words = t.lower().split()[:max_len]
            # Simple hash-based token mapping
            word_tokens = [hash(w) % 10000 for w in words]
            # Pad to max_len
            word_tokens = word_tokens + [0] * (max_len - len(word_tokens))
            tokens.append(word_tokens[:max_len])

        tokens = torch.tensor(tokens, dtype=torch.long).to(self._device)

        embedded = self.text_embedding(tokens)
        output, (hidden, _) = self.text_encoder(embedded)

        # Use last hidden state from both directions
        return hidden.transpose(0, 1).reshape(batch_size, -1)

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
            Multimodal embedding [B, D]
        """
        embeddings = []

        if image is not None:
            img_features = self.encode_image(image)
            if img_features.dim() == 3:  # Multiple views
                img_features = img_features.mean(dim=1)  # Average pool
            embeddings.append(img_features)

        if text is not None:
            text_features = self.encode_text(text)
            embeddings.append(text_features)

        if not embeddings:
            raise ValueError("At least one of image or text must be provided")

        if len(embeddings) == 1:
            return embeddings[0]

        # Fuse multimodal features
        combined = torch.cat(embeddings, dim=-1)
        return self.fusion(combined)
