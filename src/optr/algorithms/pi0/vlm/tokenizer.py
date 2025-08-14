"""
Tokenizer utilities for VLMs
"""

import torch


class VLMTokenizer:
    """
    Simple tokenizer interface for VLMs
    """

    def __init__(
        self,
        vocab_size: int = 10000,
        pad_token_id: int = 0,
        unk_token_id: int = 1,
        bos_token_id: int = 2,
        eos_token_id: int = 3,
    ):
        self.vocab_size = vocab_size
        self.pad_token_id = pad_token_id
        self.unk_token_id = unk_token_id
        self.bos_token_id = bos_token_id
        self.eos_token_id = eos_token_id

        # Simple word-to-id mapping
        self.word_to_id = {
            "<pad>": pad_token_id,
            "<unk>": unk_token_id,
            "<bos>": bos_token_id,
            "<eos>": eos_token_id,
        }
        self.id_to_word = {v: k for k, v in self.word_to_id.items()}
        self._next_id = 4

    def add_word(self, word: str) -> int:
        """
        Add word to vocabulary

        Args:
            word: Word to add

        Returns:
            Token ID for the word
        """
        if word not in self.word_to_id:
            if self._next_id < self.vocab_size:
                self.word_to_id[word] = self._next_id
                self.id_to_word[self._next_id] = word
                self._next_id += 1
            else:
                return self.unk_token_id
        return self.word_to_id[word]

    def tokenize(
        self,
        text: str | list[str],
        max_length: int = 128,
        padding: bool = True,
        truncation: bool = True,
        add_special_tokens: bool = True,
        return_tensors: str | None = "pt",
    ) -> dict:
        """
        Tokenize text

        Args:
            text: Text to tokenize
            max_length: Maximum sequence length
            padding: Whether to pad sequences
            truncation: Whether to truncate sequences
            add_special_tokens: Whether to add BOS/EOS tokens
            return_tensors: Format for return ('pt' for PyTorch, None for list)

        Returns:
            Dictionary with 'input_ids' and 'attention_mask'
        """
        if isinstance(text, str):
            text = [text]

        batch_tokens = []
        batch_masks = []

        for t in text:
            # Simple word-level tokenization
            words = t.lower().split()

            # Convert to token IDs
            tokens = []
            if add_special_tokens:
                tokens.append(self.bos_token_id)

            for word in words:
                # Simple hash-based mapping for unknown words
                if word in self.word_to_id:
                    token_id = self.word_to_id[word]
                else:
                    # Use hash for consistent mapping
                    token_id = (hash(word) % (self.vocab_size - 4)) + 4
                tokens.append(token_id)

            if add_special_tokens:
                tokens.append(self.eos_token_id)

            # Truncate if needed
            if truncation and len(tokens) > max_length:
                tokens = tokens[:max_length]
                if add_special_tokens and tokens[-1] != self.eos_token_id:
                    tokens[-1] = self.eos_token_id

            # Create attention mask
            mask = [1] * len(tokens)

            # Pad if needed
            if padding and len(tokens) < max_length:
                pad_length = max_length - len(tokens)
                tokens.extend([self.pad_token_id] * pad_length)
                mask.extend([0] * pad_length)

            batch_tokens.append(tokens)
            batch_masks.append(mask)

        # Convert to tensors if requested
        if return_tensors == "pt":
            input_ids = torch.tensor(batch_tokens, dtype=torch.long)
            attention_mask = torch.tensor(batch_masks, dtype=torch.long)
        else:
            input_ids = batch_tokens
            attention_mask = batch_masks

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }

    def decode(
        self,
        token_ids: torch.Tensor | list[int] | list[list[int]],
        skip_special_tokens: bool = True,
    ) -> str | list[str]:
        """
        Decode token IDs back to text

        Args:
            token_ids: Token IDs to decode
            skip_special_tokens: Whether to skip special tokens

        Returns:
            Decoded text
        """
        # Handle different input formats
        if isinstance(token_ids, torch.Tensor):
            if token_ids.dim() == 2:
                # Batch of sequences
                return [
                    self._decode_single(ids.tolist(), skip_special_tokens)
                    for ids in token_ids
                ]
            else:
                # Single sequence
                return self._decode_single(token_ids.tolist(), skip_special_tokens)
        elif isinstance(token_ids[0], list):
            # Batch of sequences
            return [self._decode_single(ids, skip_special_tokens) for ids in token_ids]
        else:
            # Single sequence
            return self._decode_single(token_ids, skip_special_tokens)

    def _decode_single(
        self,
        token_ids: list[int],
        skip_special_tokens: bool,
    ) -> str:
        """
        Decode a single sequence of token IDs

        Args:
            token_ids: Token IDs to decode
            skip_special_tokens: Whether to skip special tokens

        Returns:
            Decoded text
        """
        special_tokens = {
            self.pad_token_id,
            self.unk_token_id,
            self.bos_token_id,
            self.eos_token_id,
        }

        words = []
        for token_id in token_ids:
            if skip_special_tokens and token_id in special_tokens:
                continue

            if token_id in self.id_to_word:
                words.append(self.id_to_word[token_id])
            else:
                # Unknown token
                if not skip_special_tokens:
                    words.append("<unk>")

        return " ".join(words)

    def batch_decode(
        self,
        token_ids: torch.Tensor | list[list[int]],
        skip_special_tokens: bool = True,
    ) -> list[str]:
        """
        Decode batch of token IDs

        Args:
            token_ids: Batch of token IDs
            skip_special_tokens: Whether to skip special tokens

        Returns:
            List of decoded texts
        """
        if isinstance(token_ids, torch.Tensor):
            token_ids = token_ids.tolist()

        return [self._decode_single(ids, skip_special_tokens) for ids in token_ids]


def create_tokenizer(tokenizer_type: str = "simple", **kwargs) -> VLMTokenizer:
    """
    Create a tokenizer

    Args:
        tokenizer_type: Type of tokenizer ('simple' or others)
        **kwargs: Additional arguments

    Returns:
        Tokenizer instance
    """
    if tokenizer_type == "simple":
        return VLMTokenizer(**kwargs)
    else:
        raise ValueError(f"Unknown tokenizer type: {tokenizer_type}")
