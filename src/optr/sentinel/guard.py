"""
Safety guard for action validation and recovery
"""

from collections.abc import Callable

from ..operator.action import Action
from ..operator.types import State


class Guard:
    """Generic safety and validation guard for any connector type"""

    def __init__(self):
        self.precondition_rules = {}
        self.postcondition_rules = {}
        self.recovery_strategies = {}
        self.global_rules = []

    async def check_preconditions(self, action: Action, state: State) -> bool:
        """Check if action is safe to execute"""
        # Check global rules first
        for rule in self.global_rules:
            if not await rule(action, state):
                return False

        # Check action-specific preconditions
        if action.type in self.precondition_rules:
            for rule in self.precondition_rules[action.type]:
                if not await rule(action, state):
                    return False

        return True

    async def check_postconditions(
        self, action: Action, state_before: State, state_after: State
    ) -> bool:
        """Verify action had expected effect"""
        # Check action-specific postconditions
        if action.type in self.postcondition_rules:
            for rule in self.postcondition_rules[action.type]:
                if not await rule(action, state_before, state_after):
                    return False

        return True

    async def rollback(self, action: Action, state: State) -> bool:
        """Attempt to rollback failed action"""
        if action.type in self.recovery_strategies:
            strategy = self.recovery_strategies[action.type]
            return await strategy(action, state)

        return False

    def add_global_rule(self, rule: Callable):
        """Add rule that applies to all actions"""
        self.global_rules.append(rule)

    def add_precondition(self, action_type: str, rule: Callable):
        """Add precondition rule for specific action type"""
        if action_type not in self.precondition_rules:
            self.precondition_rules[action_type] = []
        self.precondition_rules[action_type].append(rule)

    def add_postcondition(self, action_type: str, rule: Callable):
        """Add postcondition rule for specific action type"""
        if action_type not in self.postcondition_rules:
            self.postcondition_rules[action_type] = []
        self.postcondition_rules[action_type].append(rule)

    def add_recovery_strategy(self, action_type: str, strategy: Callable):
        """Add recovery strategy for action type"""
        self.recovery_strategies[action_type] = strategy
