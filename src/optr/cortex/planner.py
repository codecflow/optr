"""
Generic planner for generating action sequences
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from ..operator.types import Action, State


class PlannerBase(ABC):
    """Abstract base class for planners"""

    @abstractmethod
    async def plan(
        self, goal: Any, current_state: State, context: dict[str, Any] | None = None
    ) -> list[Action]:
        """Generate a plan to achieve the goal"""
        pass


class Planner:
    """
    Generic planner that can work with different planning strategies
    Users can register their own planning functions or use built-in ones
    """

    def __init__(self):
        self.strategies = {}
        self.planning_history = []
        self.default_strategy = None

    def register_strategy(
        self, name: str, strategy: Callable, set_default: bool = False
    ):
        """
        Register a planning strategy

        Args:
            name: Name of the strategy
            strategy: Callable that takes (goal, state, context) and returns List[Action]
            set_default: Whether to set this as the default strategy
        """
        self.strategies[name] = strategy
        if set_default or self.default_strategy is None:
            self.default_strategy = name

    async def plan(
        self,
        goal: Any,
        current_state: State,
        context: dict[str, Any] | None = None,
        strategy: str | None = None,
    ) -> list[Action]:
        """
        Generate a plan using specified or default strategy

        Args:
            goal: Goal to achieve (format depends on strategy)
            current_state: Current state
            context: Additional context
            strategy: Name of strategy to use (uses default if None)

        Returns:
            List of actions to execute
        """
        strategy_name = strategy or self.default_strategy

        if not strategy_name or strategy_name not in self.strategies:
            # Return empty plan if no strategy available
            return []

        strategy_func = self.strategies[strategy_name]

        # Generate plan using selected strategy
        plan = await strategy_func(goal, current_state, context)

        # Store in history
        self.planning_history.append(
            {
                "goal": goal,
                "state": current_state,
                "plan": plan,
                "context": context,
                "strategy": strategy_name,
            }
        )

        return plan

    async def decompose(
        self, task: Any, decomposer: Callable | None = None
    ) -> dict[str, Any]:
        """
        Decompose a task into subtasks using provided decomposer

        Args:
            task: Task to decompose
            decomposer: Function to decompose the task

        Returns:
            Decomposition structure (format depends on decomposer)
        """
        if decomposer:
            return await decomposer(task)

        # Default: return task as-is without decomposition
        return {"task": task, "subtasks": []}

    async def replan(
        self,
        original_plan: list[Action],
        failure_info: dict[str, Any],
        current_state: State,
        replanner: Callable | None = None,
    ) -> list[Action]:
        """
        Generate alternative plan after failure

        Args:
            original_plan: The plan that failed
            failure_info: Information about the failure
            current_state: Current state after failure
            replanner: Custom replanning function

        Returns:
            New plan
        """
        if replanner:
            return await replanner(original_plan, failure_info, current_state)

        # Default: return remaining actions from original plan
        failed_index = failure_info.get("failed_index", 0)
        return original_plan[failed_index + 1 :]

    def validate_plan(
        self, plan: list[Action], validator: Callable | None = None
    ) -> tuple[bool, str | None]:
        """
        Validate a plan

        Args:
            plan: Plan to validate
            validator: Custom validation function

        Returns:
            (is_valid, error_message)
        """
        if validator:
            return validator(plan)

        # Basic validation
        if not plan:
            return False, "Plan is empty"

        for action in plan:
            if not action.type:
                return False, "Action missing type"

        return True, None

    def merge_plans(
        self, plans: list[list[Action]], merger: Callable | None = None
    ) -> list[Action]:
        """
        Merge multiple plans into one

        Args:
            plans: List of plans to merge
            merger: Custom merging function

        Returns:
            Merged plan
        """
        if merger:
            return merger(plans)

        # Default: concatenate plans
        merged = []
        for plan in plans:
            merged.extend(plan)
        return merged

    def optimize_plan(
        self, plan: list[Action], optimizer: Callable | None = None
    ) -> list[Action]:
        """
        Optimize a plan

        Args:
            plan: Plan to optimize
            optimizer: Custom optimization function

        Returns:
            Optimized plan
        """
        if optimizer:
            return optimizer(plan)

        # Default: return plan as-is
        return plan

    def get_history(self, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Get planning history

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of planning history entries
        """
        if limit:
            return self.planning_history[-limit:]
        return self.planning_history

    def clear_history(self):
        """Clear planning history"""
        self.planning_history = []
