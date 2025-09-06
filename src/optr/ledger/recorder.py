"""
Recorder for capturing and replaying operator sessions
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..operator.action import Action, action
from ..operator.types import State
from .episode import Episode


class Recorder:
    """
    Records and replays operator execution episodes
    """

    def __init__(self, storage_dir: str | None = None):
        """
        Initialize recorder

        Args:
            storage_dir: Directory to store episodes (default: ./episodes)
        """
        self.storage_dir = Path(storage_dir or "./episodes")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.current_episode: Episode | None = None
        self.replay_callbacks: dict[str, Callable] = {}

    def start_recording(
        self, episode_id: str, metadata: dict[str, Any] | None = None
    ) -> Episode:
        """
        Start recording a new episode

        Args:
            episode_id: Unique identifier for the episode
            metadata: Optional metadata for the episode

        Returns:
            New Episode instance
        """
        if self.current_episode:
            self.stop_recording()

        self.current_episode = Episode(id=episode_id, metadata=metadata or {})
        return self.current_episode

    def record_step(
        self,
        action: Action,
        state_before: State,
        state_after: State | None = None,
        result: Any | None = None,
        error: str | None = None,
    ):
        """
        Record a step in the current episode

        Args:
            action: Action that was executed
            state_before: State before action
            state_after: State after action
            result: Result of the action
            error: Error message if action failed
        """
        if not self.current_episode:
            raise ValueError("No active recording. Call start_recording first.")

        self.current_episode.add_step(
            action=action,
            state_before=state_before,
            state_after=state_after,
            result=result,
            error=error,
        )

    def stop_recording(self) -> Episode | None:
        """
        Stop recording and finalize the current episode

        Returns:
            The completed episode
        """
        if not self.current_episode:
            return None

        self.current_episode.finalize()
        episode = self.current_episode
        self.current_episode = None
        return episode

    def save_episode(self, episode: Episode, filename: str | None = None) -> str:
        """
        Save episode to disk

        Args:
            episode: Episode to save
            filename: Optional filename (default: episode_id.json)

        Returns:
            Path to saved file
        """
        if not filename:
            filename = f"{episode.id}.json"

        filepath = self.storage_dir / filename

        with open(filepath, "w") as f:
            f.write(episode.to_json())

        return str(filepath)

    def load_episode(self, filename: str) -> Episode:
        """
        Load episode from disk

        Args:
            filename: Name of the file to load

        Returns:
            Loaded Episode
        """
        filepath = self.storage_dir / filename

        with open(filepath) as f:
            json_str = f.read()

        return Episode.from_json(json_str)

    def list_episodes(self) -> list[str]:
        """
        List all saved episodes

        Returns:
            List of episode filenames
        """
        return [f.name for f in self.storage_dir.glob("*.json")]

    def register_replay_callback(self, action_type: str, callback: Callable):
        """
        Register a callback for replaying specific action types

        Args:
            action_type: Type of action to handle
            callback: Function to call for this action type
        """
        self.replay_callbacks[action_type] = callback

    async def replay_episode(
        self, episode: Episode, speed: float = 1.0, skip_errors: bool = False
    ) -> dict[str, Any]:
        """
        Replay a recorded episode

        Args:
            episode: Episode to replay
            speed: Replay speed multiplier
            skip_errors: Whether to skip steps that had errors

        Returns:
            Replay results
        """
        results: dict[str, Any] = {
            "total_steps": len(episode.steps),
            "executed_steps": 0,
            "skipped_steps": 0,
            "errors": [],
        }

        for step in episode.steps:
            # Skip error steps if requested
            if skip_errors and step.get("error"):
                results["skipped_steps"] = results["skipped_steps"] + 1
                continue

            action_type = step["action"]["type"]

            # Find appropriate callback
            if action_type in self.replay_callbacks:
                callback = self.replay_callbacks[action_type]
                try:
                    # Recreate action
                    action_params = step["action"].get("params", {})
                    recreated_action = action(action_type, **action_params)

                    # Execute callback
                    await callback(recreated_action)
                    results["executed_steps"] = results["executed_steps"] + 1

                except Exception as e:
                    errors_list = results["errors"]
                    if isinstance(errors_list, list):
                        errors_list.append({"step": step, "error": str(e)})
            else:
                results["skipped_steps"] = results["skipped_steps"] + 1

        return results

    def analyze_episode(self, episode: Episode) -> dict[str, Any]:
        """
        Analyze an episode for patterns and statistics

        Args:
            episode: Episode to analyze

        Returns:
            Analysis results
        """
        analysis: dict[str, Any] = {
            "duration": episode.get_duration(),
            "total_steps": episode.get_step_count(),
            "success_rate": episode.get_success_rate(),
            "action_types": {},
            "error_types": {},
            "avg_step_duration": 0,
        }

        # Count action types
        action_types: dict[str, int] = {}
        for step in episode.steps:
            action_type = step["action"]["type"]
            action_types[action_type] = action_types.get(action_type, 0) + 1
        analysis["action_types"] = action_types

        # Count error types
        error_types: dict[str, int] = {}
        for step in episode.steps:
            if step.get("error"):
                error = step["error"]
                error_types[error] = error_types.get(error, 0) + 1
        analysis["error_types"] = error_types

        # Calculate average step duration
        if len(episode.steps) > 1:
            durations = []
            for i in range(1, len(episode.steps)):
                duration = (
                    episode.steps[i]["timestamp"] - episode.steps[i - 1]["timestamp"]
                )
                durations.append(duration)
            analysis["avg_step_duration"] = sum(durations) / len(durations)

        return analysis

    def merge_episodes(self, episodes: list[Episode], new_id: str) -> Episode:
        """
        Merge multiple episodes into one

        Args:
            episodes: Episodes to merge
            new_id: ID for the merged episode

        Returns:
            Merged episode
        """
        merged = Episode(id=new_id)

        # Combine metadata
        merged.metadata = {
            "merged_from": [ep.id for ep in episodes],
            "merge_count": len(episodes),
        }

        # Combine steps
        for episode in episodes:
            merged.steps.extend(episode.steps)

        # Update timestamps
        if episodes:
            merged.start_time = min(ep.start_time for ep in episodes)
            merged.end_time = max(ep.end_time for ep in episodes if ep.end_time)

        return merged
