"""
Dataset management for training OPTR algorithms
"""

import pickle
from pathlib import Path
from typing import Any

import numpy as np

from ..ledger import Episode
from ..operator.action import Action, action
from ..operator.types import State


class Dataset:
    """
    Dataset for training algorithms from recorded episodes
    """

    def __init__(self, name: str, storage_dir: str | None = None):
        """
        Initialize dataset

        Args:
            name: Name of the dataset
            storage_dir: Directory to store dataset (default: ./datasets)
        """
        self.name = name
        self.storage_dir = Path(storage_dir or "./datasets")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.episodes = []
        self.samples = []
        self.metadata = {
            "name": name,
            "num_episodes": 0,
            "num_samples": 0,
            "data_types": set(),
        }

    def add_episode(self, episode: Episode):
        """
        Add an episode to the dataset

        Args:
            episode: Episode to add
        """
        self.episodes.append(episode)

        # Extract samples from episode
        for i, step in enumerate(episode.steps):
            sample = self._step_to_sample(step, i)
            if sample:
                self.samples.append(sample)

        # Update metadata
        self.metadata["num_episodes"] = len(self.episodes)
        self.metadata["num_samples"] = len(self.samples)

    def add_episodes_from_directory(self, directory: str):
        """
        Load episodes from a directory

        Args:
            directory: Directory containing episode JSON files
        """
        episode_dir = Path(directory)

        for episode_file in episode_dir.glob("*.json"):
            try:
                episode = Episode.from_json(episode_file.read_text())
                self.add_episode(episode)
            except Exception as e:
                print(f"Failed to load episode {episode_file}: {e}")

    def _step_to_sample(
        self, step: dict[str, Any], index: int
    ) -> dict[str, Any] | None:
        """
        Convert an episode step to a training sample

        Args:
            step: Step from episode
            index: Step index

        Returns:
            Training sample or None
        """
        if not step.get("action") or step.get("error"):
            return None

        sample = {
            "index": index,
            "timestamp": step.get("timestamp"),
            "state": self._reconstruct_state(step.get("state_before")),
            "action": self._reconstruct_action(step.get("action")),
            "next_state": self._reconstruct_state(step.get("state_after")),
            "result": step.get("result"),
        }

        return sample

    def _reconstruct_state(self, state_data: dict | None) -> State | None:
        """Reconstruct State object from serialized data"""
        if not state_data:
            return None

        return State(
            timestamp=state_data.get("timestamp", 0),
            visual=None,  # Visual data not serialized
            metadata=state_data.get("metadata", {}),
        )

    def _reconstruct_action(self, action_data: dict | None) -> Action | None:
        """Reconstruct Action object from serialized data"""
        if not action_data:
            return None

        return action(
            action_data.get("type", "unknown"),
            **action_data.get("params", {})
        )

    def split(
        self,
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
        shuffle: bool = True,
        seed: int | None = None,
    ) -> tuple["Dataset", "Dataset", "Dataset"]:
        """
        Split dataset into train/val/test sets

        Args:
            train_ratio: Ratio for training set
            val_ratio: Ratio for validation set
            test_ratio: Ratio for test set
            shuffle: Whether to shuffle before splitting
            seed: Random seed for shuffling

        Returns:
            Tuple of (train_dataset, val_dataset, test_dataset)
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6

        samples = self.samples.copy()

        if shuffle:
            if seed is not None:
                np.random.seed(seed)
            np.random.shuffle(samples)

        n = len(samples)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)

        train_samples = samples[:train_end]
        val_samples = samples[train_end:val_end]
        test_samples = samples[val_end:]

        # Create new datasets
        train_dataset = Dataset(f"{self.name}_train")
        train_dataset.samples = train_samples
        train_dataset.metadata["num_samples"] = len(train_samples)

        val_dataset = Dataset(f"{self.name}_val")
        val_dataset.samples = val_samples
        val_dataset.metadata["num_samples"] = len(val_samples)

        test_dataset = Dataset(f"{self.name}_test")
        test_dataset.samples = test_samples
        test_dataset.metadata["num_samples"] = len(test_samples)

        return train_dataset, val_dataset, test_dataset

    def get_batch(self, batch_size: int, shuffle: bool = True) -> list[dict[str, Any]]:
        """
        Get a batch of samples

        Args:
            batch_size: Size of batch
            shuffle: Whether to shuffle samples

        Returns:
            List of samples
        """
        if shuffle:
            indices = np.random.choice(
                len(self.samples),
                size=min(batch_size, len(self.samples)),
                replace=False,
            )
            return [self.samples[i] for i in indices]
        else:
            return self.samples[:batch_size]

    def iterate_batches(
        self, batch_size: int, shuffle: bool = True, drop_last: bool = False
    ):
        """
        Iterate over batches

        Args:
            batch_size: Size of each batch
            shuffle: Whether to shuffle samples
            drop_last: Whether to drop last incomplete batch

        Yields:
            Batches of samples
        """
        samples = self.samples.copy()

        if shuffle:
            np.random.shuffle(samples)

        n_batches = len(samples) // batch_size

        for i in range(n_batches):
            start = i * batch_size
            end = start + batch_size
            yield samples[start:end]

        # Handle last batch
        if not drop_last and len(samples) % batch_size != 0:
            yield samples[n_batches * batch_size :]

    def save(self, filename: str | None = None):
        """
        Save dataset to disk

        Args:
            filename: Optional filename (default: dataset_name.pkl)
        """
        if not filename:
            filename = f"{self.name}.pkl"

        filepath = self.storage_dir / filename

        data = {
            "name": self.name,
            "episodes": [ep.to_dict() for ep in self.episodes],
            "samples": self.samples,
            "metadata": self.metadata,
        }

        with open(filepath, "wb") as f:
            pickle.dump(data, f)

    def load(self, filename: str):
        """
        Load dataset from disk

        Args:
            filename: Name of file to load
        """
        filepath = self.storage_dir / filename

        with open(filepath, "rb") as f:
            data = pickle.load(f)

        self.name = data["name"]
        self.episodes = [Episode.from_dict(ep) for ep in data["episodes"]]
        self.samples = data["samples"]
        self.metadata = data["metadata"]

    def get_statistics(self) -> dict[str, Any]:
        """Get dataset statistics"""
        stats = {
            "name": self.name,
            "num_episodes": len(self.episodes),
            "num_samples": len(self.samples),
            "avg_episode_length": 0,
            "action_types": {},
            "success_rate": 0,
        }

        if self.episodes:
            lengths = [ep.get_step_count() for ep in self.episodes]
            stats["avg_episode_length"] = np.mean(lengths)

            success_rates = [ep.get_success_rate() for ep in self.episodes]
            stats["success_rate"] = np.mean(success_rates)

        # Count action types
        for sample in self.samples:
            if sample and sample.get("action"):
                action_type = sample["action"].type
                stats["action_types"][action_type] = (
                    stats["action_types"].get(action_type, 0) + 1
                )

        return stats

    def filter_samples(self, filter_func: callable) -> "Dataset":
        """
        Create filtered dataset

        Args:
            filter_func: Function that takes sample and returns bool

        Returns:
            New filtered dataset
        """
        filtered = Dataset(f"{self.name}_filtered")
        filtered.samples = [s for s in self.samples if filter_func(s)]
        filtered.metadata["num_samples"] = len(filtered.samples)

        return filtered

    def augment_samples(self, augment_func: callable) -> "Dataset":
        """
        Create augmented dataset

        Args:
            augment_func: Function that takes sample and returns augmented sample(s)

        Returns:
            New augmented dataset
        """
        augmented = Dataset(f"{self.name}_augmented")

        for sample in self.samples:
            aug_samples = augment_func(sample)
            if isinstance(aug_samples, list):
                augmented.samples.extend(aug_samples)
            else:
                augmented.samples.append(aug_samples)

        augmented.metadata["num_samples"] = len(augmented.samples)

        return augmented

    def __len__(self) -> int:
        """Get number of samples"""
        return len(self.samples)

    def __getitem__(self, index: int) -> dict[str, Any]:
        """Get sample by index"""
        return self.samples[index]

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"Dataset(name='{self.name}', "
            f"episodes={len(self.episodes)}, "
            f"samples={len(self.samples)})"
        )
