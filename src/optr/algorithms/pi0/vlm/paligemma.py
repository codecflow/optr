"""
PaliGemma VLM implementation
"""

import os

import torch
import torch.nn as nn
import torchvision.transforms as T

from .base import VLMInterface


class PaliGemmaVLM(VLMInterface):
    """
    PaliGemma Vision-Language Model implementation
    """

    def __init__(
        self,
        model_name: str = "google/paligemma-3b-pt-224",
        device: str = "cpu",
        use_auth_token: bool = True,
        embedding_dim: int = 2048,
    ):
        self._device = torch.device(device)
        self._embedding_dim = embedding_dim
        self.model_name = model_name

        try:
            from transformers import AutoProcessor, PaliGemmaForConditionalGeneration

            # Check for HF token
            if use_auth_token and not os.environ.get("HF_TOKEN"):
                raise ImportError(
                    "HF_TOKEN environment variable required for PaliGemma. "
                    "Please set it or use SimpleVLM instead."
                )

            self.model = PaliGemmaForConditionalGeneration.from_pretrained(
                model_name,
                use_auth_token=use_auth_token if os.environ.get("HF_TOKEN") else False,
            ).to(self._device)

            self.processor = AutoProcessor.from_pretrained(
                model_name,
                use_auth_token=use_auth_token if os.environ.get("HF_TOKEN") else False,
            )

            # Freeze model for inference
            for param in self.model.parameters():
                param.requires_grad = False

            self.model.eval()

            # Projection layers to match embedding dim
            actual_dim = self.model.config.text_config.hidden_size
            if actual_dim != embedding_dim:
                self.image_projection: nn.Module = nn.Linear(
                    actual_dim, embedding_dim
                ).to(self._device)
                self.text_projection: nn.Module = nn.Linear(
                    actual_dim, embedding_dim
                ).to(self._device)
            else:
                self.image_projection = nn.Identity()
                self.text_projection = nn.Identity()

        except (ImportError, OSError) as e:
            raise ImportError(
                f"Failed to load PaliGemma model '{model_name}': {e}\n"
                "Please ensure transformers is installed and HF_TOKEN is set."
            ) from e

        # Image preprocessing
        self.image_transform = T.Resize((224, 224))

    @property
    def device(self) -> torch.device:
        return self._device

    @property
    def embedding_dim(self) -> int:
        return self._embedding_dim

    def encode_image(self, image: torch.Tensor) -> torch.Tensor:
        """
        Encode image using PaliGemma vision encoder

        Args:
            image: Image tensor [B, C, H, W] or [B, N, C, H, W]

        Returns:
            Image features [B, D] or [B, N, D]
        """
        multi_view = image.dim() == 5

        if multi_view:
            B, N, C, H, W = image.shape
            image = image.view(B * N, C, H, W)

        # Resize and normalize
        image = self.image_transform(image)
        # PaliGemma expects [-1, 1] range
        if image.max() > 1.0:
            image = image / 255.0
        image = image * 2.0 - 1.0

        # Get image features
        with torch.no_grad():
            features = self.model.model.get_image_features(image)

        # Pool over patches and project
        if features.dim() == 3:  # [B, num_patches, D]
            features = features.mean(dim=1)

        features = self.image_projection(features)

        if multi_view:
            features = features.view(B, N, -1)

        return features

    def encode_text(self, text: str | list[str]) -> torch.Tensor:
        """
        Encode text using PaliGemma text encoder

        Args:
            text: Text string or list of strings

        Returns:
            Text features [B, D]
        """
        if isinstance(text, str):
            text = [text]

        # Add newline as per PaliGemma convention
        text = [t if t.endswith("\n") else f"{t}\n" for t in text]

        # Tokenize
        inputs = self.processor.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=128,
            return_tensors="pt",
        ).to(self._device)

        # Get text embeddings
        with torch.no_grad():
            embeddings = self.model.get_input_embeddings()(inputs.input_ids)

        # Pool over sequence length
        mask = inputs.attention_mask.unsqueeze(-1).float()
        pooled = (embeddings * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)

        # Project to embedding dim
        pooled = self.text_projection(pooled)

        return pooled

    def get_multimodal_embedding(
        self,
        image: torch.Tensor | None = None,
        text: str | list[str] | None = None,
    ) -> torch.Tensor:
        """
        Get combined vision-language embedding from PaliGemma

        Args:
            image: Optional image tensor
            text: Optional text

        Returns:
            Multimodal embedding [B, D]
        """
        if image is None and text is None:
            raise ValueError("At least one of image or text must be provided")

        # For true multimodal, we could use the full model
        # but for simplicity, we'll concatenate features
        embeddings = []

        if image is not None:
            img_features = self.encode_image(image)
            if img_features.dim() == 3:  # Multiple views
                img_features = img_features.mean(dim=1)
            embeddings.append(img_features)

        if text is not None:
            text_features = self.encode_text(text)
            embeddings.append(text_features)

        if len(embeddings) == 1:
            return embeddings[0]

        # Simple averaging for multimodal fusion
        # Could be replaced with more sophisticated fusion
        return torch.stack(embeddings).mean(dim=0)

    def generate(
        self,
        image: torch.Tensor,
        prompt: str,
        max_length: int = 50,
    ) -> str:
        """
        Generate text given image and prompt (for inference)

        Args:
            image: Image tensor
            prompt: Text prompt
            max_length: Maximum generation length

        Returns:
            Generated text
        """
        # Prepare inputs
        image = self.image_transform(image)
        if image.max() > 1.0:
            image = image / 255.0

        # Process with PaliGemma
        inputs = self.processor(
            text=prompt,
            images=image,
            return_tensors="pt",
        ).to(self._device)

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
            )

        # Decode
        generated = self.processor.decode(outputs[0], skip_special_tokens=True)

        return generated
