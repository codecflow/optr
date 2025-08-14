"""
Episode data structure for recording operator sessions
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any

from ..operator.action import Action
from ..operator.types import State


@dataclass
class Episode:
    """
    Represents a recorded episode of operator execution
    """

    id: str
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    steps: list[dict[str, Any]] = field(default_factory=list)

    def add_step(
        self,
        action: Action,
        state_before: State,
        state_after: State | None = None,
        result: Any | None = None,
        error: str | None = None,
    ):
        """
        Add a step to the episode

        Args:
            action: Action that was executed
            state_before: State before action
            state_after: State after action
            result: Result of the action
            error: Error message if action failed
        """
        step = {
            "timestamp": time.time(),
            "action": {"type": action.type, "params": action.params},
            "state_before": self._serialize_state(state_before),
            "state_after": self._serialize_state(state_after) if state_after else None,
            "result": result,
            "error": error,
        }
        self.steps.append(step)

    def finalize(self):
        """Mark episode as complete"""
        self.end_time = time.time()

    def get_duration(self) -> float:
        """Get episode duration in seconds"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    def get_step_count(self) -> int:
        """Get number of steps in episode"""
        return len(self.steps)

    def get_success_rate(self) -> float:
        """Calculate success rate of steps"""
        if not self.steps:
            return 0.0

        successful = sum(1 for step in self.steps if not step.get("error"))
        return successful / len(self.steps)

    def to_dict(self) -> dict[str, Any]:
        """Convert episode to dictionary"""
        return {
            "id": self.id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.get_duration(),
            "metadata": self.metadata,
            "steps": self.steps,
            "statistics": {
                "step_count": self.get_step_count(),
                "success_rate": self.get_success_rate(),
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Episode":
        """Create episode from dictionary"""
        episode = cls(
            id=data["id"],
            start_time=data["start_time"],
            end_time=data.get("end_time"),
            metadata=data.get("metadata", {}),
            steps=data.get("steps", []),
        )
        return episode

    def to_json(self) -> str:
        """Convert episode to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Episode":
        """Create episode from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def _serialize_state(self, state: State) -> dict[str, Any]:
        """Serialize state for storage"""
        if not state:
            return None

        return {
            "timestamp": state.timestamp,
            "metadata": state.metadata,
            # Visual data is not serialized by default (too large)
            "has_visual": state.visual is not None,
        }

    def filter_steps(
        self, action_type: str | None = None, has_error: bool | None = None
    ) -> list[dict[str, Any]]:
        """
        Filter steps based on criteria

        Args:
            action_type: Filter by action type
            has_error: Filter by error presence

        Returns:
            Filtered list of steps
        """
        filtered = self.steps

        if action_type:
            filtered = [s for s in filtered if s["action"]["type"] == action_type]

        if has_error is not None:
            if has_error:
                filtered = [s for s in filtered if s.get("error")]
            else:
                filtered = [s for s in filtered if not s.get("error")]

        return filtered

    def get_summary(self) -> str:
        """Get human-readable summary of episode"""
        summary = f"Episode {self.id}\n"
        summary += f"Duration: {self.get_duration():.2f}s\n"
        summary += f"Steps: {self.get_step_count()}\n"
        summary += f"Success Rate: {self.get_success_rate():.1%}\n"

        if self.metadata:
            summary += f"Metadata: {self.metadata}\n"

        return summary
