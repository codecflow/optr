"""
Training logic for OPTR algorithms
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

from ..algorithms.base import Algorithm
from .dataset import Dataset

logger = logging.getLogger(__name__)


class Trainer:
    """
    Trainer for OPTR algorithms
    """

    def __init__(
        self,
        algorithm: Algorithm,
        output_dir: str | None = None,
        config: dict[str, Any] | None = None,
    ):
        """
        Initialize trainer

        Args:
            algorithm: Algorithm to train
            output_dir: Directory for outputs (default: ./training_outputs)
            config: Training configuration
        """
        self.algorithm = algorithm
        self.output_dir = Path(output_dir or "./training_outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Default configuration
        self.config = {
            "batch_size": 32,
            "epochs": 10,
            "learning_rate": 0.001,
            "validation_split": 0.2,
            "checkpoint_interval": 1,
            "log_interval": 10,
            "early_stopping_patience": 3,
            "save_best_only": True,
        }

        if config:
            self.config.update(config)

        # Training state
        self.current_epoch = 0
        self.training_history = {
            "epochs": [],
            "train_metrics": [],
            "val_metrics": [],
            "best_val_metric": float("inf"),
            "best_epoch": 0,
        }

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Setup training logger"""
        log_file = self.output_dir / "training.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    async def train(
        self,
        dataset: Dataset,
        validation_dataset: Dataset | None = None,
        epochs: int | None = None,
    ) -> dict[str, Any]:
        """
        Train the algorithm

        Args:
            dataset: Training dataset
            validation_dataset: Optional validation dataset
            epochs: Number of epochs (overrides config)

        Returns:
            Training history
        """
        epochs = epochs or self.config["epochs"]
        batch_size = self.config["batch_size"]

        # Split dataset if no validation provided
        if validation_dataset is None and self.config["validation_split"] > 0:
            train_dataset, val_dataset, _ = dataset.split(
                train_ratio=1 - self.config["validation_split"],
                val_ratio=self.config["validation_split"],
                test_ratio=0,
            )
        else:
            train_dataset = dataset
            val_dataset = validation_dataset

        logger.info(f"Starting training for {epochs} epochs")
        logger.info(f"Training samples: {len(train_dataset)}")
        if val_dataset:
            logger.info(f"Validation samples: {len(val_dataset)}")

        # Training loop
        for epoch in range(epochs):
            self.current_epoch = epoch
            epoch_start = time.time()

            # Train epoch
            train_metrics = await self._train_epoch(train_dataset, batch_size)

            # Validation
            val_metrics = {}
            if val_dataset:
                val_metrics = await self._validate(val_dataset, batch_size)

            epoch_time = time.time() - epoch_start

            # Log progress
            self._log_epoch(epoch, train_metrics, val_metrics, epoch_time)

            # Save checkpoint
            if (epoch + 1) % self.config["checkpoint_interval"] == 0:
                self._save_checkpoint(epoch, train_metrics, val_metrics)

            # Early stopping
            if self._should_stop_early(val_metrics):
                logger.info(f"Early stopping at epoch {epoch}")
                break

            # Update history
            self.training_history["epochs"].append(epoch)
            self.training_history["train_metrics"].append(train_metrics)
            self.training_history["val_metrics"].append(val_metrics)

        # Save final model
        self._save_final_model()

        return self.training_history

    async def _train_epoch(self, dataset: Dataset, batch_size: int) -> dict[str, Any]:
        """
        Train for one epoch

        Args:
            dataset: Training dataset
            batch_size: Batch size

        Returns:
            Epoch metrics
        """
        epoch_metrics = {"loss": 0, "accuracy": 0, "samples": 0}

        batch_count = 0

        # Iterate over batches
        for batch in dataset.iterate_batches(batch_size, shuffle=True):
            # Prepare batch data
            batch_data = self._prepare_batch(batch)

            # Train on batch
            batch_metrics = await self.algorithm.train(batch_data, validation_data=None)

            # Accumulate metrics
            if batch_metrics:
                epoch_metrics["samples"] += len(batch)

                if "loss" in batch_metrics:
                    epoch_metrics["loss"] += batch_metrics["loss"] * len(batch)

                if "accuracy" in batch_metrics:
                    epoch_metrics["accuracy"] += batch_metrics["accuracy"] * len(batch)

            batch_count += 1

            # Log progress
            if batch_count % self.config["log_interval"] == 0:
                logger.debug(f"Batch {batch_count}: {batch_metrics}")

        # Average metrics
        if epoch_metrics["samples"] > 0:
            epoch_metrics["loss"] /= epoch_metrics["samples"]
            epoch_metrics["accuracy"] /= epoch_metrics["samples"]

        return epoch_metrics

    async def _validate(self, dataset: Dataset, batch_size: int) -> dict[str, Any]:
        """
        Validate on dataset

        Args:
            dataset: Validation dataset
            batch_size: Batch size

        Returns:
            Validation metrics
        """
        val_metrics = {"loss": 0, "accuracy": 0, "samples": 0}

        # Iterate over validation batches
        for batch in dataset.iterate_batches(batch_size, shuffle=False):
            batch_data = self._prepare_batch(batch)

            # Evaluate batch
            correct = 0
            for sample in batch_data:
                predicted = await self.algorithm.predict(
                    sample["state"], sample.get("context")
                )

                if self._actions_match(predicted, sample["action"]):
                    correct += 1

            val_metrics["samples"] += len(batch)
            val_metrics["accuracy"] += correct

        # Average metrics
        if val_metrics["samples"] > 0:
            val_metrics["accuracy"] /= val_metrics["samples"]

        return val_metrics

    def _prepare_batch(self, batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Prepare batch for training

        Args:
            batch: Raw batch data

        Returns:
            Prepared batch
        """
        prepared = []

        for sample in batch:
            prepared_sample = {
                "state": sample.get("state"),
                "action": sample.get("action"),
                "next_state": sample.get("next_state"),
                "context": {},
            }

            # Add any additional context
            if sample.get("result"):
                prepared_sample["context"]["result"] = sample["result"]

            prepared.append(prepared_sample)

        return prepared

    def _actions_match(
        self, action1: Any, action2: Any, threshold: float = 0.9
    ) -> bool:
        """Check if two actions match"""
        if action1 is None or action2 is None:
            return False

        if hasattr(action1, "type") and hasattr(action2, "type"):
            return action1.type == action2.type

        return False

    def _log_epoch(
        self,
        epoch: int,
        train_metrics: dict[str, Any],
        val_metrics: dict[str, Any],
        epoch_time: float,
    ):
        """Log epoch results"""
        log_msg = f"Epoch {epoch + 1}/{self.config['epochs']} - "
        log_msg += f"Time: {epoch_time:.2f}s - "

        if train_metrics:
            log_msg += f"Train Loss: {train_metrics.get('loss', 0):.4f} - "
            log_msg += f"Train Acc: {train_metrics.get('accuracy', 0):.4f} - "

        if val_metrics:
            log_msg += f"Val Loss: {val_metrics.get('loss', 0):.4f} - "
            log_msg += f"Val Acc: {val_metrics.get('accuracy', 0):.4f}"

        logger.info(log_msg)
        print(log_msg)

    def _save_checkpoint(
        self, epoch: int, train_metrics: dict[str, Any], val_metrics: dict[str, Any]
    ):
        """Save training checkpoint"""
        checkpoint_dir = self.output_dir / "checkpoints"
        checkpoint_dir.mkdir(exist_ok=True)

        # Check if this is the best model
        is_best = False
        if val_metrics and "accuracy" in val_metrics:
            if val_metrics["accuracy"] > self.training_history.get(
                "best_val_metric", 0
            ):
                self.training_history["best_val_metric"] = val_metrics["accuracy"]
                self.training_history["best_epoch"] = epoch
                is_best = True

        # Save model
        if not self.config["save_best_only"] or is_best:
            model_path = checkpoint_dir / f"model_epoch_{epoch + 1}.pkl"
            self.algorithm.save(str(model_path))

            if is_best:
                best_path = checkpoint_dir / "best_model.pkl"
                self.algorithm.save(str(best_path))
                logger.info(f"Saved best model at epoch {epoch + 1}")

        # Save training state
        state = {
            "epoch": epoch,
            "config": self.config,
            "history": self.training_history,
            "train_metrics": train_metrics,
            "val_metrics": val_metrics,
        }

        state_path = checkpoint_dir / f"state_epoch_{epoch + 1}.json"
        with open(state_path, "w") as f:
            json.dump(state, f, indent=2, default=str)

    def _should_stop_early(self, val_metrics: dict[str, Any]) -> bool:
        """Check if training should stop early"""
        if not val_metrics or "accuracy" not in val_metrics:
            return False

        patience = self.config["early_stopping_patience"]
        if patience <= 0:
            return False

        # Check if validation hasn't improved
        best_epoch = self.training_history.get("best_epoch", 0)
        epochs_without_improvement = self.current_epoch - best_epoch

        return epochs_without_improvement >= patience

    def _save_final_model(self):
        """Save final trained model"""
        final_path = self.output_dir / "final_model.pkl"
        self.algorithm.save(str(final_path))

        # Save training history
        history_path = self.output_dir / "training_history.json"
        with open(history_path, "w") as f:
            json.dump(self.training_history, f, indent=2, default=str)

        logger.info(f"Training complete. Model saved to {final_path}")

    def load_checkpoint(self, checkpoint_path: str) -> dict[str, Any]:
        """
        Load training checkpoint

        Args:
            checkpoint_path: Path to checkpoint

        Returns:
            Checkpoint state
        """
        checkpoint_file = Path(checkpoint_path)

        # Load model
        model_path = checkpoint_file.parent / checkpoint_file.name.replace(
            "state_", "model_"
        )
        if model_path.exists():
            self.algorithm.load(str(model_path))

        # Load state
        with open(checkpoint_file) as f:
            state = json.load(f)

        self.current_epoch = state.get("epoch", 0)
        self.training_history = state.get("history", {})
        self.config.update(state.get("config", {}))

        logger.info(f"Loaded checkpoint from epoch {self.current_epoch + 1}")

        return state

    def evaluate(
        self, test_dataset: Dataset, batch_size: int | None = None
    ) -> dict[str, Any]:
        """
        Evaluate trained model on test dataset

        Args:
            test_dataset: Test dataset
            batch_size: Batch size (default: from config)

        Returns:
            Evaluation metrics
        """
        batch_size = batch_size or self.config["batch_size"]

        metrics = {
            "accuracy": 0,
            "samples": 0,
            "action_type_accuracy": {},
            "confusion_matrix": {},
        }

        # Run evaluation
        loop = asyncio.get_event_loop()
        val_metrics = loop.run_until_complete(self._validate(test_dataset, batch_size))

        metrics.update(val_metrics)

        # Detailed analysis
        for sample in test_dataset.samples:
            if sample.get("action"):
                action_type = sample["action"].type

                if action_type not in metrics["action_type_accuracy"]:
                    metrics["action_type_accuracy"][action_type] = {
                        "correct": 0,
                        "total": 0,
                    }

                predicted = loop.run_until_complete(
                    self.algorithm.predict(sample["state"], sample.get("context"))
                )

                metrics["action_type_accuracy"][action_type]["total"] += 1

                if self._actions_match(predicted, sample["action"]):
                    metrics["action_type_accuracy"][action_type]["correct"] += 1

        # Calculate per-type accuracy
        for _, counts in metrics["action_type_accuracy"].items():
            if counts["total"] > 0:
                counts["accuracy"] = counts["correct"] / counts["total"]

        return metrics
